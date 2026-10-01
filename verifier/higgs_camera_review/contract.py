"""Adapter configuration, not a second engineering model."""
from pathlib import Path
from .errors import ReviewFailure

VERSION = '0.1.3'
ASSESSMENT_CONTRACT = 'higgs-assessment-v0.1.3'
SUMMARY_CONTRACT = 'higgs-summary-v0.1.3'

DEPENDENCY_SHA = 'd23cd87f6d842ceb850eba865bf1b19ce120a5185ccb58634dbdc622e05f78ee'
PREFIX = 'HIGGS_NEAR_REAL_CAMERA_CHANGE_v0.1.2_CRUCIBLE'
DEFAULT_ARCHIVE = Path(__file__).parent / 'data' / 'higgs-v012-runtime-subset.zip'
MANIFEST_SHA = 'c6cf090c1092634573d8e45579b09e92b1a4f0a506137e47f4d0636a0f4e8786'
NOTICE = 'Advisory result — no deployment approval.'
PARAMETERS = {
    'camera_id': 'HIGGS_CAMERA_ID',
    'isp_enabled': 'HIGGS_ISP_ENABLED',
    'pixel_format': 'HIGGS_PIXEL_FORMAT',
    'transport': 'HIGGS_TRANSPORT',
    'evidence_identity': 'HIGGS_EVIDENCE_ID',
}
CAMERAS = {
    'CAM-FLIR': {'manufacturer': 'Teledyne FLIR', 'mpn': 'BFS-U3-51S5M'},
    'CAM-ALLIED': {'manufacturer': 'Allied Vision', 'mpn': 'Alvium 1800 U-507'},
    'CAM-BASLER': {'manufacturer': 'Basler', 'mpn': 'a2A1920-160umBAS'},
}

class InputRefusal(ReviewFailure, ValueError):
    def __init__(self, code, message):
        category = 'INTEGRITY_ERROR' if code.startswith(('HISTORY_', 'DEPENDENCY_')) else 'INPUT_ERROR'
        if code == 'CONFIGURATION': category = 'CONFIGURATION_ERROR'
        if code in ('EXECUTION_FAILURE', 'MAPPING_FAILURE'): category = 'PROCESS_FAILURE'
        super().__init__(category, code, message)

def parse_fps(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 32 or not value.isascii() or not value.isdecimal() or not 1 <= int(value) <= 1000:
        raise InputRefusal('UNSUPPORTED_REQUIREMENT', 'Synthetic fast-line FPS must be an integer from 1 to 1000')
    return int(value)

def recorded_binding(snapshot):
    """Decision-contract identity projection; validates cross-record relationships, not physical truth."""
    for obj in ('current_part', 'substitute_part', 'manufacturer_part'):
        if type(snapshot[obj]['object_id']) is not int or snapshot[obj]['object_id'] < 1:
            raise InputRefusal('OBJECT_IDENTITY', 'Invalid mapped object identity')
    if type(snapshot['manufacturer_part']['manufacturer_id']) is not int or snapshot['manufacturer_part']['manufacturer_id'] < 1:
        raise InputRefusal('OBJECT_IDENTITY', 'Invalid manufacturer identity')
    for k, name in PARAMETERS.items():
        p = snapshot['parameters'][k]
        if p.get('missing') or p.get('object_type') != 'common.Parameter' or p.get('parameter_name') != name or p.get('part_id') != snapshot['substitute_part']['object_id']:
            raise InputRefusal('PARAMETER_IDENTITY', 'Parameter identity does not match its declared part and mapping')
        if any(type(p.get(f)) is not int or p[f] < 1 for f in ('object_id', 'template_id')):
            raise InputRefusal('PARAMETER_IDENTITY', 'Invalid parameter identity')
    if snapshot['requirements']['classification'] != 'synthetic_user_requirement':
        raise InputRefusal('REQUIREMENT_CLASS', 'Requirement must remain a synthetic user assumption')
    return {'instance_id': snapshot['instance_id'], 'inventree_version': snapshot['inventree_version'],
            'integration_version': snapshot['integration_version'],
            'current_part_id': snapshot['current_part']['object_id'], 'substitute_part_id': snapshot['substitute_part']['object_id'],
            'manufacturer_part': snapshot['manufacturer_part'], 'parameters': snapshot['parameters'],
            'requirements': snapshot['requirements'], 'runtime': snapshot['runtime']}

def typed_inputs(snapshot):
    """No aliases, unit conversion, note parsing or factual admission."""
    p = snapshot['parameters']
    for key in PARAMETERS:
        if key not in p or p[key].get('missing'):
            raise InputRefusal('MISSING_INPUT', 'Missing configured parameter: ' + PARAMETERS[key])
    if any(p[k].get('units') for k in PARAMETERS):
        raise InputRefusal('UNSUPPORTED_UNIT', 'Declared mapping parameters are dimensionless labels; units are not converted')
    raw = {k: p[k]['raw_value'] for k in PARAMETERS}
    camera = raw['camera_id']
    if camera not in CAMERAS:
        raise InputRefusal('CAMERA_BINDING', 'Unsupported camera identity')
    bound = snapshot['manufacturer_part']
    if bound.get('manufacturer') != CAMERAS[camera]['manufacturer'] or bound.get('mpn') != CAMERAS[camera]['mpn']:
        raise InputRefusal('CAMERA_BINDING', 'Model/manufacturer does not match the configured evidence binding')
    if raw['evidence_identity'] != DEPENDENCY_SHA:
        raise InputRefusal('EVIDENCE_BINDING', 'Evidence bundle has not been admitted for this integration')
    if raw['pixel_format'] != 'Mono8' or raw['transport'] != 'USB3-Vision':
        raise InputRefusal('UNSUPPORTED_VALUE', 'This adapter accepts exact Mono8 and USB3-Vision values only')
    if raw['isp_enabled'] not in ('false', 'true', 'unknown'):
        raise InputRefusal('UNSUPPORTED_VALUE', 'ISP must be false, true or unknown')
    fps = snapshot['requirements']['fast_required_fps']
    parsed_fps = parse_fps(fps)
    return {'camera_id': camera, 'isp_enabled': {'false': False, 'true': True, 'unknown': None}[raw['isp_enabled']],
            'pixel_format': raw['pixel_format'], 'transport': raw['transport'], 'fast_required_fps': parsed_fps}


def software_identity():
    import hashlib
    root = Path(__file__).parent
    files = sorted(list(root.glob('*.py')) + list((root / 'static').glob('*.js')) + [root / 'data/approved_runtime_pins.json', root / 'data/assurance_policy.json'])
    return hashlib.sha256(b''.join(f.relative_to(root).as_posix().encode() + b'\0' + f.read_bytes() for f in files)).hexdigest()
