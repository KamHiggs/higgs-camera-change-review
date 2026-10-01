"""Per-assessment process orchestration and preservation; no camera equations."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from .contract import DEFAULT_ARCHIVE, DEPENDENCY_SHA, MANIFEST_SHA, PREFIX, NOTICE, InputRefusal, ASSESSMENT_CONTRACT, SUMMARY_CONTRACT, VERSION, recorded_binding, software_identity
from .errors import ReviewFailure, diagnostic, storage_failure
from .provenance import read_runtime, verify_runtime_bytes, extract_verified_bytes, pins
from .summary import summarize
from .freshness import compare_snapshots
from .contract import typed_inputs
from .assessment_format import validate_manifest, validate_assessment
from .presentation import human_summary

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()

def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')

def read_json(path):
    from .bounded_json import load
    return load(path)

def archive_path():
    return Path(os.environ.get('HIGGS_DEPENDENCY_ARCHIVE', DEFAULT_ARCHIVE))

def verify_dependency(path):
    raw, identity = read_runtime(path)
    return raw

def manifest_folder(folder):
    return {p.relative_to(folder).as_posix(): {'sha256': digest(p.read_bytes()), 'bytes': p.stat().st_size}
            for p in sorted(folder.rglob('*')) if p.is_file() and p.relative_to(folder).as_posix() != 'ASSESSMENT_MANIFEST.json'}

def verify_coverage(folder):
    if folder.is_symlink() or any(p.is_symlink() for p in folder.rglob('*')):
        raise InputRefusal('HISTORY_INTEGRITY', 'Historical assessment contains an unsupported symbolic link')
    try:
        manifest = read_json(folder / 'ASSESSMENT_MANIFEST.json')
        validate_manifest(manifest)
        expected = manifest['files']
        actual = manifest_folder(folder)
    except (OSError, ValueError, KeyError) as exc:
        raise InputRefusal('HISTORY_INTEGRITY', 'Historical assessment integrity cannot be verified') from exc
    if actual != expected:
        raise InputRefusal('HISTORY_INTEGRITY', 'Historical assessment no longer matches its manifest')
    return digest((folder / 'ASSESSMENT_MANIFEST.json').read_bytes())

def verify_assessment(folder):
    identity = verify_coverage(folder)
    validate_assessment(folder)
    return identity


def _run_assessment(snapshot, state_root):
    inputs = typed_inputs(snapshot)
    archive = archive_path()
    binding = recorded_binding(snapshot)
    raw, execution_identity = read_runtime(archive)
    if snapshot['runtime']['configured_runtime_sha256'] != execution_identity['sha256']:
        raise ReviewFailure('INTEGRITY_ERROR', 'SNAPSHOT_RUNTIME_CHANGED', 'Configured runtime changed after the recorded snapshot')
    subset_raw, subset_identity = read_runtime(DEFAULT_ARCHIVE)
    state = Path(state_root).resolve()
    if state.exists() and not state.is_dir():
        raise ReviewFailure('CONFIGURATION_ERROR', 'STATE_ROOT_KIND', 'Configured assessment storage is not a directory')
    state.mkdir(parents=True, exist_ok=True)
    identifier = uuid.uuid4().hex
    review = state / identifier
    review.mkdir(exist_ok=False)
    work = review / 'work'; work.mkdir()
    package = review / 'assessment'; package.mkdir()
    write_json(package / 'snapshot.json', snapshot)
    write_json(package / 'typed_inputs.json', inputs)
    (package / 'dependency').mkdir()
    # The full upstream archive includes private execution paths. Export a
    # separately identified, byte-preserving subset, never relabel it the ZIP.
    (package / 'dependency/runtime-subset.zip').write_bytes(subset_raw)
    shutil.copyfile(Path(__file__).parent / 'data/subset_identity.json', package / 'dependency/subset_identity.json')
    write_json(package / 'runtime_provenance.json', {'execution_archive_identity': execution_identity,
        'exported_runtime_subset_identity': subset_identity,
        'relationship': 'The exported runtime subset is an approved projection of the pinned analysis package.'})
    write_json(package / 'recorded_input_binding.json', binding)
    write_json(package / 'assessment_contract.json', {'assessment_contract': ASSESSMENT_CONTRACT, 'summary_contract': SUMMARY_CONTRACT,
        'integration_version': VERSION, 'integration_source_sha256': software_identity(),
        'mapper_sha256': digest(Path(__file__).with_name('map_worker.py').read_bytes()),
        'summary_sha256': digest(Path(__file__).with_name('summary.py').read_bytes())})
    extract_verified_bytes(raw, work)
    root = work / PREFIX
    env = {k: v for k, v in os.environ.items() if k in ('PATH', 'LANG', 'LC_ALL', 'SYSTEMROOT')}
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONNOUSERSITE='1', TMPDIR=str(work))
    # Mapper imports only the dependency's exact JSON helpers, in its own process.
    try:
        mapped = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('map_worker.py')), str(root), str(package / 'typed_inputs.json')],
                                cwd=work, env=env, capture_output=True, text=True, timeout=45)
    except (OSError, subprocess.TimeoutExpired) as exc:
        (review / 'mapper.failure.json').write_text(json.dumps({'failure': type(exc).__name__, 'stage': 'mapper'}) + '\n')
        raise InputRefusal('EXECUTION_FAILURE', 'Mapper process could not complete; failure retained locally') from exc
    (review / 'mapper.stdout').write_text(mapped.stdout); (review / 'mapper.stderr').write_text(mapped.stderr)
    if mapped.returncode:
        raise InputRefusal('MAPPING_FAILURE', 'Projection failed; raw failure retained in local execution records')
    write_json(package / 'mapping_result.json', json.loads(mapped.stdout))
    projected = package / 'projection'; projected.mkdir()
    for rel in ['evidence/EVIDENCE_LEDGER.json', 'evidence/SOURCE_CAPTURES.json', 'evidence/USER_SYNTHETIC_REQUIREMENTS.json', 'scenarios/inventree.json']:
        target = projected / rel; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(root / rel, target)
    records = []
    for operation in ('analyze', 'questions'):
        args = [sys.executable, '-B', str(root / 'tools/run_experiment.py'), operation,
                '--scenario', 'scenarios/inventree.json', '--camera', inputs['camera_id'], '--out', str(work / operation)]
        start = datetime.now(timezone.utc).isoformat()
        try:
            proc = subprocess.Popen(args, cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try: stdout, stderr = proc.communicate(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill(); stdout, stderr = proc.communicate(); stderr += '\nTIMEOUT\n'
            code = proc.returncode
            rec = {'operation': operation, 'exit_code': code, 'pid': proc.pid, 'started_utc': start,
                   'command': ['python', '-B', 'working_dependency/tools/run_experiment.py', operation, '--scenario', 'scenarios/inventree.json', '--camera', inputs['camera_id'], '--out', '../' + operation]}
        except OSError as exc:
            stdout, stderr, code = '', type(exc).__name__, 5
            rec = {'operation': operation, 'exit_code': code, 'started_utc': start, 'launch_failure': type(exc).__name__}
        (review / (operation + '.stdout')).write_text(stdout)
        (review / (operation + '.stderr')).write_text(stderr)
        # Exact local streams retained outside portable export because CLI stdout contains an absolute output path.
        rec['stdout_sha256'] = digest(stdout.encode()); rec['stderr_sha256'] = digest(stderr.encode())
        records.append(rec)
        if (work / operation).exists(): shutil.copytree(work / operation, package / 'outputs' / operation)
    write_json(package / 'processes.json', records)
    summary = summarize(package, inputs['camera_id'])
    summary.update(assessment_id=identifier, created_utc=datetime.now(timezone.utc).isoformat())
    summary['recorded_input_binding'] = binding
    write_json(package / 'summary.json', summary)
    trace = mapping_trace(snapshot, inputs)
    write_json(package / 'mapping_trace.json', trace)
    shutil.copyfile(Path(__file__).with_name('replay.py'), package / 'replay.py')
    (package / 'SUMMARY.md').write_text(human_summary(summary))
    # Scan the distributable assessment projection/outputs for private host paths.
    for p in package.rglob('*'):
        if p.is_file() and p.suffix in ('.json', '.md', '.html', '.py'):
            if str(state).encode() in p.read_bytes() or b'/Users/' in p.read_bytes():
                raise InputRefusal('EXPORT_PATH', 'Private local path in assessment; result retained locally, export refused')
    write_json(package / 'ASSESSMENT_MANIFEST.json', {'format': ASSESSMENT_CONTRACT, 'files': manifest_folder(package)})
    return summary

def export_assessment(folder, destination):
    verify_assessment(folder)
    # Freeze accepted bytes before writing; a later source edit cannot enter this export.
    payload = {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob('*')) if p.is_file()}
    manifest = json.loads(payload['ASSESSMENT_MANIFEST.json'])
    if set(payload) != set(manifest['files']) | {'ASSESSMENT_MANIFEST.json'}:
        raise InputRefusal('HISTORY_INTEGRITY', 'Export membership differs from the recorded manifest')
    for name, rec in manifest['files'].items():
        if digest(payload[name]) != rec['sha256'] or len(payload[name]) != rec['bytes']:
            raise InputRefusal('HISTORY_INTEGRITY', 'Export bytes differ from the recorded manifest')
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in payload.items(): z.writestr(name, data)



def run_assessment(snapshot, state_root):
    try:
        return _run_assessment(snapshot, state_root)
    except ReviewFailure as exc:
        diagnostic(exc.code, category=exc.category)
        raise
    except OSError as exc:
        raise storage_failure(exc) from exc


def mapping_trace(snapshot, inputs):
    trace = []
    camera_for_trace = inputs['camera_id']
    for key, row in snapshot['parameters'].items():
        dest = {'camera_id': 'selected camera_id + evidence subject binding', 'isp_enabled': 'scenario.camera_modes.CAM-FLIR.isp_enabled' if camera_for_trace == 'CAM-FLIR' else 'not applied to this model; retained configuration label',
                'pixel_format': 'scenario.premises.pixel_format + selected camera mode', 'transport': 'scenario.premises.transport',
                'evidence_identity': 'verified dependency/capture bundle'}[key]
        trace.append(dict(row, logical_name=key, normalized_value=inputs.get(key, row['raw_value']), destination=dest,
                          classification='evidence_pointer' if key == 'evidence_identity' else 'inventory_context' if key == 'camera_id' else 'synthetic_operating_declaration'))
    trace.append({'raw_value': snapshot['requirements']['fast_required_fps'], 'normalized_value': inputs['fast_required_fps'],
                  'classification': 'synthetic_user_requirement', 'source_field': 'POST fast_required_fps (user input, no InvenTree Parameter object)', 'units': 'fps', 'destination': 'SYN-REQ-LINE-FAST/data/required_fps'})
    return trace
