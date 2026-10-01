"""Mapper-defined change relevance. No engineering result is used to infer relevance."""
from .contract import parse_fps, InputRefusal

def compare_snapshots(old, new):
    try:
        a_fps = parse_fps(old['requirements']['fast_required_fps'])
        b_fps = parse_fps(new['requirements']['fast_required_fps'])
    except (InputRefusal, KeyError, TypeError):
        return {'state': 'INVALID_COMPARISON_INPUT', 'changes': [], 'meaning': 'No current/stale verdict: invalid request-local FPS assumption'}
    def flatten(value, prefix=''):
        if isinstance(value, dict):
            result = {}
            for k, v in value.items():
                if prefix == '' and k == 'audit': continue
                result.update(flatten(v, prefix + '/' + k))
            return result
        return {prefix: value}
    a, b = flatten(old), flatten(new); changes = []
    camera = (old.get('parameters', {}).get('camera_id') or {}).get('raw_value')
    for field in sorted(set(a) | set(b)):
        if field in a and field in b and a[field] == b[field]: continue
        cls = 'EVIDENCE_OR_IDENTITY_CHANGE'
        if field in ('/current_part/name', '/substitute_part/name', '/current_part/role'):
            cls = 'DISPLAY_CONTEXT_CHANGE'
        elif field == '/requirements/fast_required_fps':
            cls = 'DECISION_INPUT_CHANGE' if a_fps != b_fps else 'DISPLAY_CONTEXT_CHANGE'
        elif field.startswith('/parameters/') and field.endswith('/raw_value'):
            key = field.split('/')[2]
            if key in ('isp_enabled', 'pixel_format', 'transport'):
                cls = 'DISPLAY_CONTEXT_CHANGE' if key == 'isp_enabled' and camera != 'CAM-FLIR' else 'DECISION_INPUT_CHANGE'
        changes.append({'field': field, 'before': a.get(field), 'after': b.get(field), 'change_class': cls})
    classes = sorted({x['change_class'] for x in changes})
    state = ('STALE_EVIDENCE_BINDING' if 'EVIDENCE_OR_IDENTITY_CHANGE' in classes else
             'STALE_ANALYSIS' if 'DECISION_INPUT_CHANGE' in classes else 'CURRENT_ANALYSIS')
    return {'state': state, 'change_classes': classes, 'changes': changes,
            'analytically_current': state == 'CURRENT_ANALYSIS',
            'assumption': {'saved_raw_fps': old['requirements']['fast_required_fps'], 'compared_raw_fps': new['requirements']['fast_required_fps'],
                           'basis': 'saved_assessment' if a_fps == b_fps else 'draft_what_if', 'maintained_project_requirement': False},
            'meaning': 'Point-in-time mapped inventory and request-local assumption comparison; not physical verification or a project-requirements database.'}
