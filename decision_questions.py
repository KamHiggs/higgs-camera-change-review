"""One missing guaranteed jitter bound, analyzed over the existing synthetic model.

Thresholds are analytical Fractions. Region witnesses exercise existing simulation;
they do not establish every point's finite-encoding behavior or create real facts.
"""
from fractions import Fraction as Q
import engine
import sources as cs

FIELD = 'timestamp_jitter_bound_ms'
POINTER = '/data/' + FIELD


def _effect(cost, current_cost):
    if current_cost is None:
        return 'create_first_feasible_plan'
    if cost < current_cost:
        return 'reduce_established_cost'
    if cost == current_cost:
        return 'add_equal_cost_alternative'
    return 'more_expensive_alternative'


def _domain(threshold):
    return {'kind': 'unbounded' if threshold is None else 'empty' if threshold < 0 else 'bounded',
            'lower_ms': Q(0), 'upper_ms': threshold, 'lower_inclusive': True,
            'upper_inclusive': threshold is not None and threshold >= 0,
            'meaning': 'nonnegative guaranteed jitter; mathematical domain only'}


def _contains(domain, value):
    return domain['kind'] != 'empty' and (domain['upper_ms'] is None or value <= domain['upper_ms'])


def _regions(policies):
    cuts = sorted({Q(0)} | {p['domain']['upper_ms'] for p in policies
                          if p['domain']['upper_ms'] is not None and p['domain']['upper_ms'] >= 0})
    rows = []
    for i, left in enumerate(cuts):
        rows.append({'lower_ms': left, 'upper_ms': left, 'lower_inclusive': True,
                     'upper_inclusive': True, 'representative_ms': left})
        right = cuts[i+1] if i+1 < len(cuts) else None
        rows.append({'lower_ms': left, 'upper_ms': right, 'lower_inclusive': False,
                     'upper_inclusive': False, 'representative_ms': (left+right)/2 if right is not None else left+1})
    return rows


def _explanation(out):
    cid = out['target']['camera_id']; lines = [
        'Candidate: ' + cid + '. Current decision: ' + str(out['current_decision']['decision_status']) + '.',
        'Analysis: ' + out['analysis_status'] + '.']
    if out['blockers']:
        lines.append('Jitter alone cannot overcome: ' + '; '.join(out['blockers']) + '.')
    for detail in out['blocker_details']:
        lines.append(detail['variant_id']+' '+detail['constraint']+': value '+str(detail['value'])+' must satisfy '+detail['comparison']+' '+str(detail['limit'])+'; source locators are retained in blocker_details.')
    if out['remaining_unknowns']:
        lines.append('Single-answer sufficiency is not established: ' + '; '.join(out['remaining_unknowns']) + '.')
    for p in out['policies']:
        d = p['domain']; t = p['threshold_ms']
        condition = ('any nonnegative guaranteed bound' if d['kind']=='unbounded' else
                     'no nonnegative bound (threshold '+str(t)+' ms)' if d['kind']=='empty' else
                     '0 <= guaranteed jitter <= '+str(t)+' ms, inclusive')
        lines.append(p['policy'] + ': ' + condition + '; cost ' + str(p['cost_points']) +
                     ' synthetic points; if feasible: ' + p['effect_if_this_policy_feasible'].replace('_',' ') + '.')
    for r in out['regions']:
        lo, hi = r['lower_ms'], r['upper_ms']
        domain = ('j = '+str(lo) if lo == hi else str(lo)+' < j' if hi is None else str(lo)+' < j < '+str(hi))
        lines.append(domain+' ms: '+r['effect'].replace('_',' ')+(('; best target policy '+r['best_target_policy']+', '+str(r['target_cost_points'])+' points') if r['best_target_policy'] else '')+'. Conditional mathematics only.')
    if out['evidence_request']:
        lines.append('Ask: '+out['evidence_request']['text'])
    else:
        lines.append('No jitter-only request is issued as sufficient to improve or add a tied option to this decision.')
    failures = [r for r in out['regions'] if r['preview']['execution_status'] != 'completed']
    if failures:
        lines.append('Some hypothetical witnesses did not execute: '+', '.join(sorted({r['preview']['execution_status'] for r in failures}))+'. Their errors do not mean physical impossibility.')
    lines += out['limitations']
    lines.append('Mathematical conditions are not a guaranteed executable configuration. No supplier fact, deployment approval, or hardware qualification was created.')
    return '\n\n'.join(lines)


