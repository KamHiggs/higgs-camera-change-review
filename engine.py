"""Exact synthetic constraint solver, policy selection and independent evidence audit."""
from fractions import Fraction
from sources import entity, equal, existing_pointer, loads
from reporting import dumps

POLICY_COST = {'shared':0, 'per_variant':3}
LIMIT_FIELDS = {'registration_error_mm':'max_registration_error_mm', 'mm_per_pixel':'max_mm_per_pixel',
                'bandwidth_MB_s':'link_capacity_MB_s','power_W':'power_budget_W'}
APP_FIELDS = ('variant_id','camera_id','spec_source_id','firmware_revision','policy','offset_ms')
U01 = ('U01 conservative identity hold: agreed physical leaves remain usable, but any genuine active '
       'camera data conflict withholds scalar spec selection. Descriptive-only conflicts may cause '
       'unnecessary refusal; this is a disclosed interpretation, not benchmark adjudication.')


def locators(ent, fields):
    results = []
    for sid in ent['source_ids']:
        document = {'data':ent.get('_source_data',{}).get(sid,ent['data'])}
        for field in fields:
            parts = field.split('/')
            if parts[0] == 'timestamp_bias_ms_by_variant' and len(parts)>1:
                parts = [parts[0], '/'.join(parts[1:])]
            requested = '/data/' + '/'.join(p.replace('~','~0').replace('/','~1') for p in parts)
            actual = existing_pointer(document,requested)
            results.append({'source_id':sid,'locator':actual,'requested_locator':requested,
                            'field_present':actual==requested})
    return results


def evaluate(camera_id, variant_id, camera, variant):
    c, v = camera['data'], variant['data']
    checks, metrics = [], {'mm_per_pixel':None,'bandwidth_MB_s':None}
    def check(name, cfields, vfields, compute, comparison, limit):
        values = [c.get(f) for f in cfields] + [v.get(f) for f in vfields]
        missing = [f for f,val in zip(cfields + vfields,values) if val is None]
        value = None
        passed = None
        if not missing:
            value, passed = compute()
        row = {'constraint':name,'status':'unknown' if passed is None else ('pass' if passed else 'fail'),
               'value':value,'limit':limit,'comparison':comparison,'missing_fields':missing,
               'source_ids':sorted(set(camera['source_ids']+variant['source_ids'])),
               'locators':locators(camera,cfields)+locators(variant,vfields)}
        checks.append(row)
        return value
    check('frame_rate',['max_fps'],['required_fps'],lambda:(c['max_fps'],c['max_fps']>=v['required_fps']),'>=',v.get('required_fps'))
    metrics['mm_per_pixel'] = check('resolution',['image_width_px'],['field_of_view_mm','max_mm_per_pixel'],
        lambda:(Fraction(v['field_of_view_mm'],c['image_width_px']), Fraction(v['field_of_view_mm'],c['image_width_px'])<=v['max_mm_per_pixel']), '<=',v.get('max_mm_per_pixel'))
    metrics['bandwidth_MB_s'] = check('throughput',['image_width_px','image_height_px','bytes_per_pixel'],['required_fps','link_capacity_MB_s'],
        lambda:(Fraction(c['image_width_px']*c['image_height_px']*c['bytes_per_pixel']*v['required_fps'],1000000),
        Fraction(c['image_width_px']*c['image_height_px']*c['bytes_per_pixel']*v['required_fps'],1000000)<=v['link_capacity_MB_s']), '<=',v.get('link_capacity_MB_s'))
    check('power',['power_W'],['power_budget_W'],lambda:(c['power_W'],c['power_W']<=v['power_budget_W']), '<=',v.get('power_budget_W'))
    bounds, supply = c.get('supply_range_V'), v.get('supply_voltage_V')
    voltage = None
    if bounds is not None and supply is not None:
        if bounds[0] is not None and supply < bounds[0] or bounds[1] is not None and supply > bounds[1]:
            voltage = False
        elif all(x is not None for x in bounds):
            voltage = True
    checks.append({'constraint':'voltage','status':'unknown' if voltage is None else ('pass' if voltage else 'fail'),
        'value':supply,'limit':bounds,'comparison':'inside inclusive range','missing_fields':['supply voltage/range'] if voltage is None else [],
        'source_ids':sorted(set(camera['source_ids']+variant['source_ids'])),
        'locators':locators(camera,['supply_range_V'])+locators(variant,['supply_voltage_V'])})
    check('transport',['transport'],['transport'],lambda:(c['transport'],c['transport']==v['transport']), '==',v.get('transport'))
    speed, limit, cj, hj = (v.get('speed_m_s'), v.get('max_registration_error_mm'), c.get('timestamp_jitter_bound_ms'), v.get('host_jitter_bound_ms'))
    bias = (c.get('timestamp_bias_ms_by_variant') or {}).get(variant_id)
    missing = [name for name,val in [('speed_m_s',speed),('max_registration_error_mm',limit),('timestamp_jitter_bound_ms',cj),('host_jitter_bound_ms',hj),('timestamp_bias_ms_by_variant/'+variant_id,bias)] if val is None]
    kind, interval, irreducible, radius = 'unknown', None, None, None
    if all(x is not None for x in (speed,limit,cj,hj)):
        irreducible = speed*(cj+hj)
        if irreducible > limit:
            kind = 'empty'
        elif not missing:
            if speed == 0:
                kind = 'unbounded'
            else:
                radius = Fraction(limit,speed)-cj-hj
                interval = [-bias-radius,-bias+radius]
                kind = 'bounded'
    checks.append({'constraint':'timing','status':'fail' if kind=='empty' else 'pass' if kind in {'bounded','unbounded'} else 'unknown',
        'value':irreducible,'limit':limit,'comparison':'minimum achievable worst-case error <= limit',
        'missing_fields':missing,'source_ids':sorted(set(camera['source_ids']+variant['source_ids'])),
        'locators':locators(camera,['timestamp_jitter_bound_ms','timestamp_bias_ms_by_variant/'+variant_id])+locators(variant,['speed_m_s','max_registration_error_mm','host_jitter_bound_ms'])})
    blockers = [row['constraint'] + ': established failure' for row in checks if row['status']=='fail']
    unknowns = [row['constraint'] + ': missing/conflicting ' + ', '.join(row['missing_fields']) for row in checks if row['missing_fields']]
    status = 'infeasible' if blockers else 'unknown' if any(row['status']=='unknown' for row in checks) else 'feasible'
    metrics.update(minimum_registration_error_mm=irreducible, timing_radius_ms=radius)
    return {'camera_id':camera_id,'variant_id':variant_id,'status':status,'metrics':metrics,
        'feasible_offset_interval_ms':interval,'feasible_offset_interval_kind':kind,'blockers':blockers,'unknowns':unknowns,
        'source_ids':sorted(set(camera['source_ids']+variant['source_ids'])),'constraints':checks}


