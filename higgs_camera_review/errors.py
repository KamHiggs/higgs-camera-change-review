"""Bounded integration failures; public messages never contain host paths."""
import json
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path

CATEGORIES = {'INPUT_ERROR', 'CONFIGURATION_ERROR', 'INTEGRITY_ERROR',
              'MODEL_REFUSAL', 'PROCESS_FAILURE', 'STORAGE_FAILURE'}

class ReviewFailure(Exception):
    def __init__(self, category, code, message, status=None):
        if category not in CATEGORIES:
            raise ValueError('Unknown failure category')
        self.category, self.code = category, code
        self.status = status or (500 if category in {'CONFIGURATION_ERROR', 'PROCESS_FAILURE', 'STORAGE_FAILURE'} else 400)
        super().__init__(message)

def diagnostic(code, **fields):
    """Best-effort local/operator record, outside distributable assessments."""
    root = os.environ.get('HIGGS_DIAGNOSTIC_DIR')
    if not root:
        return False
    try:
        p = Path(root); p.mkdir(parents=True, exist_ok=True)
        with (p / 'integrity-and-failures.jsonl').open('a') as f:
            f.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'code': code, **fields}, default=str) + '\n')
        return True
    except OSError:
        return False

def storage_failure(exc):
    diagnostic('STORAGE_FAILURE', exception=type(exc).__name__, traceback=traceback.format_exc())
    return ReviewFailure('STORAGE_FAILURE', 'STORAGE_ACCESS', 'Assessment storage could not complete the requested operation')
