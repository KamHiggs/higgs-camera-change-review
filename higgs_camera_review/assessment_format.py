"""Coverage is separate from versioned file permission and minimum JSON shape.

These checks admit records for processing, not facts into the engineering model.
Historical records retain their own semantic contract.
"""
import json
from pathlib import Path
from .errors import ReviewFailure


def bad(code='MALFORMED_ASSESSMENT', message='Assessment does not satisfy its recorded format'):
    raise ReviewFailure('INTEGRITY_ERROR', code, message)


def obj(value, fields=None):
    if type(value) is not dict:
        bad()
    for key, typ in (fields or {}).items():
        if key not in value or type(value[key]) not in (typ if isinstance(typ, tuple) else (typ,)):
            bad()
    return value


def rows(value):
    if type(value) is not list or any(type(x) is not dict for x in value):
        bad()
    return value


def strings(value):
    if type(value) is not list or any(type(x) is not str for x in value):
        bad()


from .bounded_json import load


def validate_manifest(value):
    obj(value, {'format': str, 'files': dict})
    for name, record in value['files'].items():
        if not isinstance(name, str) or Path(name).is_absolute() or '..' in Path(name).parts or name == 'ASSESSMENT_MANIFEST.json':
            bad('MANIFEST_FORMAT')
        obj(record, {'sha256': str, 'bytes': int})
        if record['bytes'] < 0 or len(record['sha256']) != 64 or any(c not in '0123456789abcdef' for c in record['sha256']):
            bad('MANIFEST_FORMAT')


BASE_REQUIRED = {
    'snapshot.json', 'typed_inputs.json', 'mapping_result.json', 'mapping_trace.json',
    'summary.json', 'processes.json', 'dependency/runtime-subset.zip',
    'dependency/subset_identity.json', 'projection/evidence/EVIDENCE_LEDGER.json',
    'projection/evidence/SOURCE_CAPTURES.json', 'projection/evidence/USER_SYNTHETIC_REQUIREMENTS.json',
    'projection/scenarios/inventree.json',
}
NEW_REQUIRED = BASE_REQUIRED | {'SUMMARY.md', 'assessment_contract.json', 'recorded_input_binding.json', 'runtime_provenance.json', 'replay.py'}
OPTIONAL_ANCILLARY = {'ancillary/operator-note.txt'}
SOURCE_NAMES = {
    'GEN-CAM-ALLIED', 'GEN-CAM-BASLER', 'GEN-CAM-FLIR', 'SYN-APPROVAL',
    'SYN-CAM-LEGACY', 'SYN-CONFIG-BASE', 'SYN-FW-BASE', 'SYN-GRAPH',
    'SYN-REQ-LINE-FAST', 'SYN-REQ-LINE-SLOW', 'SYN-TEST-FLIR-SAMPLE', 'SYN-TEST-LEGACY-FAST',
}
ENGINE_FILES = set()
for operation in ('analyze', 'questions'):
    ENGINE_FILES |= {f'outputs/{operation}/applicability.json', f'outputs/{operation}/materialization_trace.json', f'outputs/{operation}/generated_case/case.json'}
    ENGINE_FILES |= {f'outputs/{operation}/generated_case/sources/{s}.json' for s in SOURCE_NAMES}
ENGINE_FILES |= {'outputs/analyze/analysis/' + n for n in ('report.json', 'result.json', 'engineering_review.html', 'revalidation_plan.md')}
ENGINE_FILES |= {'outputs/questions/questions/' + n for n in ('result.json', 'explanation.md')}


