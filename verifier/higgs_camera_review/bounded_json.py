"""Bounded assessment JSON intake; no arbitrary-depth or general hostile-archive claim."""
import json
from pathlib import Path
from .errors import ReviewFailure

MAX_BYTES = 4 * 1024 * 1024
MAX_DEPTH = 64

def refuse(code, message):
    raise ReviewFailure('INTEGRITY_ERROR', code, message)

def loads(raw):
    if len(raw) > MAX_BYTES:
        refuse('ASSESSMENT_STRUCTURE_LIMIT_EXCEEDED', 'Assessment JSON exceeds the supported 4 MiB document limit')
    try:
        text = raw.decode('utf-8') if isinstance(raw, bytes) else raw
        depth = 0
        quoted = escaped = False
        for ch in text:
            if quoted:
                if escaped: escaped = False
                elif ch == chr(92): escaped = True
                elif ch == '"': quoted = False
            elif ch == '"': quoted = True
            elif ch in '[{':
                depth += 1
                if depth > MAX_DEPTH:
                    refuse('ASSESSMENT_STRUCTURE_LIMIT_EXCEEDED', 'Assessment JSON exceeds the supported 64 container levels')
            elif ch in ']}': depth -= 1
        return json.loads(text, parse_constant=lambda _: refuse('MALFORMED_ASSESSMENT', 'Nonfinite JSON constants are unsupported'))
    except RecursionError as exc:
        raise ReviewFailure('INTEGRITY_ERROR', 'ASSESSMENT_STRUCTURE_LIMIT_EXCEEDED', 'Assessment exceeds supported parser recursion') from exc
    except ValueError as exc:
        # Includes JSONDecodeError, UnicodeError and the interpreter's integer
        # conversion limit. Keep its configured limit; refuse this document.
        raise ReviewFailure('INTEGRITY_ERROR', 'MALFORMED_ASSESSMENT', 'Assessment JSON is malformed, not UTF-8, or exceeds the parser integer limit') from exc

def load(path):
    try:
        with Path(path).open('rb') as handle:
            return loads(handle.read(MAX_BYTES + 1))
    except OSError as exc:
        raise ReviewFailure('INTEGRITY_ERROR', 'ASSESSMENT_DOCUMENT', 'Required assessment document is missing or unreadable') from exc
