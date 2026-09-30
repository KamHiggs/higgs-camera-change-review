"""Combined-command regressions. Arithmetic expectations were pinned before coding.
Development fixtures, not unseen external acceptance or hardware validation.
"""
import copy
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT/'examples/public_camera_change'
STAMP=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
WORK=ROOT/'test_runs'/('questions-'+STAMP)
COMMANDS=[]


def decimal_json(x):
    """Fixture writer: exact finite decimal tokens, never an intermediate float."""
    if isinstance(x,Q):
        n=x.denominator
        for p in (2,5):
            while n%p==0:n//=p
        if n!=1:raise ValueError('Fixture needs a finite decimal')
        with localcontext() as ctx:
            ctx.prec=512
            return format(Decimal(x.numerator)/Decimal(x.denominator),'f')
    if isinstance(x,dict):return '{'+','.join(json.dumps(k)+':'+decimal_json(v) for k,v in x.items())+'}'
    if isinstance(x,list):return '['+','.join(decimal_json(v) for v in x)+']'
    return json.dumps(x,allow_nan=False)


def decode(text):
    return json.loads(text,object_hook=lambda d:Q(*map(int,d['$rational'])) if set(d)=={'$rational'} else d)


def read_case(path=PUBLIC):
    import sources
    _,c,r=sources.load_case(path)
    return c,{sid:{k:v for k,v in row.items() if k!='_path'} for sid,row in r.items()}


def write_case(path,c,r):
    path.mkdir(parents=True)
    for e in c['source_inventory']:
        target=path/e['path'];target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(decimal_json(r[e['source_id']])+'\n')
    (path/'case.json').write_text(decimal_json(c)+'\n')
    return path


def identities(path):
    return {str(p.relative_to(path)):hashlib.sha256(p.read_bytes()).hexdigest() for p in path.rglob('*') if p.is_file()}


def arithmetic_case(a=(Q(1),Q(3,4),Q(5,4)),biases=(Q(0),Q(1,2),-Q(1,4))):
    c,r=read_case();source=copy.deepcopy(r['CAM-D-R1']);source.update(source_id='SPEC-N',subject_id='SENSOR-N',revision='rev-N',supersedes=[])
    ids=['LINE-'+str(i) for i in range(len(a))]
    source['data'].update(timestamp_jitter_bound_ms=None,timestamp_bias_ms_by_variant=dict(zip(ids,biases)))
    records={'SPEC-N':source}
    for vid,limit in zip(ids,a):
        v=copy.deepcopy(r['REQ-SLOW']);v.update(source_id='REQ-'+vid,subject_id=vid,supersedes=[])
        v['data'].update(speed_m_s=1,host_jitter_bound_ms=0,max_registration_error_mm=limit)
        records[v['source_id']]=v
    c.update(case_id='INTEGRATION-ARITHMETIC',variant_ids=ids,candidate_camera_ids=['SENSOR-N'],source_inventory=[{'source_id':sid,'path':'facts/'+sid+'.json'} for sid in records])
    return c,records


def add(c,r,row):
    r[row['source_id']]=row;c['source_inventory'].append({'source_id':row['source_id'],'path':'facts/'+row['source_id']+'.json'})


