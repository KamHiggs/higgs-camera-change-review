"""Versioned deterministic display summary; engineering equations remain in retained runtime."""
import json
from pathlib import Path
from .contract import NOTICE, SUMMARY_CONTRACT

def read_json(path):
    return json.loads(Path(path).read_text())

def summarize(folder, camera):
    a = folder / 'outputs/analyze/analysis/result.json'
    q = folder / 'outputs/questions/questions/result.json'
    summary = {'summary_contract': SUMMARY_CONTRACT, 'engineering_status': 'EXECUTION_FAILURE', 'notice': NOTICE,
               'synthetic_installation': True, 'camera_id': camera, 'blockers': [], 'unknowns': [], 'evaluations': []}
    processes = read_json(folder / 'processes.json')
    if any(p['exit_code'] not in (0, 3) for p in processes):
        summary['failure_category'] = 'MODEL_REFUSAL' if any(p['exit_code'] == 2 for p in processes) else 'PROCESS_FAILURE'
        summary['failure'] = 'Model refusal or process failure; inspect retained structured process records.'
        return summary
    if not a.exists():
        refusal = folder / 'outputs/analyze/applicability.json'
        summary['engineering_status'] = 'OUTSIDE_MODEL_OR_UNSUPPORTED'
        if refusal.exists(): summary['applicability'] = read_json(refusal)
        return summary
    analysis = read_json(a)
    report_path = folder / 'outputs/analyze/analysis/report.json'
    if analysis.get('execution_status') != 'completed' or not report_path.exists():
        return summary
    report = read_json(report_path)
    summary['analysis_execution_status'] = analysis['execution_status']
    summary['overall_decision_status'] = analysis.get('decision_status')
    summary['applicability'] = read_json(folder / 'outputs/analyze/applicability.json')
    evs = [r for r in report['evaluations'] if r['camera_id'] == camera]
    summary['evaluations'] = evs
    for ev in evs:
        for row in ev['constraints']:
            named = dict(row, variant_id=ev['variant_id'])
            if row['status'] == 'fail': summary['blockers'].append(named)
            elif row['status'] == 'unknown': summary['unknowns'].append(named)
    if q.exists():
        question = read_json(q)
        summary['questions'] = question
        status = (question.get('result') or {}).get('analysis_status')
    else:
        status = None
    summary['engineering_status'] = ('ESTABLISHED_BLOCKER' if summary['blockers'] else
        'CONDITIONAL_EVIDENCE_QUESTION' if status == 'supported' else 'MISSING_EVIDENCE')
    rows = [r for r in summary['applicability'].get('withheld_evidence', [])
            if (r.get('destination') or {}).get('record_id') == 'GEN-' + camera]
    def unique(state):
        return list({r['entry_id']: r for r in rows if r.get('state') == state}.values())
    unresolved = unique('CONDITION_UNRESOLVED')
    quarantined = unique('QUARANTINED')
    inapplicable = unique('CONDITION_INAPPLICABLE')
    premises = sorted({('camera_modes.' + v if v.startswith('CAM-') else v)
                       for r in unresolved for v in r.get('missing', [])})
    summary['evidence'] = {'unresolved_premises': premises, 'condition_unresolved_rows': unresolved,
                           'quarantined_rows': quarantined, 'normally_inapplicable_rows': inapplicable}
    summary['counts'] = {'unresolved_premises': len(premises), 'condition_unresolved_evidence_rows': len(unresolved),
                         'quarantined_evidence_rows': len(quarantined), 'normally_inapplicable_rows': len(inapplicable),
                         'established_constraint_failures': len(summary['blockers']), 'unknown_constraint_evaluations': len(summary['unknowns'])}
    summary['reasons'] = []
    if unresolved:
        summary['reasons'].append({'reason_class': 'OPERATING_DECLARATION_UNRESOLVED',
                                   'missing_premises': premises, 'affected_source_rows': [r['entry_id'] for r in unresolved]})
    if quarantined:
        summary['reasons'].append({'reason_class': 'EVIDENCE_QUARANTINED', 'affected_source_rows': [r['entry_id'] for r in quarantined]})
    if summary['engineering_status'] == 'MISSING_EVIDENCE' and quarantined:
        summary['engineering_status'] = 'UNRESOLVED_EVIDENCE'
    # The selected camera's applicability is not a statement about every other camera.
    summary['scope'] = 'Bounded non-voltage synthetic installation; real source captures; no full camera compatibility.'
    return summary

