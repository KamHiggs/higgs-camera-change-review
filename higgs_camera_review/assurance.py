"""External requirement policy, explicitly frozen before implementation."""
import json
import os
from pathlib import Path
from .errors import ReviewFailure
from .contract import VERSION

POLICY = json.loads((Path(__file__).parent / 'data/assurance_policy.json').read_text())

def host_requirement(requested=None):
    minimum = os.environ.get('HIGGS_REQUIRED_ASSURANCE', POLICY['host']['default'])
    if minimum not in POLICY['contracts']:
        raise ReviewFailure('CONFIGURATION_ERROR', 'HOST_ASSURANCE_UNSUPPORTED', 'Operator assurance configuration is unsupported')
    required = minimum if requested is None else requested
    if not isinstance(required, str) or required not in POLICY['contracts']:
        raise ReviewFailure('INPUT_ERROR', 'REQUIRED_ASSURANCE_UNSUPPORTED', 'Requested assurance contract is unsupported')
    if minimum not in POLICY['satisfies'][required]:
        raise ReviewFailure('INPUT_ERROR', 'HOST_ASSURANCE_FLOOR', 'Request cannot lower the operator assurance requirement')
    return required, minimum

def classify(result, required, origin):
    version = result.get('assessment_version')
    row = POLICY['formats'].get(version, {})
    status = result.get('assurance_level', 'NOT_VERIFIED')
    contract = row.get('decision_contract') if status == 'VERIFIED_RECORDED_DECISION' else row.get('engine_contract') if status == 'REPRODUCED_ENGINE_OUTPUT' else None
    result.update(verifier_software_version=VERSION, assessment_format_version=version,
        assurance_contract=contract,
        historical_verification={'status': status, 'contract': contract,
            'executing_verifier_version': result.get('executing_verifier_version'),
            'historical_verifier_archive_sha256': result.get('historical_verifier_archive_sha256'),
            'authenticated_creation_time': False},
        recipient_requirement={'contract': required, 'origin': origin, 'policy_id': POLICY['policy_id']})
    if required is None:
        acceptance = {'status': 'NOT_EVALUATED', 'code': 'REQUIRED_ASSURANCE_NOT_SUPPLIED'}
    elif required not in POLICY['contracts']:
        acceptance = {'status': 'REFUSED', 'code': 'REQUIRED_ASSURANCE_UNSUPPORTED'}
    elif not contract:
        acceptance = {'status': 'NOT_ACCEPTED', 'code': 'VERIFICATION_FAILED'}
    elif required in POLICY['satisfies'][contract]:
        acceptance = {'status': 'ACCEPTED', 'code': 'REQUIRED_ASSURANCE_MET'}
    else:
        acceptance = {'status': 'DOES_NOT_MEET_REQUIRED_ASSURANCE', 'code': 'REQUIRED_ASSURANCE_UNMET'}
    acceptance['meaning'] = 'Assurance-policy result only; not deployment approval, source truth or physical compatibility'
    result['acceptance'] = acceptance
    return result

def exit_code(result):
    if not result.get('receipt_saved') or result.get('assurance_level') == 'NOT_VERIFIED': return 1
    if result['acceptance']['code'] == 'REQUIRED_ASSURANCE_UNSUPPORTED': return 6
    if result.get('requested_level') == 'decision' and result['assurance_level'] != 'VERIFIED_RECORDED_DECISION': return 3
    if result['acceptance']['status'] == 'NOT_EVALUATED': return 5
    return 0 if result['acceptance']['status'] == 'ACCEPTED' else 4
