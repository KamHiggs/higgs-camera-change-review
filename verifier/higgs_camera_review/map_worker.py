"""Projection in its own process using the dependency's exact serializer.

Only an extracted per-review working copy is edited. No engine rules change.
"""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root / 'tools'))
from common import load, dumps, semantic_sha, sha

inputs = load(Path(sys.argv[2]))
ledger_path = root / 'evidence/EVIDENCE_LEDGER.json'
captures_path = root / 'evidence/SOURCE_CAPTURES.json'
ledger, captures = load(ledger_path), load(captures_path)
scenario = load(root / 'scenarios/A_compatible.json')
camera = inputs['camera_id']
scenario['scenario_id'] = 'INVENTREE-SYNTHETIC-INSTALLATION'
scenario['premises']['pixel_format'] = inputs['pixel_format']
scenario['premises']['transport'] = inputs['transport']
scenario['camera_modes'][camera]['pixel_format'] = inputs['pixel_format']
if camera == 'CAM-FLIR':
    scenario['camera_modes'][camera]['isp_enabled'] = inputs['isp_enabled']

source = root / 'evidence/USER_SYNTHETIC_REQUIREMENTS.json'
source.write_text(dumps({'synthetic': True, 'classification': 'synthetic_user_requirement',
    'LINE-FAST': {'required_fps': inputs['fast_required_fps']},
    'meaning': 'Fictional installation requirement; not observed manufacturer performance'}) + '\n')
sid = 'SYN-INVENTREE-USER-REQUIREMENTS'
ledger['sources'][sid] = {'origin': 'synthetic', 'sha256': sha(source), 'url': None,
    'locator_base': 'evidence/USER_SYNTHETIC_REQUIREMENTS.json'}
changed = []
for e in ledger['entries']:
    dest = e.get('destination') or {}
    if dest == {'record_id': 'SYN-REQ-LINE-FAST', 'pointer': '/data/required_fps'}:
        c = next(c for c in captures['captures'] if c['capture_id'] == e['capture_id'])
        for obj in (c, e):
            obj['source_id'] = sid
            obj['lexical_value'] = str(inputs['fast_required_fps'])
            obj['locator'] = 'evidence/USER_SYNTHETIC_REQUIREMENTS.json#/LINE-FAST/required_fps'
        c['source_document_sha256'] = sha(source)
        e['normalized_exact'] = inputs['fast_required_fps']
        e['capture_sha256'] = semantic_sha(c)
        e['adjudication_reason'] = 'Explicit user requirement for the fictional installation; no manufacturer guarantee inferred'
        changed.append(e['id'])
if len(changed) != 1:
    raise ValueError('Expected exactly one synthetic requirement destination')
ledger_path.write_text(dumps(ledger) + '\n')
captures_path.write_text(dumps(captures) + '\n')
(root / 'scenarios/inventree.json').write_text(dumps(scenario) + '\n')
print(dumps({'changed_entries': changed, 'scenario': 'scenarios/inventree.json',
            'frozen_dependency_modified': False, 'working_projection_modified': True}))
