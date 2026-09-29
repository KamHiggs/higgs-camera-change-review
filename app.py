#!/usr/bin/env python3
"""Offline engineering-change CLI. Python 3 standard library only."""
import argparse
import json
import sys
sys.dont_write_bytecode = True
from pathlib import Path
from fractions import Fraction
from sources import load_case, resolve_sources, inside, InputError, entity, loads
from engine import analyze
from reporting import dumps, native, view, revalidation, ADAPTER


def validate_output(case_root, output):
    raw=Path(output)
    resolved=raw.resolve()
    if inside(resolved,case_root) or inside(case_root,resolved):
        raise InputError('Output overlaps case inputs; choose a disjoint directory')
    if raw.is_symlink():
        raise InputError('Output directory cannot be a symlink')
    if resolved.exists() and (not resolved.is_dir() or any(resolved.iterdir())):
        raise InputError('Output must be nonexistent or an empty directory; refusing overwrite')
    return resolved


def recheck_serialized_plan(plan, case, resolved):
    """Recheck decoded numeric JSON, allowing only the contractual output tolerance."""
    if plan is None: return []
    c=entity(resolved,'camera',plan['camera_id'])['data']
    checks=[]
    for variant_id in case['variant_ids']:
        v=entity(resolved,'variant',variant_id)['data']
        offset=plan['offset_ms_by_variant'][variant_id]
        error=v['speed_m_s']*(abs(c['timestamp_bias_ms_by_variant'][variant_id]+offset)+c['timestamp_jitter_bound_ms']+v['host_jitter_bound_ms'])
        if error-v['max_registration_error_mm']>Fraction(1,1000000000):
            raise InputError('Numeric encoding limitation: serialized offset violates timing; no physical impossibility inferred')
        checks.append({'variant_id':variant_id,'serialized_offset_ms':offset,'worst_case_error_mm':error,'limit_mm':v['max_registration_error_mm'],'within_output_tolerance':True})
    if plan['policy']=='shared' and len(set(plan['offset_ms_by_variant'].values()))!=1:
        raise InputError('Serialized shared offsets differ')
    return checks


def run(case_dir, out_dir):
    root,case,records=load_case(case_dir)
    output=validate_output(root,out_dir)
    resolved,reviews,links=resolve_sources(records)
    report=analyze(case,records,resolved,reviews,links)
    encoded=dumps(report)
    decoded=loads(encoded)
    checks=recheck_serialized_plan(decoded['selected_plan'],case,resolved)
    report['serialized_plan_checks']=checks
    # Fully render and validate before any output files are created.
    canonical=native(report)
    files={'report.json':dumps(canonical), 'engineering_review.html':view(canonical),
           'revalidation_plan.md':revalidation(canonical)}
    if report['selected_plan']:
        files.update({'proposed_configuration.json':dumps(report['selected_plan']), 'proposed_firmware.py':ADAPTER})
    output.mkdir(parents=True,exist_ok=True)
    if any(output.iterdir()):
        raise InputError('Output became nonempty before write; refusing overwrite')
    for name,contents in files.items():
        with (output/name).open('x',encoding='utf-8') as f:
            f.write(contents)
    return canonical


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('analyze');p.add_argument('--case',required=True);p.add_argument('--out',required=True)
    args=parser.parse_args(argv)
    try:
        report=run(args.case,args.out)
    except (InputError,ValueError,OSError,OverflowError,RecursionError) as exc:
        print('Input/analysis error: '+str(exc),file=sys.stderr)
        return 2
    print(json.dumps({'case_id':report['case_id'],'status':report['status'],'output':str(Path(args.out).resolve())}))
    return 0

if __name__=='__main__':
    sys.exit(main())