def policy_evaluation(camera_id, policy, camera, evaluations, baseline_ids):
    c = camera['data']; reasons = []
    blocked = any(e['status']=='infeasible' for e in evaluations)
    unknown = any(e['status']=='unknown' for e in evaluations)
    if blocked: reasons.append('Established variant constraint failure')
    if unknown: reasons.append('Missing or conflicting physical facts')
    available = c.get('available')
    if available is False or camera_id in baseline_ids:
        blocked = True; reasons.append('Unavailable camera or baseline camera is not selectable')
    elif available is None:
        unknown = True; reasons.append('Availability is unknown, not false')
    bounded = [e['feasible_offset_interval_ms'] for e in evaluations if e['feasible_offset_interval_kind']=='bounded']
    intersection = [max(x[0] for x in bounded),min(x[1] for x in bounded)] if bounded else None
    if policy == 'shared' and intersection and intersection[0] > intersection[1]:
        blocked = True; reasons.append('Known offset intervals are disjoint')
    status = 'infeasible' if blocked else 'unknown' if unknown else 'feasible'
    cost = c.get('migration_cost_points')
    cost = None if cost is None else cost + POLICY_COST[policy]
    if cost is None: reasons.append('Migration cost unknown: unranked, not zero')
    if camera['representative'] is None: reasons.append('No unconflicted scalar spec identity (U01 if conflicting)')
    return {'camera_id':camera_id,'policy':policy,'status':status,'reason':'; '.join(reasons) or 'All required facts and constraints established',
        'cost_points':cost,'cost_comparison_status':'unknown' if cost is None else 'known',
        'selection_identity_eligible':camera['representative'] is not None,
        'availability':available,
        'shared_interval_ms':intersection if policy=='shared' and (not intersection or intersection[0]<=intersection[1]) else None,
        'source_ids':camera['source_ids']}


