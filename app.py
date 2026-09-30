#!/usr/bin/env python3
"""Offline engineering-change CLI. Python 3 standard library only."""
import argparse
import json
import sys
sys.dont_write_bytecode = True
from pathlib import Path
from fractions import Fraction
from sources import load_case, resolve_sources, inside, InputError, entity, loads
from camera_runtime import analyze_memory, NumericEncodingError, recheck_serialized_plan
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


def run(case_dir, out_dir):
    root,case,records=load_case(case_dir)
    output=validate_output(root,out_dir)
    report=analyze_memory(case,records)
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
    q=sub.add_parser("questions", help="Derive decision-changing jitter evidence from this case")
    q.add_argument("--case", required=True); q.add_argument("--camera", required=True); q.add_argument("--out", required=True)
    args=parser.parse_args(argv)
    try:
        if args.command == "questions":
            from questions_cli import run_questions
            return run_questions(args.case, args.camera, args.out)
        report=run(args.case,args.out)
    except NumericEncodingError as exc:
        print(json.dumps({"execution_status":"numeric_encoding_error", "decision_status":None, "error":str(exc), "deployment_qualified":False}), file=sys.stderr)
        return 4
    except (InputError,ValueError,OSError,OverflowError,RecursionError) as exc:
        print('Input/analysis error: '+str(exc),file=sys.stderr)
        return 2
    print(json.dumps({'case_id':report['case_id'],'status':report['status'],'output':str(Path(args.out).resolve())}))
    return 0

if __name__=='__main__':
    sys.exit(main())
