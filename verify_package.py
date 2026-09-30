"""Verify distributed payload identities, allowing documented local run outputs."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
ROOT=Path(__file__).resolve().parent

def main():
    manifest=json.loads((ROOT/'SHA256SUMS.json').read_text())
    expected=manifest['files'];failures=[]
    for rel,digest in expected.items():
        p=PurePosixPath(rel)
        if p.is_absolute() or '..' in p.parts:
            failures.append(rel+': unsafe manifest path');continue
        path=ROOT/rel
        if not path.is_file() or any(x.is_symlink() for x in [path]+list(path.parents) if x!=ROOT and ROOT in x.parents):
            failures.append(rel+': missing or symlink');continue
        if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:failures.append(rel+': hash mismatch')
    generated={'outputs','records','test_runs','__pycache__'}
    actual={str(p.relative_to(ROOT)) for p in ROOT.rglob('*') if p.is_file() and not any(x in generated for x in p.relative_to(ROOT).parts)}
    extras=actual-set(expected)-{'SHA256SUMS.json'}
    failures.extend(x+': unexpected payload file' for x in sorted(extras))
    print(json.dumps({'status':'FAIL' if failures else 'PASS','verified_entries':len(expected),'failures':failures,'ignored_generated_directories':sorted(generated)},indent=2))
    return 1 if failures else 0

if __name__=='__main__':sys.exit(main())