def select_plan(case, resolved, policies, evaluations):
    choices = [p for p in policies if p['status']=='feasible' and p['cost_points'] is not None and p['selection_identity_eligible']]
    if not case.get('base_firmware_revision'):
        return None
    if not choices:
        return None
    chosen = min(choices,key=lambda p:(p['cost_points'],p['camera_id'],p['policy'],entity(resolved,'camera',p['camera_id'])['representative']))
    camera = entity(resolved,'camera',chosen['camera_id'])
    offsets = {}
    if chosen['policy']=='shared':
        domain = chosen['shared_interval_ms']
        offset = Fraction(domain[0]+domain[1],2) if domain else 0
        offsets = {v:offset for v in case['variant_ids']}
    else:
        for e in evaluations:
            if e['camera_id']==chosen['camera_id']:
                offsets[e['variant_id']] = 0 if e['feasible_offset_interval_kind']=='unbounded' else -camera['data']['timestamp_bias_ms_by_variant'][e['variant_id']]
    unresolved = []
    for camera_id in case['candidate_camera_ids']:
        possible = [p for p in policies if p['camera_id']==camera_id and p['status']!='infeasible' and
                    (p['status']=='unknown' or not p['selection_identity_eligible'] or p['cost_points'] is None)]
        if not possible: continue
        known = [p['cost_points'] for p in possible if p['cost_points'] is not None]
        potential = min(known) if known else None
        if potential is None or potential < chosen['cost_points']:
            unresolved.append({'camera_id':camera_id,'potential_cost_points':potential,
                'reason':'Possibly cheaper/incomparable; ' + '; '.join(sorted(set(p['reason'] for p in possible)))})
    base = case['base_firmware_revision']
    return {'camera_id':chosen['camera_id'],'spec_source_id':camera['representative'],'policy':chosen['policy'],
        'offset_ms_by_variant':offsets,'firmware_revision':base if chosen['policy']=='shared' else base+'-PROPOSED-per_variant',
        'cost_points':chosen['cost_points'],'optimality':'minimum_among_established_feasible_plans',
        'unresolved_cheaper_candidates':unresolved,'requires_human_approval':True,'deployment_qualified':False}


def evidence_review(case, records, resolved, plan):
    results, limitations = [], []
    for sid, rec in sorted(records.items()):
        if rec['kind']!='test_record': continue
        d=rec['data']; cfg=d.get('configuration') or {}; variant_id=cfg.get('variant_id')
        variant=entity(resolved,'variant',variant_id)
        flags, reasons, comparisons = [], [], []
        if plan is None:
            flags.append('no_selected_configuration'); reasons.append('No selected configuration exists')
        else:
            selected = dict(plan)
            selected.update(variant_id=variant_id if variant_id in case['variant_ids'] else None,
                            offset_ms=plan['offset_ms_by_variant'].get(variant_id))
            for field in sorted(set(APP_FIELDS) | set(cfg)):
                recorded, proposed=cfg.get(field), selected.get(field)
                state='missing' if recorded is None or proposed is None else ('equal' if equal(recorded,proposed) else 'different')
                if field=='variant_id' and recorded is not None and recorded not in case['variant_ids']: state='different'
                comparisons.append({'field':field,'recorded':recorded,'selected':proposed,'state':state})
            if any(x['state']=='different' for x in comparisons): flags.append('stale_configuration')
            if any(x['state']=='missing' for x in comparisons): flags.append('insufficient_applicability_data')
            if all(x['state']=='equal' for x in comparisons): flags.append('applicable_to_selected_configuration')
            reasons.extend(x['field'] + ': ' + x['state'] for x in comparisons if x['state']!='equal')
        observations=d.get('observations') or []; recorded_limit=d.get('recorded_limit')
        if d.get('claimed_result')=='PASS' and recorded_limit is not None and any(o is not None and o>recorded_limit for o in observations):
            flags.append('internally_contradictory'); reasons.append('Recorded PASS has observations above its own recorded limit')
        field=LIMIT_FIELDS.get(d.get('metric')); current_limit=variant['data'].get(field) if field else None
        if current_limit is not None and recorded_limit is not None and not equal(current_limit,recorded_limit):
            flags.append('requirement_limit_mismatch')
            reasons.append('Recorded upper limit is ' + ('looser' if recorded_limit>current_limit else 'tighter') + ' than current '+field)
        if field is None:
            limitations.append(sid+': unsupported saved metric '+str(d.get('metric'))+'; current-limit direction/units not inferred. FPS, voltage and transport remain physical constraints.')
        elif current_limit is None or recorded_limit is None:
            reasons.append('Current/recorded requirement limit unavailable; no compliance conclusion')
        if observations or d.get('claims_to_establish_guaranteed_jitter_bound') is True:
            flags.append('finite_sample_not_guaranteed_bound'); reasons.append('Finite observations cannot establish a guaranteed jitter bound')
        results.append({'source_id':sid,'flags':sorted(set(flags)),'reason':'; '.join(reasons) or 'Listed applicability fields match; observation only',
            'source_ids':sorted(set([sid]+variant['source_ids'])), 'applicability_comparisons':comparisons,
            'metric':d.get('metric'),'recorded_limit':recorded_limit,'current_limit':current_limit,
            'current_requirement_locators':locators(variant,[field]) if field else []})
    return results, limitations