def decision_questions(inputs, api):
    api.keys(inputs, {'camera_id','base'}, {'camera_id'})
    cid = inputs['camera_id']; cs.string(cid, 'camera_id')
    base = inputs.get('base', {})
    case, records = api._camera_prepare(base)
    if cid not in case['candidate_camera_ids']:
        raise api.ContractError('Target must be a declared candidate')
    before = api.digest({'case':case, 'records':records})
    resolved, reviews, links = cs.resolve_sources(records)
    ent = cs.entity(resolved, 'camera', cid); c = ent['data']
    current = api.execute('camera', 'evaluate', base)
    if current['execution_status'] == 'input_error':
        raise api.ContractError(current['error'])
    report = current.get('result',{}).get('report',{})
    selected = report.get('selected_plan')
    current_cost = None
    if selected:
        current_cost = cs.entity(resolved, 'camera', selected['camera_id'])['data']['migration_cost_points'] + engine.POLICY_COST[selected['policy']]
    locators = [{'source_id':sid, 'file':records[sid]['_path'],
                 'locator':cs.existing_pointer(records[sid], POINTER), 'requested_locator':POINTER,
                 'source_identity':api.digest({k:v for k,v in records[sid].items() if k!='_path'})}
                for sid in ent['source_ids']]
    out = {'decision_status':'conditional_evidence_analysis','analysis_status':'unsupported',
           'run_kind':'conditional_evidence_analysis','model_id':api.CAMERA_MODEL,
           'cartridge_version':api.VERSION,'base_input_identity':before,'base_unchanged':True,
           'current_decision':{'execution_status':current['execution_status'],'decision_status':current['decision_status'],
                               'input_identity':before,'request_identity':current.get('request_identity'),
                               'cartridge_version':api.VERSION,'selected_plan':selected,'cost_points_exact':current_cost,
                               'error':current.get('error')},
           'target':{'camera_id':cid,'field':FIELD,'source_id':ent['representative'],
                     'source_ids':ent['source_ids'],'spec_revision':records[ent['representative']].get('revision') if ent['representative'] else None,'requested_locator':POINTER,'locators':locators},
           'blockers':[], 'blocker_details':[], 'remaining_unknowns':[], 'policies':[], 'regions':[], 'derivation':[],
           'evidence_request':None,'executable_configuration_promised':False,
           'deployment_qualified':False,'human_approval_recorded':False,
           'rule_ids':['R-AUTH','R-U01','R-TIME','R-SELECT','R-SERIAL','R-EVIDENCE','R-SIM'],
           'limitations':['Synthetic model only; facts are supplied, not independently authenticated.',
                          'Cost comparison covers established plans only; unresolved other candidates can still matter.',
                          'Representative previews are hypothetical witnesses, not a proof of encoding over a whole region.']}
    def finish(status):
        out['analysis_status'] = status
        if before != api.digest({'case':case,'records':records}):
            raise RuntimeError('Decision question changed base inputs')
        out['explanation'] = _explanation(out)
        return out
    if current['execution_status'] != 'completed':
        out['remaining_unknowns'].append('Current analysis did not complete: '+current['execution_status'])
        return finish('unsupported')
    evaluations = [engine.evaluate(cid,v,ent,cs.entity(resolved,'variant',v)) for v in case['variant_ids']]
    for ev in evaluations:
        out['blockers'].extend(ev['variant_id']+': '+x for x in ev['blockers'])
        for check in ev['constraints']:
            if check['status']=='fail':
                out['blocker_details'].append(dict(check, variant_id=ev['variant_id']))
            if check['status']=='unknown':
                out['remaining_unknowns'].extend(ev['variant_id']+': '+x for x in check['missing_fields'] if x!=FIELD)
    baselines = {e['data'].get('camera_id') for (kind,subject),e in resolved.items() if kind=='configuration'}
    if c.get('available') is False or cid in baselines:
        out['blockers'].append('Target is unavailable or is an excluded baseline camera')
    if ent['representative'] is None:
        out['remaining_unknowns'].append('Unconflicted active scalar specification identity required (U01); '+', '.join(ent['conflicts']))
    for field in ('available','migration_cost_points'):
        if c.get(field) is None: out['remaining_unknowns'].append(field)
    if not case.get('base_firmware_revision'):
        out['remaining_unknowns'].append('base_firmware_revision')
    out['remaining_unknowns'] = sorted(set(out['remaining_unknowns']))
    if out['blockers']:
        return finish('blocked')
    if out['remaining_unknowns']:
        return finish('unsupported')
    if c.get(FIELD) is not None:
        out['limitations'].append('The target guaranteed jitter field is already supplied; this operation does not audit its authenticity or request unrelated missing descriptions.')
        return finish('not_needed')
    positive = []
    for vid in case['variant_ids']:
        variant = cs.entity(resolved,'variant',vid); v=variant['data']; s=v['speed_m_s']; b=c['timestamp_bias_ms_by_variant'][vid]
        row={'variant_id':vid,'speed_m_s':s,'limit_mm':v['max_registration_error_mm'],
             'host_jitter_ms':v['host_jitter_bound_ms'],'bias_ms':b,'supplied_variant_operating_conditions':dict(v),
             'source_locators':engine.locators(ent,[FIELD,'timestamp_bias_ms_by_variant/'+vid])+engine.locators(variant,['speed_m_s','max_registration_error_mm','host_jitter_bound_ms'])}
        if s==0:
            row.update(a_ms=None,zero_speed=True,meaning='No interval restriction once required operands, including the guarantee, are supplied')
        else:
            a=Q(v['max_registration_error_mm'],s)-v['host_jitter_bound_ms']
            row.update(a_ms=a,zero_speed=False,lower_at_zero_ms=-b-a,upper_at_zero_ms=-b+a)
            positive.append(row)
        out['derivation'].append(row)
    if positive:
        low=max(x['lower_at_zero_ms'] for x in positive); high=min(x['upper_at_zero_ms'] for x in positive)
        ts=(high-low)/2; tp=min(x['a_ms'] for x in positive)
        controls={'shared':{'lower_controlling_variants':[x['variant_id'] for x in positive if x['lower_at_zero_ms']==low],
                            'upper_controlling_variants':[x['variant_id'] for x in positive if x['upper_at_zero_ms']==high]},
                  'per_variant':{'limiting_variants':[x['variant_id'] for x in positive if x['a_ms']==tp]}}
    else:
        ts=tp=None;controls={'shared':{'limiting_variants':[]},'per_variant':{'limiting_variants':[]}}
        out['limitations'].append('All speeds are zero: no finite timing threshold; the guarantee is still a required input under the unchanged model, not a demonstrated timing improvement.')
    for policy,t in [('shared',ts),('per_variant',tp)]:
        cost=c['migration_cost_points']+engine.POLICY_COST[policy]
        out['policies'].append({'policy':policy,'threshold_ms':t,'units':'ms','domain':_domain(t),
            'boundary_outcomes':{'below':'mathematically_feasible' if t is not None and t>0 else 'no_nonnegative_values' if t is not None else 'not_applicable_unbounded',
                                 'at':'mathematically_feasible' if t is not None and t>=0 else 'outside_nonnegative_domain' if t is not None else 'not_applicable_unbounded',
                                 'above':'mathematically_infeasible' if t is not None else 'not_applicable_unbounded'},
            'controlling_constraints':controls[policy],'cost_points':cost,
            'effect_if_this_policy_feasible':_effect(cost,current_cost),
            'equation_reference':'docs/DECISION_QUESTIONS_CONTRACT.md',
            'decision_scope':'conditional_mathematics_only','guarantee_required':True})
    for region in _regions(out['policies']):
        j=region['representative_ms']
        feasible=[p for p in out['policies'] if _contains(p['domain'],j)]
        best=min(feasible,key=lambda p:p['cost_points']) if feasible else None
        region.update(decision_scope='conditional_mathematics_only',feasible_target_policies=[p['policy'] for p in feasible],
                      best_target_policy=best['policy'] if best else None,
                      target_cost_points=best['cost_points'] if best else None,
                      effect=_effect(best['cost_points'],current_cost) if best else 'no_target_plan')
        preview = api.execute('camera','simulate',{'base':base,'camera_id':cid,'bounds_ms':[j]})
        witness={'execution_status':preview['execution_status'],'hypothetical':True,'decision_scope':'hypothetical_only',
                 'assumed_guaranteed_jitter_ms':j,'coverage':'One representative only; not proof for the whole region',
                 'error':preview.get('error'),'target_selected_and_serialized':False}
        if preview['execution_status']=='completed':
            scenario=preview['result']['scenarios'][0]; sr=scenario['report']; sp=sr['selected_plan']
            witness.update(input_identity=scenario['input_identity'],assumption=scenario['assumption'],
                           result={'decision_scope':'hypothetical_only','hypothetical':True,'decision_status':sr['status'],
                                   'selected_plan':sp,'serialized_plan_checks':sr['serialized_plan_checks']},
                           target_selected_and_serialized=sp is not None and sp['camera_id']==cid)
        region['preview']=witness;out['regions'].append(region)
    useful=any(r['effect'] in {'create_first_feasible_plan','reduce_established_cost','add_equal_cost_alternative'} for r in out['regions'])
    feasible_regions=[r for r in out['regions'] if r['best_target_policy']]
    zero_encoding_block=(len(feasible_regions)==1 and feasible_regions[0]['lower_ms']==feasible_regions[0]['upper_ms']==0
                         and feasible_regions[0]['preview']['execution_status']=='numeric_encoding_error')
    if zero_encoding_block:
        useful=False;out['limitations'].append('The sole mathematically admissible value is zero and its preview fails finite encoding. A jitter guarantee alone cannot produce an emitted target plan with the current implementation.')
    if useful:
        out['evidence_request']={'field':FIELD,'source_id':ent['representative'],'locator':POINTER,
            'units':'ms','evidence_standard':'Applicable guaranteed upper bound; a typical value, finite sample or PASS is insufficient',
            'operating_conditions':out['derivation'],'source_requirements':'Traceable authoritative specification for the exact candidate/spec revision and relevant conditions; retain provenance and explicit supersession if revised. Source authenticity remains externally reviewed.',
            'text':'Obtain an applicable guaranteed upper bound in ms for '+cid+' ('+ent['representative']+'), covering every listed variant operating condition. Compare it with the exact policy domains above. A typical value, finite observations or a PASS statement will not establish this guarantee. Preserve the specification revision, provenance and any explicit supersession; then rerun the ordinary solver and its finite-encoding checks.'}
    return finish('supported')
