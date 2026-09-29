"""Finite JSON and human views rendered from the same canonical analysis."""
import json
import math
import html
from fractions import Fraction

ADAPTER = '''"""Proposed timestamp adapter. Unapproved; not validated on real equipment."""

def normalize_timestamp(sensor_timestamp_ms, variant_id, plan):
    offsets = plan["offset_ms_by_variant"]
    if variant_id not in offsets:
        raise ValueError("Unknown variant: " + str(variant_id))
    return sensor_timestamp_ms + offsets[variant_id]
'''


def native(value):
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return value.numerator
        try:
            result = float(value)
        except OverflowError as exc:
            raise ValueError('Numeric encoding limitation: rational exceeds finite JSON float range') from exc
        if not math.isfinite(result):
            raise ValueError('Numeric encoding limitation: nonfinite output')
        return result
    if isinstance(value, dict):
        return {k:native(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)):
        return [native(v) for v in value]
    return value


def dumps(value):
    return json.dumps(native(value),indent=2,ensure_ascii=True,allow_nan=False)+'\n'


def view(report):
    esc=lambda v:html.escape(str(v))
    blocks=['<!doctype html><html lang="en"><meta charset="utf-8"><title>Engineering change review</title>',
        '<style>body{font:16px system-ui;max-width:1200px;margin:40px auto;padding:0 20px;color:#173046}table{border-collapse:collapse;width:100%;margin:16px 0}th,td{border:1px solid #cbd5df;padding:8px;text-align:left;vertical-align:top}pre{white-space:pre-wrap;background:#f1f4f7;padding:16px}h2{margin-top:36px}.boundary{padding:18px;background:#fff0cc}</style>',
        '<h1>'+esc(report['case_id'])+' — '+esc(report['status'])+'</h1>',
        '<p class="boundary"><strong>Proposed, unapproved, not hardware-validated.</strong> Calculated feasibility and software execution do not grant deployment approval.</p>',
        '<h2>Selected proposal</h2><pre>'+esc(dumps(report['selected_plan']))+'</pre>',
        '<h2>Current configuration</h2><pre>'+esc(dumps(report['current_configurations']))+'</pre>',
        '<h2>Candidate and policy outcomes</h2><pre>'+esc(dumps(report['policy_evaluations']))+'</pre>']
    for e in report['evaluations']:
        blocks.append('<h2>'+esc(e['camera_id'])+' / '+esc(e['variant_id'])+' — '+esc(e['status'])+'</h2>')
        blocks.append('<p>Feasible offset domain: '+esc(e['feasible_offset_interval_kind'])+' '+esc(e['feasible_offset_interval_ms'])+'</p>')
        blocks.append('<table><tr><th>Constraint</th><th>Status</th><th>Value / limit</th><th>Comparison</th><th>Sources and fields</th></tr>')
        for c in e['constraints']:
            blocks.append('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in [c['constraint'],c['status'],str(c['value'])+' / '+str(c['limit']),c['comparison'],c['locators']])+'</tr>')
        blocks.append('</table>')
    blocks.append('<h2>Independent evidence audit</h2>')
    for e in report['evidence_review']:
        blocks.append('<h3>'+esc(e['source_id'])+'</h3><p>'+esc(', '.join(e['flags']))+'</p><p>'+esc(e['reason'])+'</p>')
        blocks.append('<table><tr><th>Field</th><th>Recorded</th><th>Selected</th><th>State</th></tr>')
        for c in e['applicability_comparisons']:
            blocks.append('<tr>'+''.join('<td>'+esc(c[k])+'</td>' for k in ('field','recorded','selected','state'))+'</tr>')
        blocks.append('</table>')
    for title,key in [('Source authority','source_review'),('Impact chains','impact_chains'),('Findings','findings'),('Required revalidation','required_retests'),('Missing evidence and blockers','evidence_requests'),('Selection evidence required','selection_evidence_requests'),('Limitations','limitations')]:
        blocks.append('<h2>'+title+'</h2><pre>'+esc(dumps(report[key]))+'</pre>')
    return '\n'.join(blocks)+'\n</html>\n'


def revalidation(report):
    lines=['# Revalidation plan','', '**Proposed, unapproved, not hardware-validated.**', '',
           'Status: '+report['status'], '', 'Retain all original pre-change records. No hardware test has been created or run by this application.','']
    for item in report['required_retests']:
        lines += ['## Variant '+str(item['variant_id']), '', item['action'], '',
                  'Exact configuration:', '```json', dumps(item['configuration']).rstrip(),'```','']
        lines += ['- '+c+': test the exact configuration, record observations and guaranteed source bounds as separate evidence.' for c in item['checks']]
        lines += ['', 'Retain evidence: '+', '.join(item['retain_obsolete_evidence']), '']
    lines += ['## Evidence required / established blockers','', '```json',dumps(report['evidence_requests']).rstrip(),'```','', 'Selection evidence:', '```json',dumps(report['selection_evidence_requests']).rstrip(),'```','',
              'If a known constraint fails, an alternative guaranteed specification meeting that named limit would change the conclusion. Changing hardware, required FPS, speed or requirements is outside the permitted plan and is only a counterfactual.', '',
              'After both software and hardware revalidation, obtain explicit human engineering approval. A saved PASS, a source document or this report is not approval.','']
    return '\n'.join(lines)