def _snapshot(s):
    obj(s, {'schema':str,'instance_id':str,'inventree_version':str,'integration_version':str,
            'current_part':dict,'substitute_part':dict,'manufacturer_part':dict,
            'parameters':dict,'requirements':dict,'runtime':dict})
    for name in ('current_part', 'substitute_part'):
        obj(s[name], {'object_id':int,'name':str})
    obj(s['manufacturer_part'], {'object_id':int,'manufacturer_id':int,'manufacturer':str,'mpn':str})
    for name in ('camera_id','isp_enabled','pixel_format','transport','evidence_identity'):
        if name not in s['parameters']:bad()
        obj(s['parameters'][name], {'object_type':str,'object_id':int,'part_id':int,'parameter_name':str,'template_id':int,'units':str,'raw_value':str})
    obj(s['requirements'], {'fast_required_fps':str,'classification':str})
    obj(s['runtime'], {'configured_runtime_sha256':str,'pinned_original_archive_sha256':str})
    if s['integration_version'] != '0.1.0':obj(s['runtime'], {'integration_source_sha256':str})


def _evaluations(values):
    for ev in rows(values):
        obj(ev, {'camera_id':str,'variant_id':str,'constraints':list})
        for row in rows(ev['constraints']):obj(row, {'constraint':str,'status':str,'comparison':str,'missing_fields':list,'source_ids':list})


def _applicability(a):
    obj(a, {'analysis_allowed':bool,'verdict':str,'withheld_evidence':list})
    for row in rows(a['withheld_evidence']):
        obj(row, {'entry_id':str,'state':str})
        if row.get('destination') is not None:obj(row['destination'], {'record_id':str})
        if 'missing' in row:strings(row['missing'])


def validate_structure(folder):
    """Minimum shapes before consumers call .get/.items/index fields. No repair."""
    folder = Path(folder)
    docs = {}
    for p in folder.rglob('*.json'):
        rel=p.relative_to(folder).as_posix()
        # Unknown ancillary JSON is rejected by v0.1.2 format permission below;
        # historical extra files are not retrospectively assigned semantic meaning.
        if rel in BASE_REQUIRED | NEW_REQUIRED | ENGINE_FILES:
            docs[rel]=load(p)
    if not BASE_REQUIRED - {'dependency/runtime-subset.zip'} <= set(docs):bad()
    s=docs['snapshot.json'];_snapshot(s);version=s['integration_version']
    if version not in ('0.1.0','0.1.1','0.1.2','0.1.3'):bad('ASSESSMENT_VERSION','Assessment contract is not supported')
    inputs=docs['typed_inputs.json'];obj(inputs, {'camera_id':str,'isp_enabled':(bool,type(None)),'pixel_format':str,'transport':str,'fast_required_fps':int})
    if version == '0.1.0' and 'assessment_contract.json' in docs:bad('ASSESSMENT_VERSION')
    if version != '0.1.0':
        for name in ('assessment_contract.json','recorded_input_binding.json','runtime_provenance.json'):
            if name not in docs:bad()
        c=docs['assessment_contract.json']
        obj(c, {k:str for k in ('assessment_contract','summary_contract','integration_version','integration_source_sha256','mapper_sha256','summary_sha256')})
        if c['assessment_contract']!='higgs-assessment-v'+version or c['integration_version']!=version:bad('ASSESSMENT_VERSION')
        b=docs['recorded_input_binding.json'];obj(b, {'instance_id':str,'inventree_version':str,'integration_version':str,'current_part_id':int,'substitute_part_id':int,'manufacturer_part':dict,'parameters':dict,'requirements':dict,'runtime':dict})
        r=docs['runtime_provenance.json'];obj(r, {'execution_archive_identity':dict,'exported_runtime_subset_identity':dict,'relationship':str})
        for key in ('execution_archive_identity','exported_runtime_subset_identity'):
            obj(r[key], {k:str for k in ('sha256','kind','original_archive_sha256','source_manifest_sha256','approved_member_set_sha256')})
    obj(docs['dependency/subset_identity.json'], {'original_archive_sha256':str,'subset_sha256':str,'original_manifest_sha256':str,'included_files':list})
    strings(docs['dependency/subset_identity.json']['included_files'])
    obj(docs['mapping_result.json'], {'changed_entries':list,'scenario':str,'frozen_dependency_modified':bool,'working_projection_modified':bool})
    for row in rows(docs['mapping_trace.json']):obj(row, {'classification':str,'destination':str})
    ps=rows(docs['processes.json'])
    if len(ps)!=2:bad()
    for row in ps:obj(row, {'operation':str,'exit_code':int})
    if {p['operation'] for p in ps}!={'analyze','questions'}:bad()
    summary=docs['summary.json'];obj(summary, {'engineering_status':str,'notice':str,'synthetic_installation':bool,'camera_id':str,'blockers':list,'unknowns':list,'evaluations':list,'assessment_id':str,'created_utc':str})
    for key in ('blockers','unknowns'):rows(summary[key])
    _evaluations(summary['evaluations'])
    if version!='0.1.0':obj(summary, {'summary_contract':str,'recorded_input_binding':dict})
    if 'applicability' in summary:_applicability(summary['applicability'])
    if 'counts' in summary:
        obj(summary['counts'])
        if any(type(v) is not int for v in summary['counts'].values()):bad()
    if 'reasons' in summary:
        for r in rows(summary['reasons']):
            obj(r, {'reason_class':str,'affected_source_rows':list});strings(r['affected_source_rows'])
            if 'missing_premises' in r:strings(r['missing_premises'])
    if 'questions' in summary:
        obj(summary['questions'], {'execution_status':str,'result':(dict,type(None))})
        q=summary['questions']['result']
        if q is not None:
            obj(q, {'analysis_status':str})
            if 'policies' in q:
                for policy in rows(q['policies']):obj(policy, {'policy':str})

    for rel,value in docs.items():
        if rel.startswith(('outputs/','projection/')):
            obj(value)
            if rel.endswith('/applicability.json'):_applicability(value)
            if rel.endswith('/analysis/report.json'):
                obj(value, {'evaluations':list});_evaluations(value['evaluations'])
            if rel.endswith('/result.json'):
                obj(value, {'execution_status':str,'result':(dict,type(None))})
                if value['result'] is not None and '/questions/' in rel:obj(value['result'], {'analysis_status':str})
    obj(docs['projection/evidence/EVIDENCE_LEDGER.json'], {'entries':list,'sources':dict,'record_templates':dict})
    rows(docs['projection/evidence/EVIDENCE_LEDGER.json']['entries'])
    obj(docs['projection/evidence/SOURCE_CAPTURES.json'], {'captures':list});rows(docs['projection/evidence/SOURCE_CAPTURES.json']['captures'])
    obj(docs['projection/evidence/USER_SYNTHETIC_REQUIREMENTS.json'], {'LINE-FAST':dict,'classification':str,'synthetic':bool})
    obj(docs['projection/scenarios/inventree.json'], {'camera_modes':dict,'premises':dict,'scenario_id':str,'synthetic':bool})
    return version


