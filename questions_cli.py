"""Case-folder adapter for the retained Python CogniMap decision_questions method.

All nested analyses use detached values loaded once. No demonstration fallback.
No model, supplier lookup, source write, or executable configuration is performed.
"""
import hashlib
import json
from pathlib import Path
import sys
from fractions import Fraction

import sources
import camera_cognimap as cm


def exact_export(value):
    """Keep derived rational values exact; established finite reports stay native."""
    if isinstance(value, Fraction):
        return {'$rational': [str(value.numerator), str(value.denominator)]}
    if isinstance(value, dict):
        return {k: exact_export(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [exact_export(v) for v in value]
    return value


def load_snapshot(case_dir):
    root = Path(case_dir).resolve(strict=True)
    identities = {}

    def read_document(path):
        raw = path.read_bytes()
        identities[str(path.relative_to(root))] = hashlib.sha256(raw).hexdigest()
        return sources.loads(raw.decode('utf-8'))

    root, case, records = sources.load_case(root, read_document=read_document)
    # Detect writes during loading before any analysis is issued. This is not an
    # OS snapshot/lock: the result identities describe the exact captured bytes.
    for name, digest in identities.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise sources.InputError('Case changed during capture: ' + name)
    base = {'model_id': cm.CAMERA_MODEL, 'case_data': case,
            'source_records': [{k:v for k,v in r.items() if k != '_path'}
                               for r in records.values()]}
    return root, base, identities


def explain(envelope, case_id):
    lines = ['# Camera evidence questions', '', 'Case: ' + case_id, '',
             '**Conditional synthetic analysis. Not deployment approval.**', '']
    result = envelope.get('result')
    if result is None:
        return '\n'.join(lines + [envelope['execution_status'] + ': ' + envelope.get('error',''), ''])
    current = result['current_decision']; plan = current['selected_plan']
    lines += ['## Current supported decision', '',
              current['execution_status'] + ' / ' + str(current['decision_status']), '']
    if plan:
        lines += ['Selected ' + plan['camera_id'] + ', ' + plan['policy'] +
                  ', ' + str(current['cost_points_exact']) + ' synthetic cost points.', '']
    elif current.get('error'):
        lines += [current['error'], '']
    else:
        lines += ['No supported plan selected.', '']
    target = result['target']
    lines += ['## Target evidence', '', 'Camera: ' + target['camera_id'],
              'Requested field: ' + target['requested_locator'],
              'Source revision: ' + str(target['spec_revision']), '']
    for loc in target['locators']:
        lines += ['- ' + loc['source_id'] + ': ' + loc['file'] + '#' + loc['locator'] +
                  ' (requested ' + loc['requested_locator'] + ')']
    lines += ['', '## Conditional result', '', result['explanation'], '',
              '## Boundary derivation', '']
    for row in result['derivation']:
        lines += ['- ' + row['variant_id'] + ': speed=' + str(row['speed_m_s']) +
                  ' m/s; error limit=' + str(row['limit_mm']) + ' mm; host jitter=' +
                  str(row['host_jitter_ms']) + ' ms; bias=' + str(row['bias_ms']) +
                  ' ms; timing allowance=' + str(row['a_ms']) + ' ms.']
        for loc in row['source_locators']:
            lines += ['  - ' + loc['source_id'] + '#' + loc['locator']]
    for policy in result['policies']:
        lines += ['', policy['policy'] + ' controls: ' +
                  json.dumps(policy['controlling_constraints'], ensure_ascii=True)]
    lines += ['', 'Exact rational domains, hypothetical witnesses, source identities and supplied operating conditions are retained in result.json.',
              'This report uses one captured case. Separate analyze and questions invocations each capture their own inputs; a later command may see a later revision.', '']
    return '\n'.join(lines)


def run_questions(case_dir, camera_id, out_dir):
    # Delayed import retains app.run and its established public command.
    from app import validate_output
    root, base, identities = load_snapshot(case_dir)
    output = validate_output(root, out_dir)
    # Also reject symlinked parent paths, even if they resolve to a disjoint path.
    raw = Path(out_dir).absolute()
    if any(p.is_symlink() for p in (raw,) + tuple(raw.parents)):
        raise sources.InputError('Output cannot traverse a symlink')
    result = cm.execute('camera', 'decision_questions', {'camera_id':camera_id, 'base':base})
    result['integration'] = {'application':'Higgs Camera Change Review',
                             'version':cm.APPLICATION_VERSION,
                             'method_origin':'Higgs Python CogniMap 0.1.2',
                             'case_id':base['case_data']['case_id'],
                             'source_sha256':identities,
                             'snapshot_kind':'one loaded case; no nested disk reads'}
    text = json.dumps(exact_export(result), indent=2, ensure_ascii=True, allow_nan=False) + '\n'
    if result['execution_status'] == 'input_error':
        print(text, file=sys.stderr, end='')
        return 2
    explanation = explain(result, base['case_data']['case_id'])
    # Construct all content before writes, retain safe fresh output behavior.
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise sources.InputError('Output became nonempty before write; refusing overwrite')
    for name, contents in [('result.json', text), ('explanation.md', explanation)]:
        with (output/name).open('x', encoding='utf-8') as stream:
            stream.write(contents)
    print(text, end='')
    if result['execution_status'] != 'completed':
        return {'unsupported':3, 'numeric_encoding_error':4}.get(result['execution_status'], 5)
    analysis = result['result']
    if analysis['current_decision']['execution_status'] == 'numeric_encoding_error':
        return 4
    return 3 if analysis['analysis_status'] == 'unsupported' else 0
