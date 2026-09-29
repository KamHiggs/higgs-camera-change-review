"""Behavioral and adversarial tests. Fixtures/oracles are development-only."""
import copy
import hashlib
import importlib.util
import json
import math
import os
import subprocess
import sys
import time
import unittest
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import sources
from run_cases import CASES, ROOT, adapter_checks, hashes
sys.dont_write_bytecode=True
STAMP=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
WORK=ROOT/'test_runs'/STAMP
WORK.mkdir(parents=True)
COMMANDS=[]


def read_fixture(path):
    case=json.loads((path/'case.json').read_text())
    records={e['source_id']:json.loads((path/e['path']).read_text()) for e in case['source_inventory']}
    return case,records


def write_fixture(path,case,records):
    path.mkdir(parents=True)
    for ent in case['source_inventory']:
        target=path/ent['path'];target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(records[ent['source_id']],indent=2)+'\n')
    (path/'case.json').write_text(json.dumps(case,indent=2)+'\n')


def own_fixture():
    variants=['idle','inspect','rapid']; candidates=['steady','sample_only','premium']
    case={'schema_version':'1.0','case_id':'OWN-THREE-SPEED-BOUNDARY','variant_ids':variants,
        'candidate_camera_ids':candidates,'base_firmware_revision':'own-base','source_inventory':[]}
    records={}
    def add(sid,kind,subject,data,status='active',supersedes=None):
        case['source_inventory'].append({'source_id':sid,'path':'facts/'+sid+'.json'})
        records[sid]={'source_id':sid,'kind':kind,'subject_id':subject,'status':status,'revision':1,'supersedes':supersedes or [],'data':data}
    for v,speed,fps in zip(variants,[0,1,2],[5,10,20]):
        add('req-'+v,'variant',v,{'field_of_view_mm':10,'supply_voltage_V':12,'transport':'LocalBus','host_jitter_bound_ms':0.1,
            'required_fps':fps,'max_mm_per_pixel':0.1,'link_capacity_MB_s':0.02,'power_budget_W':4,'speed_m_s':speed,'max_registration_error_mm':0.4})
    for c,cost,jitter in [('steady',4,0.1),('sample_only',1,None),('premium',6,0.1)]:
        add('spec-'+c,'camera',c,{'available':True,'image_width_px':100,'image_height_px':10,'bytes_per_pixel':1,'max_fps':20,
            'power_W':4,'supply_range_V':[12,24],'transport':'LocalBus','timestamp_bias_ms_by_variant':{'idle':9,'inspect':0.1,'rapid':0.1},
            'timestamp_jitter_bound_ms':jitter,'migration_cost_points':cost,'typical_timestamp_jitter_ms':0.01})
    add('original-configuration','configuration','family',{'camera_id':'retired','spec_source_id':'retired-spec','firmware_revision':'own-base','policy':'shared','offset_ms_by_variant':dict.fromkeys(variants,0)})
    add('old-power','test_record','old-power',{'metric':'power_W','configuration':{'variant_id':'rapid','camera_id':'steady','spec_source_id':'spec-steady','firmware_revision':'own-base','policy':'shared','offset_ms':-0.1},'observations':[4.5],'recorded_limit':5,'claimed_result':'PASS','claims_to_establish_guaranteed_jitter_bound':False})
    return case,records