def impact_chains(case, records, resolved, evaluations, evidence):
    chains=[]
    for (kind,subject), ent in sorted(resolved.items()):
        if kind=='dependency_graph':
            for edge in ent['data'].get('edges') or []:
                if not isinstance(edge,dict) or not edge.get('from') or not edge.get('to'): continue
                chains.append({'nodes':[edge['from'],edge['to']], 'edges':[dict(edge,basis='declared',source_ids=ent['source_ids'])],
                    'consequence':'Declared relationship; potential dependency, not by itself a calculated violation'})
    for ev in evaluations:
        cam=entity(resolved,'camera',ev['camera_id']); var=entity(resolved,'variant',ev['variant_id'])
        for row in ev['constraints']:
            param=ev['camera_id']+'/'+row['constraint']
            requirement=ev['variant_id']+'/'+row['constraint']
            nodes=[ev['camera_id'],param,requirement]
            edges=[{'from':nodes[0],'to':param,'basis':'derived','source_ids':cam['source_ids'],
                    'locators':[l for l in row['locators'] if l['source_id'] in cam['source_ids']], 'support':'Camera data fields in the public '+row['constraint']+' constraint'},
                   {'from':param,'to':requirement,'basis':'derived','source_ids':row['source_ids'],'locators':row['locators'],
                    'support':row['comparison']}]
            linked=[e['source_id'] for e in evidence if (records[e['source_id']]['data'].get('configuration') or {}).get('variant_id')==ev['variant_id'] and
                    LIMIT_FIELDS.get(records[e['source_id']]['data'].get('metric')) in [l['locator'].split('/')[-1] for l in row['locators']]]
            for test in linked:
                nodes.append(test); edges.append({'from':requirement,'to':test,'basis':'derived','source_ids':sorted(set(var['source_ids']+[test])),
                    'support':'Recorded metric/configuration tied to this variant requirement; applicability audited separately',
                    'locators':[{'source_id':test,'locator':'/data/configuration'}]})
            chains.append({'nodes':nodes,'edges':edges,'consequence':row['status']+': '+row['constraint']+' for candidate '+ev['camera_id']+' / '+ev['variant_id']+
                '; potential change impact; only fail means calculated violation'})
    return chains


