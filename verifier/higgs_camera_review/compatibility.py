"""Explicit dispatch to the unchanged historical verifier; never newer semantics."""
import json
import subprocess
import sys
import zipfile
import io
import hashlib
from pathlib import Path
from .errors import ReviewFailure

from .assurance import POLICY
from .contract import VERSION

HISTORICAL = {
    '0.1.1': (Path(__file__).parent / 'data/historical-verifier-v0.1.1.zip', POLICY['formats']['0.1.1']['archive_sha256']),
    '0.1.2': (Path(__file__).parent / 'data/historical-verifier-v0.1.2.zip', POLICY['formats']['0.1.2']['archive_sha256']),
}

def compatibility_info(version):
    row = POLICY['formats'].get(version)
    if row is None:
        return {'assessment_format_version': version, 'available': False, 'code': 'ASSESSMENT_VERSION'}
    from .contract import software_identity
    historical = row['executor'] != VERSION
    available = True
    if historical:
        archive, pin = HISTORICAL[row['executor']]
        try: available = hashlib.sha256(archive.read_bytes()).hexdigest() == pin
        except OSError: available = False
    return dict(row, assessment_format_version=version, verifier_software_version=VERSION,
        dispatcher_software_sha256=software_identity(), available=available,
        executing_verifier_version=row['executor'],
        full_decision_available=available and row['decision_contract'] is not None,
        code='AVAILABLE' if available else 'HISTORICAL_VERIFIER_UNAVAILABLE',
        meaning='Declared format selects verification semantics, not authenticity or recipient acceptance')


def run_historical(assessment,out,level,version,env):
    executor = POLICY['formats'][version]['executor']
    archive, expected_sha = HISTORICAL[executor]
    try:raw=archive.read_bytes()
    except OSError as exc:
        raise ReviewFailure('CONFIGURATION_ERROR','HISTORICAL_VERIFIER_UNAVAILABLE','Verification unavailable for this historical contract') from exc
    if hashlib.sha256(raw).hexdigest()!=expected_sha:
        raise ReviewFailure('INTEGRITY_ERROR','HISTORICAL_VERIFIER_IDENTITY','Historical verifier does not match the externally pinned package')
    target=out/'historical-verifier'
    # Only a byte-exact, externally pinned archive may supply executable code.
    with zipfile.ZipFile(io.BytesIO(raw)) as z:z.extractall(target)
    proc=subprocess.run([sys.executable,'-B',str(target/'verify_assessment.py'),'--assessment',str(assessment),
                         '--out',str(out/'historical-result'),'--level',level],cwd=out,env=env,capture_output=True,text=True,timeout=180)
    (out/'historical.stdout').write_text(proc.stdout);(out/'historical.stderr').write_text(proc.stderr)
    try:result=json.loads(proc.stdout)
    except ValueError as exc:
        raise ReviewFailure('PROCESS_FAILURE','HISTORICAL_VERIFIER_FAILED','Historical verifier did not return a structured result; diagnostics retained') from exc
    if not isinstance(result,dict) or result.get('assurance_level') not in ('NOT_VERIFIED','REPRODUCED_ENGINE_OUTPUT','VERIFIED_RECORDED_DECISION'):
        raise ReviewFailure('PROCESS_FAILURE','HISTORICAL_VERIFIER_FAILED','Historical verifier returned an unsupported result')
    expected_exit=1 if result['assurance_level']=='NOT_VERIFIED' else (3 if level=='decision' and result['assurance_level']!='VERIFIED_RECORDED_DECISION' else 0)
    if proc.returncode!=expected_exit:
        raise ReviewFailure('PROCESS_FAILURE','HISTORICAL_VERIFIER_EXIT','Historical verifier exit disagrees with its result')
    result.update(assessment_version=version, executing_verifier_version=executor,
                  dispatcher_version=VERSION, historical_verifier_archive_sha256=expected_sha,
                  historical_intake='Bounded JSON, coverage and structure before exact historical dispatch; no newer semantic assurance')
    return result
