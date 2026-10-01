"""Separately obtained verifier: pinned execution, then optional v0.1.1 decision-chain checks."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from .contract import (ASSESSMENT_CONTRACT, SUMMARY_CONTRACT, VERSION, PREFIX,
                       typed_inputs, recorded_binding, software_identity)
from .core import read_json, write_json, digest, verify_assessment, mapping_trace
from .summary import summarize
from .provenance import read_runtime, extract_verified_bytes, pins
from .errors import ReviewFailure
from .assessment_format import validate_assessment
from .presentation import human_summary
from .compatibility import compatibility_info, run_historical
from .assurance import classify, exit_code

PROJECTION_FILES = {'evidence/EVIDENCE_LEDGER.json', 'evidence/SOURCE_CAPTURES.json',
                    'evidence/USER_SYNTHETIC_REQUIREMENTS.json', 'scenarios/inventree.json'}

def require(condition, code, message):
    if not condition:
        raise ReviewFailure('INTEGRITY_ERROR', code, message)

def file_bytes(folder):
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in folder.rglob('*') if p.is_file()}

def _run(assessment, out, level):
    require(level in ('engine', 'decision'), 'VERIFY_LEVEL', 'Choose engine or decision verification')
    here = Path(__file__).resolve().parent
    require(here != assessment and assessment not in here.parents, 'VERIFIER_LOCATION',
            'Verifier must be obtained and run separately from the examined assessment')
    manifest_hash = verify_assessment(assessment)
    runtime_file = assessment / 'dependency/runtime-subset.zip'
    raw, subset = read_runtime(runtime_file)
    expected = pins()
    require(subset['sha256'] == expected['subset_sha256'], 'EXPORTED_RUNTIME', 'Export must contain the approved runtime subset')
    internal = read_json(assessment / 'dependency/subset_identity.json')
    require(internal['original_archive_sha256'] == expected['original_archive_sha256'] and
            internal['subset_sha256'] == expected['subset_sha256'] and
            internal['original_manifest_sha256'] == expected['original_manifest_sha256'] and
            set(internal['included_files']) == set(expected['required_members']),
            'RUNTIME_DECLARATION', 'Export runtime declarations disagree with external verifier pins')
    snapshot = read_json(assessment / 'snapshot.json')
    execution_hash = snapshot['runtime']['configured_runtime_sha256']
    require(execution_hash in (expected['original_archive_sha256'], expected['subset_sha256']),
            'EXECUTION_RUNTIME', 'Recorded execution archive is outside the verifier approved identities')
    require(snapshot['runtime']['pinned_original_archive_sha256'] == expected['original_archive_sha256'],
            'ORIGINAL_RUNTIME', 'Recorded original runtime identity differs from the external pin')
    projection = file_bytes(assessment / 'projection')
    require(set(projection) == PROJECTION_FILES, 'PROJECTION_MEMBERSHIP', 'Unexpected or missing projection files')
    contract_file = assessment / 'assessment_contract.json'
    contract = read_json(contract_file) if contract_file.exists() else {}
    is_new = contract.get('assessment_contract') == ASSESSMENT_CONTRACT
    legacy = not contract and snapshot.get('integration_version') == '0.1.0'
    require(is_new or legacy, 'ASSESSMENT_VERSION', 'Assessment contract is not supported by this verifier')
    outputs = out / 'reproduced'
    extract_verified_bytes(raw, out / 'runtime')
    root = out / 'runtime' / PREFIX
    inputs = read_json(assessment / 'typed_inputs.json')
    if level == 'decision' and is_new:
        expected_contract = {'assessment_contract': ASSESSMENT_CONTRACT, 'summary_contract': SUMMARY_CONTRACT,
            'integration_version': VERSION, 'integration_source_sha256': software_identity(),
            'mapper_sha256': digest(Path(__file__).with_name('map_worker.py').read_bytes()),
            'summary_sha256': digest(Path(__file__).with_name('summary.py').read_bytes())}
        require(contract == expected_contract, 'CONTRACT_IDENTITY', 'Historical decision contract differs from this pinned verifier version')
        require(snapshot['integration_version'] == VERSION and snapshot['runtime']['integration_source_sha256'] == software_identity(),
                'INTEGRATION_IDENTITY', 'Recorded integration software identity differs from this verifier version')
        derived_inputs = typed_inputs(snapshot)
        require(inputs == derived_inputs, 'TYPED_INPUT_MISMATCH', 'Recorded typed inputs differ from the raw snapshot')
        binding = recorded_binding(snapshot)
        require(read_json(assessment / 'recorded_input_binding.json') == binding,
                'RECORDED_BINDING', 'Mapped object identities or raw declarations disagree')
        require(read_json(assessment / 'mapping_trace.json') == mapping_trace(snapshot, inputs),
                'MAPPING_TRACE', 'Recorded mapping trace differs from the versioned mapping contract')
        identities = read_json(assessment / 'runtime_provenance.json')
        require(identities['execution_archive_identity']['sha256'] == execution_hash and
                identities['exported_runtime_subset_identity'] == subset,
                'RUNTIME_RELATIONSHIP', 'Execution/export runtime identities disagree')
        for item in identities.values():
            if isinstance(item, dict):
                require(item['original_archive_sha256'] == expected['original_archive_sha256'] and
                        item['source_manifest_sha256'] == expected['original_manifest_sha256'] and
                        item['approved_member_set_sha256'] == subset['approved_member_set_sha256'],
                        'RUNTIME_RELATIONSHIP', 'Runtime member relationship is not the approved projection')
        # Execute only this externally obtained mapper, never code inside the assessment.
        mapped = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('map_worker.py')), str(root), str(assessment / 'typed_inputs.json')],
                                capture_output=True, text=True, timeout=45, env=clean_env(), cwd=out)
        (out / 'mapper.stdout').write_text(mapped.stdout); (out / 'mapper.stderr').write_text(mapped.stderr)
        require(mapped.returncode == 0, 'MAPPER_RECONSTRUCTION', 'Pinned mapper did not reconstruct the inputs')
        require(json.loads(mapped.stdout) == read_json(assessment / 'mapping_result.json'), 'MAPPER_RESULT', 'Mapper record differs from reconstruction')
        require(all((root / n).read_bytes() == data for n, data in projection.items()),
                'PROJECTION_MISMATCH', 'Saved projection differs from reconstruction using pinned manufacturer material and recorded inputs')
    else:
        for rel, data in projection.items():
            target = root / rel; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
    # Only the camera argument is consumed by engine-only reproduction. No full-consistency claim follows.
    require(inputs.get('camera_id') in ('CAM-FLIR', 'CAM-ALLIED', 'CAM-BASLER'), 'CAMERA_ID', 'Unsupported camera selector')
    original_processes = read_json(assessment / 'processes.json'); records = []
    require(len(original_processes) == 2 and {p['operation'] for p in original_processes} == {'analyze', 'questions'},
            'PROCESS_RECORDS', 'Expected one analyze and one questions process record')
    for op in ('analyze', 'questions'):
        r = subprocess.run([sys.executable, '-B', str(root / 'tools/run_experiment.py'), op, '--scenario', 'scenarios/inventree.json',
                            '--camera', inputs['camera_id'], '--out', str(outputs / op)],
                           capture_output=True, text=True, timeout=60, cwd=out, env=clean_env())
        (out / (op + '.stdout')).write_text(r.stdout); (out / (op + '.stderr')).write_text(r.stderr)
        before = file_bytes(assessment / 'outputs' / op); after = file_bytes(outputs / op)
        old_exit = next(p['exit_code'] for p in original_processes if p['operation'] == op)
        records.append({'operation': op, 'exit_code': r.returncode, 'same_exit': r.returncode == old_exit,
                        'same_output_bytes': before == after, 'files': len(before)})
    write_json(out / 'ENGINE_COMPARISON.json', records)
    require(all(r['same_exit'] and r['same_output_bytes'] for r in records), 'ENGINE_OUTPUT_MISMATCH', 'Engine output or exit differs from the historical record')
    result = {'requested_level': level, 'assurance_level': 'REPRODUCED_ENGINE_OUTPUT', 'assessment_manifest_sha256': manifest_hash,
              'verifier_version': VERSION, 'verifier_software_sha256': software_identity(), 'engine_comparison': records,
              'execution_archive_identity': execution_hash, 'exported_runtime_subset_identity': subset,
              'scope': 'Agreement with separately pinned software/records; not manufacturer truth, physical identity, deployment approval or an independent oracle.'}
    if legacy:
        result.update(historical_status='HISTORICAL_ENGINE_REPRODUCTION_SUPPORTED',
                      full_decision_status='FULL_DECISION_VERIFICATION_NOT_AVAILABLE_FOR_THIS_VERSION')
    elif level == 'decision':
        # Derive summary from the freshly executed output, not from the saved display.
        fresh = out / 'summary-work'; fresh.mkdir(); shutil.copytree(outputs, fresh / 'outputs')
        write_json(fresh / 'processes.json', records)
        recomputed = summarize(fresh, inputs['camera_id'])
        recomputed['recorded_input_binding'] = recorded_binding(snapshot)
        saved = read_json(assessment / 'summary.json')
        expected_saved = {k: v for k, v in saved.items() if k not in ('assessment_id', 'created_utc')}
        require(recomputed == expected_saved, 'SUMMARY_MISMATCH', 'Displayed decision status, reasons, blockers, unknowns or evidence request differ from reconstructed results')
        require((assessment / 'SUMMARY.md').read_bytes() == human_summary(recomputed).encode('utf-8'),
                'HUMAN_SUMMARY_MISMATCH', 'SUMMARY.md differs from the deterministic verified decision view')
        result.update(assurance_level='VERIFIED_RECORDED_DECISION', full_decision_status='VERIFIED_RECORDED_DECISION')
    else:
        result['full_decision_status'] = 'NOT_REQUESTED'
    return result

def clean_env():
    env = {k:v for k,v in os.environ.items() if k in ('PATH', 'LANG', 'LC_ALL', 'SYSTEMROOT')}
    return dict(env, PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1')

def verify(assessment, output, level, require_assurance=None, requirement_origin='CLI argument (external to assessment)'):
    assessment, out = Path(assessment).resolve(), Path(output).resolve()
    created = False
    version = None
    try:
        if out.exists() or out == assessment or assessment in out.parents or out in assessment.parents:
            raise ReviewFailure('INPUT_ERROR', 'VERIFICATION_OUTPUT', 'Verification output must be new and separate from the assessment')
        out.mkdir(parents=True)
        created = True
        require(level in ('engine','decision'), 'VERIFY_LEVEL', 'Choose engine or decision verification')
        verify_assessment(assessment)
        version, format_result = validate_assessment(assessment)
        if version != VERSION:
            result = run_historical(assessment,out,level,version,clean_env())
        else:
            result = _run(assessment,out,level)
            result.update(assessment_version=version,executing_verifier_version=VERSION,
                assurance_details={'semantic_contract':version,'file_coverage':'Complete recorded assessment payload coverage; not authorship or authority',
                    'format_permission':format_result,'checked':['recorded file coverage','versioned allowed file set','minimum document structures','pinned runtime and reproduced engine outputs'] +
                        (['snapshot to typed inputs to mapper projection to engine result to summary.json','deterministic SUMMARY.md'] if level=='decision' else []),
                    'not_checked':(['snapshot/mapper consistency','summary.json decision consistency','SUMMARY.md semantic consistency'] if level=='engine' else []) +
                        ['authorship','chronology and creation IDs','inventory display labels','snapshot.audit','process timestamps/PIDs/command/stream hashes','runtime_provenance.relationship','dependency/subset_identity.meaning','physical identity','manufacturer truth','engineering approval'],
                    'ancillary_files':format_result.get('optional_ancillary',[]),
                    'ancillary_assurance':'MANIFEST_VERIFIED_BUT_NOT_SEMANTICALLY_VERIFIED'})
    except ReviewFailure as exc:
        result = {'requested_level':level,'assurance_level':'NOT_VERIFIED','assessment_version':version,'category':exc.category,'code':exc.code,'message':str(exc)}
    except (KeyError, TypeError, ValueError, AttributeError, UnicodeError) as exc:
        result = {'requested_level':level,'assurance_level':'NOT_VERIFIED','assessment_version':version,'category':'INTEGRITY_ERROR','code':'MALFORMED_ASSESSMENT','message':'Assessment does not satisfy its recorded format'}
    except subprocess.SubprocessError:
        result = {'requested_level':level,'assurance_level':'NOT_VERIFIED','category':'PROCESS_FAILURE','code':'VERIFIER_EXECUTION','message':'Verification did not complete; no verified result'}
    except OSError:
        result = {'requested_level':level,'assurance_level':'NOT_VERIFIED','category':'STORAGE_FAILURE','code':'VERIFICATION_STORAGE','message':'Verification storage could not complete the operation'}
    # Historical child receipts are preserved under historical-result; their persistence
    # fields do not describe this dispatcher's receipt.
    for key in ('receipt_saved', 'receipt_path', 'receipt_identity'):
        result.pop(key, None)
    result = classify(result, require_assurance, requirement_origin)
    result.update(record_type='HIGGS_VERIFICATION_RESULT_CONTENT', record_state='CONTENT_ONLY',
        finality_rule='Unpublished except as complete canonical VERIFICATION_RESULT.json. Temporary files are not receipts.')
    response = dict(result, receipt_saved=False)
    if created:
        pending = out / '.verification-result.tmp'
        try:
            write_json(pending, result)
            raw = pending.read_bytes()
            final = out / 'VERIFICATION_RESULT.json'
            pending.replace(final)
            response.update(receipt_saved=True, receipt_path=str(final),
                            receipt_identity={'sha256':digest(raw),'bytes':len(raw)})
        except OSError:
            # Do not discard historical verification, or claim recipient acceptance
            # following a failed persistence operation. Staging has no saved claim.
            response.update(assurance_level='NOT_VERIFIED', category='STORAGE_FAILURE',
                code='VERIFICATION_RESULT_STORAGE', message='Verification receipt could not be saved',
                acceptance={'status':'NOT_ACCEPTED','code':'RECEIPT_PERSISTENCE_FAILED'})
            try: pending.unlink(missing_ok=True)
            except OSError: pass
    return response

def main():
    import argparse
    p = argparse.ArgumentParser(description='Use this verifier from separately obtained trusted software, outside the assessment.')
    p.add_argument('--assessment', required=True); p.add_argument('--out', required=True); p.add_argument('--level', required=True, choices=['engine','decision'])
    p.add_argument('--require-assurance', help='External recipient contract. Omission permits historical verification only (exit 5).')
    args = p.parse_args()
    result = verify(args.assessment, args.out, args.level, args.require_assurance)
    print(json.dumps(result, sort_keys=True))
    return exit_code(result)

if __name__ == '__main__':
    sys.exit(main())