def analyze(case, records, resolved, reviews, invalid_links):
    evaluations=[]
    for camera_id in case['candidate_camera_ids']:
        for variant_id in case['variant_ids']:
            evaluations.append(evaluate(camera_id,variant_id,entity(resolved,'camera',camera_id),entity(resolved,'variant',variant_id)))
    baselines={e['data'].get('camera_id') for (kind,subject),e in resolved.items() if kind=='configuration'}
    policies=[policy_evaluation(c,p,entity(resolved,'camera',c),[e for e in evaluations if e['camera_id']==c],baselines)
              for c in case['candidate_camera_ids'] for p in POLICY_COST]
    plan=select_plan(case,resolved,policies,evaluations)
    # Evidence identity is the actual numeric JSON configuration that will be emitted.
    if plan is not None:
        plan=loads(dumps(plan))
    status='feasible_plan' if plan else ('no_feasible_plan' if all(p['status']=='infeasible' for p in policies) else 'insufficient_evidence')
    evidence,limitations=evidence_review(case,records,resolved,plan)
    limitations += ['Synthetic prediction only. Proposals are unapproved and not hardware-validated.', U01,
        'Unknown cost is unranked; optimality covers only established feasible, cost-comparable, identity-eligible plans.',
        'Zero speed requires known guarantees; an unbounded timing domain serializes as null plus kind=unbounded.']
    if not case.get('base_firmware_revision'): limitations.append('Missing base firmware identity prevents generation of a justified plan.')
    findings=[]
    for review in reviews:
        sid=review['source_id']
        if review['disposition']=='conflicted':
            for field in review['conflict_fields']:
                findings.append({'category':'conflict','statement':review['reason'],'source_ids':review['source_ids'], 'locator':records[sid]['_path']+'#'+existing_pointer(records[sid],field)})
        elif records[sid].get('subject_id') is None:
            findings.append({'category':'missing_evidence','statement':'Source has no subject_id; no association invented','source_ids':[sid],'locator':records[sid]['_path']})
    for ev in evaluations:
        for row in ev['constraints']:
            if row['status']!='pass':
                loc=row['locators'][0] if row['locators'] else None
                findings.append({'category':'impact' if row['status']=='fail' else 'missing_evidence',
                    'statement':ev['camera_id']+' / '+ev['variant_id']+' '+row['constraint']+': '+row['status']+'; '+', '.join(row['missing_fields']),
                    'source_ids':row['source_ids'],'locator':records[loc['source_id']]['_path']+'#'+loc['locator'] if loc else 'case.json#/candidate_camera_ids'})
    for ev in evidence:
        if 'stale_configuration' in ev['flags'] or 'internally_contradictory' in ev['flags']:
            findings.append({'category':'stale_evidence','statement':ev['source_id']+': '+ev['reason'],'source_ids':ev['source_ids'],
                'locator':records[ev['source_id']]['_path']+'#/data'})
    for sid,pred in invalid_links:
        findings.append({'category':'conflict','statement':'Unresolved or cross-subject supersession link '+str(pred)+' ignored; no retirement authority',
            'source_ids':[sid]+([pred] if pred in records else []),'locator':records[sid]['_path']+'#/supersedes'})
    approval=[s for s,r in records.items() if r['kind']=='decision']
    findings.append({'category':'approval_boundary','statement':'Prediction and generated software checks do not grant deployment approval; retain pre-change evidence and obtain human approval after revalidation.',
        'source_ids':approval,'locator':records[approval[0]]['_path']+'#/data' if approval else 'case.json#/case_id'})
    selection_requests=[]
    for cid in case['candidate_camera_ids']:
        ent=entity(resolved,'camera',cid)
        missing=[f for f in ['available','migration_cost_points'] if ent['data'].get(f) is None]
        if ent['representative'] is None:
            missing.append('active unconflicted scalar spec identity; resolve source association/conflicts (U01)')
        if missing:
            selection_requests.append({'camera_id':cid,'missing':missing,'source_ids':ent['source_ids']})
    if not case.get('base_firmware_revision'):
        selection_requests.append({'missing':['base_firmware_revision'],'source_ids':[]})
    retests=[]
    for variant in case['variant_ids']:
        retests.append({'variant_id':variant,'configuration':dict(plan,variant_id=variant,offset_ms=plan['offset_ms_by_variant'][variant]) if plan else None,
            'checks':['timing','resolution','throughput','power','voltage','transport','timestamp_adapter'],
            'status':'required_not_run_on_hardware', 'retain_obsolete_evidence':[e['source_id'] for e in evidence],
            'action':'Validate exact proposed configuration and obtain human approval' if plan else 'Resolve the listed missing facts/blockers before selecting any configuration; no executable proposal'})
    return {'schema_version':'1.0','case_id':case['case_id'],'status':status,'source_review':reviews,'evaluations':evaluations,
        'policy_evaluations':policies,'selected_plan':plan,'evidence_review':evidence,
        'impact_chains':impact_chains(case,records,resolved,evaluations,evidence),'findings':findings,'required_retests':retests,
        'limitations':limitations,'selection_evidence_requests':selection_requests,'current_configurations':[{'source_ids':e['source_ids'],'data':e['data']} for (k,s),e in resolved.items() if k=='configuration'],
        'evidence_requests':[{'camera_id':e['camera_id'],'variant_id':e['variant_id'],'missing':e['unknowns'],'established_blockers':e['blockers']} for e in evaluations if e['unknowns'] or e['blockers']]}