def validate_format(folder, version):
    if version not in ('0.1.2','0.1.3'):
        return {'format_contract':version,'policy':'Historical format; no v0.1.2 allowlist or SUMMARY.md guarantee'}
    files={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    allowed=NEW_REQUIRED | ENGINE_FILES | OPTIONAL_ANCILLARY | {'ASSESSMENT_MANIFEST.json'}
    if files-allowed:bad('FORMAT_FORBIDDEN_FILE','File is not permitted by the v0.1.2+ assessment format')
    if NEW_REQUIRED-files:bad('FORMAT_MISSING_FILE','Required v0.1.2+ assessment file is missing')
    if (folder/'replay.py').read_bytes()!=Path(__file__).with_name('replay.py').read_bytes():
        bad('FORMAT_HELPER_IDENTITY','Export helper differs from the pinned distribution helper')
    ancillary=sorted(files & OPTIONAL_ANCILLARY)
    for name in ancillary:
        b=(folder/name).read_bytes()
        if len(b)>65536:bad('ANCILLARY_SIZE')
        try:b.decode('utf-8')
        except UnicodeError:bad('ANCILLARY_ENCODING')
    return {'format_contract':version,'optional_ancillary':ancillary,'ancillary_assurance':'MANIFEST_VERIFIED_BUT_NOT_SEMANTICALLY_VERIFIED'}


def validate_assessment(folder):
    version=validate_structure(folder)
    return version,validate_format(folder,version)
