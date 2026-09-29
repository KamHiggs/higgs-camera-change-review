"""Reproducible actual CLI runs and exported adapter checks; never executes input code."""
import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT/'examples/public_camera_change'
FIXTURES=ROOT/'tests/fixtures'
CASES={'public':PUBLIC, **{name:FIXTURES/name for name in (
       'own_boundary','devised_shared','zero_radius','mixed_zero_speed',
       'descriptive_conflict','bias_equalized','jitter_known','all_blocked','insufficient')}}

def hashes(case):
    paths=[case/'case.json']+[case/e['path'] for e in json.loads((case/'case.json').read_text())['source_inventory']]
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def adapter_checks(out):
    config=json.loads((out/'proposed_configuration.json').read_text())
    spec=importlib.util.spec_from_file_location('owned_generated_adapter',out/'proposed_firmware.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    results=[]
    for variant,offset in config['offset_ms_by_variant'].items():
        for timestamp in [-100,0,123.25]:
            actual=module.normalize_timestamp(timestamp,variant,config)
            expected=timestamp+offset
            assert abs(actual-expected)<=1e-9,(variant,timestamp,actual,expected)
            results.append({'variant_id':variant,'timestamp':timestamp,'offset':offset,'actual':actual,'expected':expected})
    unknown='__unknown_variant__'
    while unknown in config['offset_ms_by_variant']:unknown+='x'
    try: module.normalize_timestamp(0,unknown,config)
    except (ValueError,KeyError) as exc: results.append({'unknown_variant':unknown,'explicit_error':str(exc)})
    else: raise AssertionError('Unknown variant accepted')
    return results


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--batch',required=True);parser.add_argument('names',nargs='+',choices=list(CASES))
    args=parser.parse_args(); records=[]
    # Keep new batch evidence local and never overwrite a previous run.
    if not args.batch or any(ch not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for ch in args.batch):
        parser.error('--batch must contain only letters, digits, underscores or hyphens')
    log_dir=ROOT/'records'; log_dir.mkdir(exist_ok=True)
    path=log_dir/('runs_'+args.batch+'.json')
    if path.exists() or (ROOT/'outputs'/args.batch).exists():
        parser.error('Batch already exists; choose a new --batch name')
    with path.open('x',encoding='utf-8') as stream:
        stream.write('[]\n')
    for name in args.names:
        case=CASES[name];out=ROOT/'outputs'/args.batch/name
        before=hashes(case); start=time.perf_counter(); utc=datetime.now(timezone.utc).isoformat()
        cmd=[sys.executable,'app.py','analyze','--case',str(case),'--out',str(out)]
        cp=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
        item={'name':name,'utc':utc,'command':cmd,'returncode':cp.returncode,'duration_seconds':time.perf_counter()-start,
              'stdout':cp.stdout,'stderr':cp.stderr,'input_hashes_before':before,'input_hashes_after':hashes(case),'adapter_checks':[]}
        if cp.returncode==0:
            report=json.loads((out/'report.json').read_text());item['status']=report['status'];item['selected_plan']=report['selected_plan']
            if report['selected_plan']:item['adapter_checks']=adapter_checks(out)
        records.append(item)
        path.write_text(json.dumps(records,indent=2)+'\n')
        print(name,cp.returncode,item.get('status'),cp.stderr)
    if any(r['returncode'] or r['input_hashes_before']!=r['input_hashes_after'] for r in records):return 1
    return 0

if __name__=='__main__':sys.exit(main())