class CombinedCommandTests(unittest.TestCase):
    def setUp(self):
        self.root=WORK/self._testMethodName;self.root.mkdir(parents=True);self.n=0
    def folder(self,c=None,r=None):
        if c is None:c,r=read_case()
        path=self.root/('case'+str(self.n));self.n+=1
        return write_case(path,c,r)
    def invoke(self,case,camera='SENSOR-N',code=0,out=None,command='questions'):
        out=out or self.root/('out'+str(self.n));self.n+=1
        cmd=[sys.executable,'-B',str(ROOT/'app.py'),command,'--case',str(case),'--out',str(out)]
        if command=='questions':cmd+=['--camera',camera]
        before=identities(case);prior_output=identities(out) if out.is_dir() else None;start=time.monotonic()
        cp=subprocess.run(cmd,cwd=self.root,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,timeout=20)
        COMMANDS.append({'test':self._testMethodName,'command':cmd,'cwd':str(self.root),'exit_code':cp.returncode,'stdout':cp.stdout,'stderr':cp.stderr,'seconds':time.monotonic()-start,'inputs_before':before,'inputs_after':identities(case)})
        self.assertEqual(before,identities(case));self.assertEqual(cp.returncode,code,cp.stderr+'\n'+cp.stdout)
        self.assertNotIn('Traceback',cp.stderr)
        if command=='analyze':
            return (json.loads((out/'report.json').read_text()) if code==0 else json.loads(cp.stderr)),out
        if code==2:
            if prior_output is not None:self.assertEqual(prior_output,identities(out))
            else:self.assertFalse(out.exists() and (out/'result.json').exists())
            return cp,out
        result=decode((out/'result.json').read_text())
        self.assertEqual(result,decode(cp.stdout))
        self.assertEqual(set(p.name for p in out.iterdir()),{'result.json','explanation.md'})
        self.assertFalse(result['deployment_qualified']);self.assertFalse(result['human_approval_recorded'])
        self.assertEqual(result['integration']['source_sha256'],{k:v for k,v in before.items() if k=='case.json' or k in [e['path'] for e in json.loads((case/'case.json').read_text())['source_inventory']]})
        return result,out
    def result(self,c,r,code=0):return self.invoke(self.folder(c,r),code=code)[0]['result']

    def test_public_guarantee_and_readable_output(self):
        q,out=self.invoke(self.folder(),camera='CAM-D');v=q['result']
        self.assertEqual(v['current_decision']['selected_plan']['camera_id'],'CAM-B')
        self.assertEqual(v['current_decision']['cost_points_exact'],5)
        self.assertEqual([p['threshold_ms'] for p in v['policies']],[Q(2,5),Q(2,5)])
        self.assertEqual([p['cost_points'] for p in v['policies']],[2,5])
        self.assertIn('typical',v['evidence_request']['text']);self.assertIn('finite',v['evidence_request']['evidence_standard'])
        self.assertEqual(v['target']['source_id'],'CAM-D-R1')
        md=(out/'explanation.md').read_text()
        for needle in ['CAM-B','CAM-D','2/5','5 synthetic','Boundary derivation','timestamp_jitter_bound_ms','V-FAST']:self.assertIn(needle,md)

    def test_other_blocker_prevents_sufficient_request(self):
        c,r=read_case();r['CAM-D-R1']['data']['power_W']=11
        q,_=self.invoke(self.folder(c,r),camera='CAM-D');v=q['result']
        self.assertEqual(v['analysis_status'],'blocked');self.assertIsNone(v['evidence_request']);self.assertEqual(v['policies'],[])
        self.assertTrue(any(x['variant_id']=='V-FAST' and x['value']==11 and x['limit']==10 for x in v['blocker_details']))

    def test_renamed_three_variants_and_source_paths(self):
        c,r=arithmetic_case();v=self.result(c,r)
        self.assertEqual([p['threshold_ms'] for p in v['policies']],[Q(5,8),Q(3,4)])
        self.assertEqual(v['current_decision']['decision_status'],'insufficient_evidence')
        self.assertEqual(v['target']['spec_revision'],'rev-N')
        self.assertEqual(v['target']['locators'][0]['file'],'facts/SPEC-N.json')
        self.assertEqual({d['variant_id'] for d in v['derivation']},set(c['variant_ids']))
        self.assertNotIn('CAM-D',json.dumps(v,default=str))

    def test_four_variants_and_changed_values(self):
        c,r=arithmetic_case((2,1,Q(3,2),Q(5,4)),(0,1,0,Q(1,2)))
        c['variant_ids'].reverse();v=self.result(c,r)
        self.assertEqual([p['threshold_ms'] for p in v['policies']],[Q(3,4),1]);self.assertEqual(len(v['derivation']),4)
        c,r=arithmetic_case((1,Q(3,2)),(0,1));v=self.result(c,r)
        self.assertEqual([p['threshold_ms'] for p in v['policies']],[Q(3,4),1]);self.assertEqual(len(v['derivation']),2)

    def test_equality_and_neighbors_through_analyze(self):
        for j,policy in [(Q(5,8)-Q(1,10000),'shared'),(Q(5,8),'shared'),(Q(5,8)+Q(1,10000),'per_variant'),(Q(3,4)-Q(1,10000),'per_variant'),(Q(3,4),'per_variant'),(Q(3,4)+Q(1,10000),None)]:
            with self.subTest(j=j):
                c,r=arithmetic_case();r['SPEC-N']['data']['timestamp_jitter_bound_ms']=j
                actual,_=self.invoke(self.folder(c,r),command='analyze');p=actual['selected_plan']
                self.assertEqual(p['policy'] if p else None,policy)
                if not p:self.assertEqual(actual['status'],'no_feasible_plan')

    def test_multiple_unknowns_no_invented_sufficiency(self):
        for f in ['power_W','available','migration_cost_points','bias','firmware']:
            with self.subTest(field=f):
                c,r=arithmetic_case()
                if f=='bias':r['SPEC-N']['data']['timestamp_bias_ms_by_variant'].pop('LINE-0')
                elif f=='firmware':c['base_firmware_revision']=None
                else:r['SPEC-N']['data'][f]=None
                v=self.result(c,r,code=3);self.assertEqual(v['analysis_status'],'unsupported');self.assertIsNone(v['evidence_request']);self.assertEqual(v['policies'],[])

    def test_u01_conflicts_and_known_failure(self):
        c,r=arithmetic_case();row=copy.deepcopy(r['SPEC-N']);row['source_id']='CONFLICT';row['data']['note']='disagreement';add(c,r,row)
        v=self.result(c,r,code=3);self.assertIn('U01',' '.join(v['remaining_unknowns']));self.assertIsNone(v['evidence_request'])
        r['SPEC-N']['data']['power_W']=100;row['data']['power_W']=100
        self.assertEqual(self.result(c,r)['analysis_status'],'blocked')

    def test_supersession_and_absent_leaf(self):
        c,r=arithmetic_case();old=copy.deepcopy(r['SPEC-N']);old.update(source_id='OLD',revision=99999);old['data']['power_W']=100;add(c,r,old)
        r['SPEC-N']['supersedes']=['OLD'];r['SPEC-N']['data'].pop('timestamp_jitter_bound_ms');v=self.result(c,r)
        self.assertEqual(v['target']['source_id'],'SPEC-N');self.assertEqual(v['target']['locators'][0]['locator'],'/data')
        self.assertEqual(v['target']['requested_locator'],'/data/timestamp_jitter_bound_ms');self.assertEqual(v['analysis_status'],'supported')

    def test_known_guarantee_and_unavailable(self):
        c,r=arithmetic_case();r['SPEC-N']['data']['timestamp_jitter_bound_ms']=Q(1,10)
        self.assertEqual(self.result(c,r)['analysis_status'],'not_needed')
        r['SPEC-N']['data']['available']=False;v=self.result(c,r)
        self.assertEqual(v['analysis_status'],'blocked');self.assertIsNone(v['evidence_request'])

    def test_cost_ties_and_more_expensive_are_not_savings(self):
        for cost,effect in [(4,'reduce_established_cost'),(2,'add_equal_cost_alternative'),(1,'more_expensive_alternative')]:
            c,r=arithmetic_case();alt=copy.deepcopy(r['SPEC-N']);alt.update(source_id='ALT',subject_id='OTHER');alt['data'].update(timestamp_jitter_bound_ms=0,migration_cost_points=cost,timestamp_bias_ms_by_variant=dict.fromkeys(c['variant_ids'],0));add(c,r,alt);c['candidate_camera_ids'].append('OTHER')
            v=self.result(c,r);self.assertEqual(v['policies'][0]['effect_if_this_policy_feasible'],effect)
            if cost==1:self.assertIsNone(v['evidence_request'])

    def test_zero_speed_and_empty_domains(self):
        c,r=arithmetic_case()
        for row in r.values():
            if row['kind']=='variant':row['data']['speed_m_s']=0
        v=self.result(c,r);self.assertEqual([p['domain']['kind'] for p in v['policies']],['unbounded','unbounded']);self.assertIsNotNone(v['evidence_request'])
        r['REQ-LINE-1']['data']['speed_m_s']=1;v=self.result(c,r);self.assertEqual([p['threshold_ms'] for p in v['policies']],[Q(3,4),Q(3,4)])
        c,r=arithmetic_case((1,),(0,));r['REQ-LINE-0']['data'].update(speed_m_s=2,host_jitter_bound_ms=1)
        v=self.result(c,r);self.assertEqual([p['threshold_ms'] for p in v['policies']],[-Q(1,2),-Q(1,2)]);self.assertIsNone(v['evidence_request'])

    def test_numeric_failure_in_current_analyze_and_questions(self):
        c,r=arithmetic_case((0,),(Q('1000000000.00000001'),));r['SPEC-N']['data']['timestamp_jitter_bound_ms']=0
        path=self.folder(c,r)
        error,out=self.invoke(path,command='analyze',code=4);self.assertEqual(error['execution_status'],'numeric_encoding_error');self.assertFalse(out.exists())
        q,_=self.invoke(path,code=4);self.assertEqual(q['result']['current_decision']['execution_status'],'numeric_encoding_error');self.assertIsNone(q['result']['current_decision']['selected_plan'])

    def test_numeric_failure_in_conditional_preview(self):
        c,r=arithmetic_case((0,),(Q('1000000000.00000001'),));v=self.result(c,r)
        self.assertEqual([p['threshold_ms'] for p in v['policies']],[0,0])
        w=v['regions'][0]['preview'];self.assertEqual(w['execution_status'],'numeric_encoding_error');self.assertNotIn('result',w)
        self.assertIsNone(v['evidence_request'])
        self.assertEqual(v['derivation'][0]['bias_ms'],Q('1000000000.00000001'))

    def test_serialization_tolerance_equality(self):
        for residual in ['0.000000001','0.0000000001','0']:
            c,r=arithmetic_case((0,),(10**9+Q(residual),));r['SPEC-N']['data']['timestamp_jitter_bound_ms']=0
            v,_=self.invoke(self.folder(c,r),command='analyze');self.assertEqual(v['status'],'feasible_plan')

    def test_malformed_and_no_fallback(self):
        path=self.folder();self.invoke(path,camera='NOT-DECLARED',code=2)
        for token in ['true','NaN','Infinity','-1','"wrong"']:
            c,r=arithmetic_case();p=self.folder(c,r);s=p/'facts/SPEC-N.json';s.write_text(s.read_text().replace('"power_W":6','"power_W":'+token))
            # Find the actual supplied power token if formatting/value differs.
            if s.read_text()==decimal_json(r['SPEC-N'])+'\n':
                import re
                s.write_text(re.sub(r'"power_W":[^,}]+','"power_W":'+token,s.read_text()))
            self.invoke(p,code=2)
        p=self.root/'empty';p.mkdir();self.invoke(p,code=2)
        p=self.folder();(p/'case.json').write_text('{}');self.invoke(p,code=2)
        p=self.folder();s=p/'case.json';s.write_text(s.read_text().replace('"case_id":','"case_id":"duplicate","case_id":'));self.invoke(p,camera='CAM-D',code=2)
        p=self.folder();(p/'sources/CAM-D-R1.json').write_text('{');self.invoke(p,camera='CAM-D',code=2)

    def test_unsupported_declared_world(self):
        c,r=arithmetic_case();c['synthetic']=False
        q,_=self.invoke(self.folder(c,r),code=3);self.assertEqual(q['execution_status'],'unsupported');self.assertNotIn('result',q)

    def test_fresh_outputs_and_symlinks(self):
        p=self.folder();q,out=self.invoke(p,camera='CAM-D')
        self.invoke(p,camera='CAM-D',code=2,out=out)
        self.invoke(p,camera='CAM-D',code=2,out=p/'nested')
        self.invoke(p,camera='CAM-D',code=2,out=self.root)
        target=self.root/'target';target.mkdir();link=self.root/'link';link.symlink_to(target,target_is_directory=True)
        self.invoke(p,camera='CAM-D',code=2,out=link/'new')
        outside=self.root/'outside.json';outside.write_text((p/'sources/CAM-D-R1.json').read_text());(p/'sources/CAM-D-R1.json').unlink();(p/'sources/CAM-D-R1.json').symlink_to(outside)
        self.invoke(p,camera='CAM-D',code=2)

    def test_hypotheses_labeled_and_single_snapshot(self):
        c,r=arithmetic_case();path=self.folder(c,r)
        import questions_cli, camera_cognimap as cm
        _,base,hashes=questions_cli.load_snapshot(path)
        # A later source edit cannot leak into nested evaluation of this capture.
        changed=copy.deepcopy(r['SPEC-N']);changed['data']['power_W']=100
        (path/'facts/SPEC-N.json').write_text(decimal_json(changed))
        with mock.patch('sources.load_case',side_effect=AssertionError('Unexpected nested read')):
            result=cm.execute('camera','decision_questions',{'camera_id':'SENSOR-N','base':base})['result']
        self.assertEqual(result['analysis_status'],'supported');self.assertTrue(result['base_unchanged'])
        self.assertEqual(result['base_input_identity'],result['current_decision']['input_identity'])
        for region in result['regions']:
            w=region['preview'];self.assertTrue(w['hypothetical'])
            if w['execution_status']=='completed':
                self.assertEqual(w['result']['decision_scope'],'hypothetical_only')
                self.assertFalse(w['assumption']['promoted_to_fact'])
                if w['result']['selected_plan']:self.assertTrue(w['result']['selected_plan']['hypothetical'])
        _,out=self.invoke(path) # actual CLI now sees the changed power
        self.assertEqual(decode((out/'result.json').read_text())['result']['analysis_status'],'blocked')


if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CombinedCommandTests))
    target=ROOT/'records';target.mkdir(exist_ok=True)
    (target/('questions-'+STAMP+'.json')).write_text(json.dumps({'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'commands':COMMANDS},indent=2)+'\n')
    sys.exit(0 if result.wasSuccessful() else 1)