class AppTests(unittest.TestCase):
    def setUp(self):
        self.dir=WORK/self._testMethodName;self.dir.mkdir();self.count=0

    def fixture(self,base='public',edit=None,own=False):
        c,r=own_fixture() if own else read_fixture(CASES[base])
        if edit:edit(c,r)
        path=self.dir/('case-'+str(self.count));self.count+=1
        write_fixture(path,c,r);return path

    def invoke(self,case,out=None,ok=True,check=True):
        out=out or self.dir/('out-'+str(self.count));self.count+=1
        before=hashes(case) if (case/'case.json').is_file() else None
        cmd=[sys.executable,str(ROOT/'app.py'),'analyze','--case',str(case),'--out',str(out)]
        start=time.perf_counter();cp=subprocess.run(cmd,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        event={'test':self._testMethodName,'command':cmd,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'duration_seconds':time.perf_counter()-start,'input_hashes_before':before,
               'input_hashes_after':hashes(case) if before is not None else None}
        COMMANDS.append(event)
        self.assertEqual(event['input_hashes_before'],event['input_hashes_after'])
        if not ok:
            self.assertNotEqual(cp.returncode,0,cp.stdout);self.assertIn('error',cp.stderr.lower());return cp
        self.assertEqual(cp.returncode,0,cp.stderr)
        report=json.loads((out/'report.json').read_text(),parse_constant=lambda s:(_ for _ in ()).throw(AssertionError(s)))
        if check:self.contract(report,case,out,event)
        return report

    def contract(self,r,case,out,event):
        c,records=read_fixture(case)
        required={'schema_version','case_id','status','source_review','evaluations','policy_evaluations','selected_plan','evidence_review','impact_chains','findings','required_retests','limitations'}
        self.assertTrue(required<=set(r));self.assertEqual(r['case_id'],c['case_id'])
        self.assertEqual({(x['camera_id'],x['variant_id']) for x in r['evaluations']},{(a,b) for a in c['candidate_camera_ids'] for b in c['variant_ids']})
        self.assertEqual(len(r['evaluations']),len(c['candidate_camera_ids'])*len(c['variant_ids']))
        self.assertEqual({(x['camera_id'],x['policy']) for x in r['policy_evaluations']},{(a,b) for a in c['candidate_camera_ids'] for b in ['shared','per_variant']})
        self.assertTrue((out/'engineering_review.html').is_file());self.assertTrue((out/'revalidation_plan.md').is_file())
        self.assertEqual({x['variant_id'] for x in r['required_retests']},set(c['variant_ids']))
        for item in r['required_retests']:self.assertEqual(set(item['checks']),{'timing','resolution','throughput','power','voltage','transport','timestamp_adapter'})
        valid_flags={'applicable_to_selected_configuration','stale_configuration','insufficient_applicability_data','internally_contradictory','requirement_limit_mismatch','finite_sample_not_guaranteed_bound','no_selected_configuration'}
        for e in r['evidence_review']:self.assertTrue(set(e['flags'])<=valid_flags)
        def citations(v):
            if isinstance(v,dict):
                if 'source_ids' in v:self.assertTrue(set(v['source_ids'])<=set(records),v)
                if 'source_id' in v:self.assertIn(v['source_id'],records)
                for x in v.values():citations(x)
            elif isinstance(v,list):
                for x in v:citations(x)
        citations(r)
        plan=r['selected_plan']
        if plan:
            self.assertTrue(plan['requires_human_approval']);self.assertFalse(plan['deployment_qualified'])
            self.assertEqual(plan['optimality'],'minimum_among_established_feasible_plans')
            self.assertEqual(json.loads((out/'proposed_configuration.json').read_text()),plan)
            event['adapter_checks']=adapter_checks(out)
            self.assertEqual(set(plan['offset_ms_by_variant']),set(c['variant_ids']))
            spec=records[plan['spec_source_id']]['data']
            # Independent numeric re-evaluation using the emitted JSON plan and actual input fields.
            for vid,offset in plan['offset_ms_by_variant'].items():
                variants=[x for x in records.values() if x['kind']=='variant' and x.get('subject_id')==vid and x['status']=='active']
                # These tests only select plans with identical variant data or a single active variant.
                v=variants[0]['data']
                self.assertGreaterEqual(spec['max_fps'],v['required_fps'])
                self.assertLessEqual(v['field_of_view_mm']/spec['image_width_px'],v['max_mm_per_pixel']+1e-9)
                self.assertLessEqual(spec['image_width_px']*spec['image_height_px']*spec['bytes_per_pixel']*v['required_fps']/1000000,v['link_capacity_MB_s']+1e-9)
                self.assertLessEqual(spec['power_W'],v['power_budget_W'])
                self.assertLessEqual(spec['supply_range_V'][0],v['supply_voltage_V']);self.assertGreaterEqual(spec['supply_range_V'][1],v['supply_voltage_V'])
                self.assertEqual(spec['transport'],v['transport'])
                error=v['speed_m_s']*(abs(spec['timestamp_bias_ms_by_variant'][vid]+offset)+spec['timestamp_jitter_bound_ms']+v['host_jitter_bound_ms'])
                self.assertLessEqual(error,v['max_registration_error_mm']+1e-9)
            self.assertEqual(plan['cost_points'],spec['migration_cost_points']+(3 if plan['policy']=='per_variant' else 0))
            if plan['policy']=='shared':
                self.assertEqual(len(set(plan['offset_ms_by_variant'].values())),1);self.assertEqual(plan['firmware_revision'],c['base_firmware_revision'])
            else:self.assertNotEqual(plan['firmware_revision'],c['base_firmware_revision'])
        else:
            self.assertFalse((out/'proposed_firmware.py').exists());self.assertFalse((out/'proposed_configuration.json').exists())

    def ev(self,r,c='CAM-B',v='V-FAST'):
        return next(x for x in r['evaluations'] if x['camera_id']==c and x['variant_id']==v)

    def pol(self,r,c='CAM-B',p='shared'):
        return next(x for x in r['policy_evaluations'] if x['camera_id']==c and x['policy']==p)

    def test_T01_T02_T22_T26_T27_T32_public_and_shared(self):
        r=self.invoke(CASES['public']);p=r['selected_plan']
        self.assertEqual((p['camera_id'],p['policy'],p['cost_points']),('CAM-B','per_variant',5))
        self.assertEqual(self.ev(r)['status'],'feasible');self.assertEqual(self.pol(r)['status'],'infeasible')
        self.assertEqual(self.ev(r,'CAM-C')['status'],'infeasible')
        self.assertEqual(len(self.ev(r,'CAM-C')['blockers']),2)
        self.assertEqual(self.ev(r,'CAM-D')['status'],'unknown')
        self.assertEqual([x['camera_id'] for x in p['unresolved_cheaper_candidates']],['CAM-D'])
        e=next(x for x in r['evidence_review'] if x['source_id']=='TEST-B-FAST')
        self.assertTrue({'stale_configuration','internally_contradictory'}<=set(e['flags']))
        r=self.invoke(CASES['devised_shared']);p=r['selected_plan']
        self.assertEqual((p['camera_id'],p['policy'],p['cost_points']),('CAM-ECONOMY','shared',4))
        self.assertEqual(len(r['evaluations']),6);self.assertTrue(all(e['status']=='feasible' for e in r['evaluations']))
        self.assertTrue(all(p['status']=='feasible' for p in r['policy_evaluations']))
        self.assertTrue(all(-1.2<=o<=-0.8 for o in r['selected_plan']['offset_ms_by_variant'].values()))

    def test_T03_retirement_not_revision(self):
        def edit(c,r):
            r['CAM-B-R1']['status']='active';r['CAM-B-R1']['revision']=9999
            old=copy.deepcopy(r['CAM-B-R1']);old.update(source_id='historical-large',status='historical',revision=99999)
            r[old['source_id']]=old;c['source_inventory'].append({'source_id':old['source_id'],'path':'history.json'})
        r=self.invoke(self.fixture(edit=edit))
        self.assertEqual(r['selected_plan']['spec_source_id'],'CAM-B-R2')
        self.assertEqual(next(x for x in r['source_review'] if x['source_id']=='CAM-B-R1')['disposition'],'superseded')

    def duplicate(self,c,r,change=None,sid='AAA-AGREE'):
        rec=copy.deepcopy(r['CAM-B-R2']);rec.update(source_id=sid,revision=999,supersedes=[])
        if change:change(rec['data'])
        r[sid]=rec;c['source_inventory'].append({'source_id':sid,'path':sid+'.json'})

    def test_T04_T21_agreeing_identity(self):
        r=self.invoke(self.fixture(edit=lambda c,r:self.duplicate(c,r)))
        self.assertEqual(r['selected_plan']['spec_source_id'],'AAA-AGREE')
        self.assertTrue({'AAA-AGREE','CAM-B-R2'}<=set(self.ev(r)['source_ids']))
        reviews={x['source_id']:x for x in r['source_review']}
        self.assertEqual(reviews['AAA-AGREE']['disposition'],'active')
        self.assertEqual(reviews['CONFIG-BASE']['disposition'],'active');self.assertEqual(reviews['GRAPH-BASE']['disposition'],'active')
        evidence=next(e for e in r['evidence_review'] if e['source_id']=='TEST-B-FAST')
        self.assertIn('stale_configuration',evidence['flags'])
        self.assertEqual(next(x for x in evidence['applicability_comparisons'] if x['field']=='spec_source_id')['state'],'different')

    def test_T04_T05_conflict_one_leaf(self):
        r=self.invoke(self.fixture(edit=lambda c,r:self.duplicate(c,r,lambda d:d['timestamp_bias_ms_by_variant'].update({'V-FAST':100}))))
        self.assertEqual(self.ev(r)['status'],'unknown');self.assertEqual(self.ev(r,v='V-SLOW')['status'],'feasible')
        self.assertTrue({'AAA-AGREE','CAM-B-R2'}<=set(self.ev(r)['source_ids']))
        r=self.invoke(CASES['descriptive_conflict']);self.assertEqual(r['status'],'insufficient_evidence')
        self.assertTrue(all(e['status']=='feasible' for e in r['evaluations'] if e['camera_id']=='CAM-B'))
        self.assertTrue(any('U01' in x for x in r['limitations']))

    def test_T05_T06_known_blockers_with_missing_guarantee(self):
        def edit(c,r):r['CAM-C-R1']['data']['timestamp_jitter_bound_ms']=None
        r=self.invoke(self.fixture(edit=edit));e=self.ev(r,'CAM-C')
        self.assertEqual(e['status'],'infeasible');self.assertEqual(len(e['blockers']),2);self.assertTrue(e['unknowns'])
        self.assertEqual(self.ev(r,'CAM-D')['status'],'unknown')
        self.assertIsNone(self.ev(r,'CAM-D')['feasible_offset_interval_ms'])

    def test_T07_seven_boundaries_and_nearby_failures(self):
        c,r=own_fixture()
        for key,value,expected in [('max_fps',19.99999999999,'frame_rate'),('image_width_px',99.99999999999,'resolution'),
                                    ('image_height_px',10.00000001,'throughput'),('power_W',4.00000000001,'power'),
                                    ('supply_range_V',[12.00000000001,24],'voltage'),('transport','WrongBus','transport'),
                                    ('timestamp_jitter_bound_ms',0.10000000001,'timing')]:
            with self.subTest(constraint=expected):
                fixture=self.fixture(own=True,edit=lambda c,r,k=key,val=value:r['spec-steady']['data'].update({k:val}))
                result=self.invoke(fixture);ev=self.ev(result,'steady','rapid')
                self.assertEqual(ev['status'],'infeasible');self.assertIn(expected+': established failure',ev['blockers'])
        result=self.invoke(self.fixture(own=True));self.assertEqual(self.ev(result,'steady','rapid')['status'],'feasible')
        self.assertEqual(self.ev(result,'steady','rapid')['feasible_offset_interval_ms'],[-0.1,-0.1])

    def test_T08_irreducible_failure_missing_bias(self):
        def edit(c,r):
            r['REQ-FAST']['data']['max_registration_error_mm']=0.3
            r['CAM-B-R2']['data']['timestamp_bias_ms_by_variant'].pop('V-FAST')
        r=self.invoke(self.fixture(edit=edit));e=self.ev(r)
        self.assertEqual(e['status'],'infeasible');self.assertEqual(e['feasible_offset_interval_kind'],'empty')
        self.assertIn('timing: established failure',e['blockers']);self.assertTrue(e['unknowns'])

    def test_T09_zero_radius(self):
        r=self.invoke(CASES['zero_radius']);e=self.ev(r)
        self.assertEqual(e['feasible_offset_interval_ms'],[-2.5,-2.5]);self.assertEqual(e['status'],'feasible')
        self.assertEqual(r['selected_plan']['cost_points'],5)

    def test_T09_sign(self):
        def edit(c,r):
            c['candidate_camera_ids']=['steady']
            for sid in ['req-inspect','req-rapid']:
                r[sid]['data'].update(speed_m_s=1,max_registration_error_mm=0.5)
            r['spec-steady']['data']['timestamp_bias_ms_by_variant'].update(inspect=2,rapid=2)
        r=self.invoke(self.fixture(own=True,edit=edit));e=self.ev(r,'steady','rapid')
        self.assertEqual(e['feasible_offset_interval_ms'],[-2.3,-1.7])
        self.assertEqual(r['selected_plan']['offset_ms_by_variant']['rapid'],-2)
        self.assertAlmostEqual(1*(abs(2+2)+0.1+0.1),4.2)

    def test_T10_T11_intersections_and_partial_contradiction(self):
        def edit(c,r):
            c['candidate_camera_ids']=['steady']
            r['req-inspect']['data'].update(speed_m_s=1,max_registration_error_mm=0.7)
            r['req-rapid']['data'].update(speed_m_s=1,max_registration_error_mm=0.7)
            r['spec-steady']['data']['timestamp_bias_ms_by_variant'].update(inspect=1.5,rapid=0.5)
        fixture=self.fixture(own=True,edit=edit);r=self.invoke(fixture)
        self.assertEqual(self.pol(r,'steady')['shared_interval_ms'],[-1,-1])
        self.assertEqual(r['selected_plan']['offset_ms_by_variant']['idle'],-1)
        def disjoint(c,r):
            edit(c,r);r['spec-steady']['data']['timestamp_bias_ms_by_variant']['rapid']=-1.5
            r['spec-steady']['data']['timestamp_bias_ms_by_variant'].pop('idle')
        r=self.invoke(self.fixture(own=True,edit=disjoint))
        self.assertEqual(self.pol(r,'steady')['status'],'infeasible');self.assertEqual(self.pol(r,'steady','per_variant')['status'],'unknown')
        self.assertEqual(r['status'],'insufficient_evidence')

    def test_T12_availability_states(self):
        for value in [True,False,None,'absent','conflict']:
            with self.subTest(value=value):
                def edit(c,r):
                    c['candidate_camera_ids']=['CAM-B']
                    if value=='absent':r['CAM-B-R2']['data'].pop('available')
                    elif value=='conflict':self.duplicate(c,r,lambda d:d.update(available=False))
                    else:r['CAM-B-R2']['data']['available']=value
                r=self.invoke(self.fixture(edit=edit))
                self.assertEqual(self.ev(r)['status'],'feasible')
                self.assertEqual(r['status'],'feasible_plan' if value is True else 'no_feasible_plan' if value is False else 'insufficient_evidence')

    def test_T12_T13_unknown_cost_and_equal_ties(self):
        def edit(c,r):
            r['CAM-B-R2']['data']['migration_cost_points']=None;r['CAM-D-R1']['data']['timestamp_jitter_bound_ms']=0.1
        r=self.invoke(self.fixture(edit=edit));p=r['selected_plan']
        self.assertEqual(p['camera_id'],'CAM-D');self.assertIsNone(next(x for x in p['unresolved_cheaper_candidates'] if x['camera_id']=='CAM-B')['potential_cost_points'])
        r=self.invoke(CASES['bias_equalized']);self.assertEqual(r['selected_plan']['unresolved_cheaper_candidates'],[])
        r=self.invoke(self.fixture(own=True,edit=lambda c,r:r['spec-premium']['data'].update(migration_cost_points=4)))
        self.assertEqual(r['selected_plan']['cost_points'],4);self.assertIn(r['selected_plan']['camera_id'],['steady','premium'])

    def test_T14_T19_two_refusals(self):
        for name,status in [('all_blocked','no_feasible_plan'),('insufficient','insufficient_evidence')]:
            r=self.invoke(CASES[name]);self.assertEqual(r['status'],status)
            self.assertTrue(all('no_selected_configuration' in e['flags'] for e in r['evidence_review']))
            self.assertIn('internally_contradictory',next(e for e in r['evidence_review'] if e['source_id']=='TEST-B-FAST')['flags'])
        r=self.invoke(self.fixture(edit=lambda c,r:r['CAM-B-R2'].update(status='superseded')))
        self.assertEqual(self.ev(r)['status'],'unknown');self.assertEqual(r['status'],'insufficient_evidence')
        def absent(c,r):
            c['candidate_camera_ids'].append('declared-no-spec')
        r=self.invoke(self.fixture(edit=absent));self.assertEqual(self.ev(r,'declared-no-spec')['status'],'unknown')
        self.assertEqual(self.ev(r,'declared-no-spec')['source_ids'],['REQ-FAST'])

    def test_T15_T16_independent_applicability(self):
        def edit(c,r):
            d=r['TEST-B-FAST']['data'];d['configuration'].pop('offset_ms')
        r=self.invoke(self.fixture(edit=edit));e=next(e for e in r['evidence_review'] if e['source_id']=='TEST-B-FAST')
        self.assertTrue({'stale_configuration','insufficient_applicability_data','internally_contradictory'}<=set(e['flags']))
        self.assertNotIn('applicable_to_selected_configuration',e['flags'])
        def exact(c,r):
            d=r['TEST-B-FAST']['data'];d['configuration'].update(firmware_revision='FW-1.0-PROPOSED-per_variant',policy='per_variant',offset_ms=-2.5)
        r=self.invoke(self.fixture(edit=exact));e=next(e for e in r['evidence_review'] if e['source_id']=='TEST-B-FAST')
        self.assertIn('applicable_to_selected_configuration',e['flags']);self.assertIn('internally_contradictory',e['flags'])
        def extra(c,r):exact(c,r);r['TEST-B-FAST']['data']['configuration']['extra_identity']='unknown'
        r=self.invoke(self.fixture(edit=extra));e=next(e for e in r['evidence_review'] if e['source_id']=='TEST-B-FAST')
        self.assertIn('insufficient_applicability_data',e['flags'])

    def test_T17_T18_limit_metrics_and_sample(self):
        r=self.invoke(self.fixture(own=True));e=next(e for e in r['evidence_review'] if e['source_id']=='old-power')
        self.assertIn('requirement_limit_mismatch',e['flags']);self.assertNotIn('internally_contradictory',e['flags']);self.assertIn('looser',e['reason'])
        for metric in ['registration_error_mm','power_W','mm_per_pixel','bandwidth_MB_s','fps','voltage','transport','unrecognized']:
            with self.subTest(metric=metric):
                def edit(c,r):r['old-power']['data'].update(metric=metric,recorded_limit=0.001,observations=[0.0005])
                r=self.invoke(self.fixture(own=True,edit=edit));e=next(e for e in r['evidence_review'] if e['source_id']=='old-power')
                if metric in ['registration_error_mm','power_W','mm_per_pixel','bandwidth_MB_s']:
                    self.assertIn('requirement_limit_mismatch',e['flags']);self.assertIn('tighter',e['reason'])
                else:self.assertTrue(any('unsupported saved metric '+metric in x for x in r['limitations']))
        r=self.invoke(CASES['jitter_known']);e=next(e for e in r['evidence_review'] if e['source_id']=='TEST-D-SAMPLE')
        self.assertIn('applicable_to_selected_configuration',e['flags']);self.assertIn('finite_sample_not_guaranteed_bound',e['flags'])

    def test_T20_T28_citations_and_directed_graph(self):
        case=self.fixture();r=self.invoke(case);c,records=read_fixture(case)
        declared={(edge['from'],edge['to']) for rec in records.values() if rec['kind']=='dependency_graph' for edge in rec['data']['edges']}
        observed=set()
        for chain in r['impact_chains']:
            for edge in chain['edges']:
                if edge['basis']=='declared':
                    self.assertIn((edge['from'],edge['to']),declared);observed.add((edge['from'],edge['to']))
                else:self.assertTrue(edge['support'])
                for loc in edge.get('locators',[]):
                    value=records[loc['source_id']]
                    for key in loc['locator'].split('/')[1:]:value=value[int(key)] if isinstance(value,list) else value[key]
        self.assertEqual(observed,declared)
        self.assertTrue(any(len(chain['nodes'])>=4 for chain in r['impact_chains']))

    def test_T23_rename_reorder(self):
        c,r=read_fixture(CASES['public'])
        ids=set(r)|set(c['variant_ids'])|set(c['candidate_camera_ids'])|{x.get('subject_id') for x in r.values()}
        mapping={x:'renamed-'+str(i) for i,x in enumerate(sorted(x for x in ids if x is not None))}
        def rename(x):
            if isinstance(x,dict):return {mapping.get(k,k):rename(v) for k,v in x.items()}
            if isinstance(x,list):return [rename(v) for v in x]
            if isinstance(x,str):return mapping.get(x,x)
            return x
        c=rename(c);r={mapping[k]:rename(v) for k,v in r.items()}
        c['source_inventory'].reverse()
        for i,ent in enumerate(c['source_inventory']):ent['path']='arbitrary/z'+str(i)+'.json'
        path=self.dir/'renamed';write_fixture(path,c,r);result=self.invoke(path)
        self.assertEqual(result['selected_plan']['camera_id'],mapping['CAM-B']);self.assertEqual(result['selected_plan']['policy'],'per_variant')
        self.assertEqual(result['selected_plan']['cost_points'],5)
        for old,expected in [('CAM-B','feasible'),('CAM-C','infeasible'),('CAM-D','unknown')]:self.assertEqual(self.ev(result,mapping[old],mapping['V-FAST'])['status'],expected)

    def test_T24_T34_own_case_adapter_decimal(self):
        r=self.invoke(self.fixture(own=True));p=r['selected_plan']
        self.assertEqual((p['camera_id'],p['policy'],p['cost_points']),('steady','shared',4))
        self.assertEqual(p['offset_ms_by_variant'],dict.fromkeys(['idle','inspect','rapid'],-0.1))
        self.assertEqual(self.ev(r,'steady','idle')['feasible_offset_interval_kind'],'unbounded')
        self.assertEqual([x['camera_id'] for x in p['unresolved_cheaper_candidates']],['sample_only'])
        # Execute the actual emitted adapter at a nonbinary decimal timestamp too.
        out=Path(COMMANDS[-1]['command'][-1]);spec=importlib.util.spec_from_file_location('decimal_adapter',out/'proposed_firmware.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        plan=json.loads((out/'proposed_configuration.json').read_text())
        self.assertAlmostEqual(mod.normalize_timestamp(0.2,'rapid',plan),0.1,delta=1e-9)

    def test_T25_missing_subject_and_invalid_identity(self):
        r=self.invoke(self.fixture(edit=lambda c,r:r['CAM-B-R2'].pop('subject_id')))
        self.assertEqual(self.ev(r)['status'],'unknown');self.assertEqual(r['status'],'insufficient_evidence')
        for edit in [lambda c,r:r['CAM-B-R2'].update(subject_id=123),lambda c,r:r['CAM-B-R2'].update(source_id='wrong'),
                     lambda c,r:c['source_inventory'].append(copy.deepcopy(c['source_inventory'][0]))]:
            path=self.fixture(edit=edit);self.invoke(path,ok=False)

    def test_T25_paths_and_output(self):
        case=self.fixture();empty=self.dir/'empty';empty.mkdir();self.invoke(case,empty)
        self.invoke(case,empty,ok=False)
        self.invoke(case,case/'nested',ok=False)
        self.invoke(case,self.dir,ok=False)
        self.invoke(case,Path(str(case)+'-other'))
        outside=self.dir/'outside.json';outside.write_text((case/'sources/CAM-B-R2.json').read_text())
        (case/'sources/CAM-B-R2.json').unlink();(case/'sources/CAM-B-R2.json').symlink_to(outside)
        self.invoke(case,ok=False)
        case=self.fixture();outlink=self.dir/'outlink';outtarget=self.dir/'outtarget';outtarget.mkdir();outlink.symlink_to(outtarget,target_is_directory=True)
        self.invoke(case,outlink,ok=False)

    def test_T25_malformed_json(self):
        case=self.fixture();(case/'sources/CAM-B-R2.json').write_text('{"invalid":')
        self.invoke(case,ok=False)
        case=self.fixture();p=case/'sources/CAM-B-R2.json';p.write_text(p.read_text().replace('"power_W": 9','"power_W": 9, "power_W": 8'))
        self.invoke(case,ok=False)

    def test_T33_zero_speed_cases(self):
        r=self.invoke(CASES['mixed_zero_speed']);self.assertEqual(r['selected_plan']['policy'],'shared')
        e=self.ev(r,v='V-SLOW');self.assertEqual(e['status'],'feasible');self.assertIsNone(e['feasible_offset_interval_ms']);self.assertEqual(e['feasible_offset_interval_kind'],'unbounded')
        self.assertEqual(self.pol(r)['shared_interval_ms'],[-2.8,-2.2]);self.assertNotEqual(r['selected_plan']['offset_ms_by_variant']['V-SLOW'],0)
        def zero(c,r):
            r['REQ-SLOW']['data']['speed_m_s']=0;r['REQ-FAST']['data']['speed_m_s']=0
        r=self.invoke(self.fixture(edit=zero));self.assertEqual(set(r['selected_plan']['offset_ms_by_variant'].values()),{0})
        self.assertEqual(self.ev(r,'CAM-D')['status'],'unknown');self.assertEqual(self.ev(r,'CAM-C')['status'],'infeasible')
        self.invoke(self.fixture(edit=lambda c,r:r['REQ-FAST']['data'].update(speed_m_s=-1)),ok=False)

    def test_T34_encoding_overflow(self):
        from reporting import dumps
        with self.assertRaisesRegex(ValueError,'encoding limitation'):dumps(Fraction(10**400,3))
        def edit(c,r):
            r['CAM-B-R2']['data']['timestamp_bias_ms_by_variant']['V-FAST']=1.0000000000000002e100
        path=self.fixture(edit=edit)
        # Finite integral values may be exactly representable as integer JSON; any limitation must be explicit.
        self.invoke(path)

    def test_T20_missing_leaf_locators_resolve(self):
        def edit(c,r):
            r['CAM-B-R2']['data'].pop('power_W')
            self.duplicate(c,r,lambda d:d.update(note='only one record has this field'))
        case=self.fixture(edit=edit);report=self.invoke(case);c,records=read_fixture(case)
        for evaluation in report['evaluations']:
            for row in evaluation['constraints']:
                for loc in row['locators']:
                    value=records[loc['source_id']]
                    for key in loc['locator'].split('/')[1:]:
                        value=value[int(key)] if isinstance(value,list) else value[key]
        for finding in report['findings']:
            path,sep,pointer=finding['locator'].partition('#')
            value=json.loads((case/path).read_text())
            if sep:
                for key in pointer.split('/')[1:]:
                    value=value[int(key)] if isinstance(value,list) else value[key]

    def test_T25_malformed_configuration_identity_is_readable(self):
        case=self.fixture(edit=lambda c,r:r['TEST-B-FAST']['data']['configuration'].update(variant_id=[]))
        result=self.invoke(case,ok=False)
        self.assertNotIn('Traceback',result.stderr)
        self.assertFalse(any(p.name.startswith('out-') for p in self.dir.iterdir()))

    def test_T25_unreadable_inventory_and_escape(self):
        case=self.fixture();source=case/'sources/CAM-B-R2.json';source.unlink()
        cmd=[sys.executable,str(ROOT/'app.py'),'analyze','--case',str(case),'--out',str(self.dir/'missing-out')]
        cp=subprocess.run(cmd,capture_output=True,text=True)
        COMMANDS.append({'test':self._testMethodName,'command':cmd,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
        self.assertEqual(cp.returncode,2);self.assertIn('error',cp.stderr.lower());self.assertNotIn('Traceback',cp.stderr)
        case=self.fixture();data=json.loads((case/'case.json').read_text());data['source_inventory'][0]['path']='../escape.json';(case/'case.json').write_text(json.dumps(data))
        cmd=[sys.executable,str(ROOT/'app.py'),'analyze','--case',str(case),'--out',str(self.dir/'escape-out')]
        cp=subprocess.run(cmd,capture_output=True,text=True)
        COMMANDS.append({'test':self._testMethodName,'command':cmd,'returncode':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr})
        self.assertEqual(cp.returncode,2);self.assertIn('contained',cp.stderr)

    def test_T21_T34_applicability_uses_emitted_offset(self):
        def edit(c,r):
            c['candidate_camera_ids']=['steady']
            r['spec-steady']['data']['timestamp_jitter_bound_ms']=0
            r['spec-steady']['data']['timestamp_bias_ms_by_variant'].update(inspect=0,rapid=0.3)
            for sid,speed in [('req-inspect',3),('req-rapid',5)]:
                r[sid]['data'].update(host_jitter_bound_ms=0,speed_m_s=speed,max_registration_error_mm=1)
            r['old-power']['data']['configuration']['offset_ms']=-13/60
        r=self.invoke(self.fixture(own=True,edit=edit))
        e=next(e for e in r['evidence_review'] if e['source_id']=='old-power')
        self.assertEqual(r['selected_plan']['offset_ms_by_variant']['rapid'],-13/60)
        self.assertIn('applicable_to_selected_configuration',e['flags'])
        self.assertNotIn('stale_configuration',e['flags'])

    def test_T35_exact_loader_and_invalid_tokens(self):
        values=sources.loads('[1e-9,1.2e3,0.1,42,-2E-3,null,true]')
        self.assertEqual(values,[Fraction(1,10**9),1200,Fraction(1,10),42,Fraction(-1,500),None,True])
        self.assertIs(type(values[-1]),bool)
        for token in ['NaN','Infinity','-Infinity']:
            with self.assertRaisesRegex(ValueError,'Nonfinite'):sources.loads(token)
            path=self.fixture();p=path/'sources/CAM-B-R2.json';p.write_text(p.read_text().replace('"power_W": 9','"power_W": '+token));self.invoke(path,ok=False)
        self.invoke(self.fixture(edit=lambda c,r:r['CAM-B-R2']['data'].update(power_W=True)),ok=False)
        self.invoke(self.fixture(edit=lambda c,r:r['CAM-B-R2']['data'].update(available=1)),ok=False)
        path=self.fixture();p=path/'sources/CAM-B-R2.json';p.write_text(p.read_text().replace('"power_W": 9','"power_W": 9e0'));self.invoke(path)


class RecordedResult(unittest.TextTestResult):
    def startTest(self,test):
        super().startTest(test);test._started=time.perf_counter()
    def stopTest(self,test):
        super().stopTest(test)
        statuses=[('failure',self.failures),('error',self.errors)]
        problem=next(((s,txt) for s,items in statuses for obj,txt in items if obj is test),None)
        RESULTS.append({'test':test.id(),'status':problem[0] if problem else 'passed','duration_seconds':time.perf_counter()-test._started,'traceback':problem[1] if problem else None})

RESULTS=[]
if __name__=='__main__':
    runner=unittest.TextTestRunner(verbosity=2,resultclass=RecordedResult)
    result=runner.run(unittest.defaultTestLoader.loadTestsFromTestCase(AppTests))
    record={'utc':datetime.now(timezone.utc).isoformat(),'command':[sys.executable,str(Path(__file__).resolve())],'work_directory':str(WORK),'tests_run':result.testsRun,
        'failure_count':len(result.failures),'error_count':len(result.errors),'results':RESULTS,'commands':COMMANDS}
    (ROOT/'records').mkdir(exist_ok=True)
    (ROOT/'records'/('tests_'+STAMP+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    print('Test record: records/tests_'+STAMP+'.json')
    sys.exit(0 if result.wasSuccessful() else 1)
