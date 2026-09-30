"""Inventory loading and field-level source authority; input documents are data."""
import json
from fractions import Fraction
from pathlib import Path

class InputError(ValueError):
    pass


def reject_nonfinite_constant(value):
    raise InputError('Nonfinite JSON constant: ' + value)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError('Duplicate JSON key: ' + key)
        result[key] = value
    return result


def loads(text):
    return json.loads(text, parse_float=Fraction,
                      parse_constant=reject_nonfinite_constant,
                      object_pairs_hook=unique_object)


def read_json(path):
    try:
        return loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError, UnicodeError) as exc:
        raise InputError('{}: {}'.format(path, exc)) from exc


def inside(path, parent):
    return path == parent or parent in path.parents


def string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise InputError(label + ' must be a nonempty string')


def number(value, label, minimum=None, positive=False):
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise InputError(label + ' must be a finite number or null (not a boolean)')
    if minimum is not None and value < minimum or positive and value <= 0:
        raise InputError(label + ' is outside its documented nonnegative/positive domain')


NONNEG = {'max_fps','power_W','timestamp_jitter_bound_ms','migration_cost_points',
          'typical_timestamp_jitter_ms','field_of_view_mm','supply_voltage_V',
          'host_jitter_bound_ms','required_fps','max_mm_per_pixel','link_capacity_MB_s',
          'power_budget_W','speed_m_s','max_registration_error_mm','recorded_limit'}
POSITIVE = {'image_width_px','image_height_px','bytes_per_pixel'}
SIGNED = {'default_offset_ms','shared_offset_ms','offset_ms'}


def validate_data(data, label):
    if not isinstance(data, dict):
        raise InputError(label + ' must be an object')
    for key, value in data.items():
        loc = label + '/' + key
        if key in NONNEG | POSITIVE | SIGNED:
            number(value, loc, 0 if key in NONNEG else None, key in POSITIVE)
        if key == 'available' and value is not None and not isinstance(value, bool):
            raise InputError(loc + ' must be boolean or null')
        if key in {'transport','variant_id','camera_id','spec_source_id','firmware_revision','policy','metric','claimed_result'} and value is not None:
            string(value, loc)
        if key in {'timestamp_bias_ms_by_variant','offset_ms_by_variant'} and value is not None:
            if not isinstance(value, dict):
                raise InputError(loc + ' must be an object')
            for name, val in value.items():
                number(val, loc + '/' + name)
        if key in {'supply_range_V','observations'} and value is not None:
            if not isinstance(value, list) or key == 'supply_range_V' and len(value) != 2:
                raise InputError(loc + ' has invalid array shape')
            for val in value:
                number(val, loc, 0 if key == 'supply_range_V' else None)
            if key == 'supply_range_V' and all(v is not None for v in value) and value[0] > value[1]:
                raise InputError(loc + ' lower bound exceeds upper bound')
        if key == 'configuration' and value is not None:
            validate_data(value, loc)
        if key == 'edges' and value is not None:
            if not isinstance(value, list):
                raise InputError(loc + ' must be an array')
            for edge in value:
                if not isinstance(edge, dict):
                    raise InputError(loc + ' edge must be an object')
                string(edge.get('from'), loc + '/from')
                string(edge.get('to'), loc + '/to')


def load_case(case_dir, read_document=None):
    read_document = read_json if read_document is None else read_document
    root = Path(case_dir).resolve(strict=True)
    if not root.is_dir():
        raise InputError('Case must be a directory')
    case_path = (root / 'case.json').resolve(strict=True)
    if not inside(case_path, root):
        raise InputError('case.json escapes case directory')
    case = read_document(case_path)
    if not isinstance(case, dict):
        raise InputError('case.json must be an object')
    string(case.get('case_id'), 'case_id')
    for key in ('variant_ids','candidate_camera_ids'):
        vals = case.get(key)
        if not isinstance(vals, list) or not vals:
            raise InputError(key + ' must be a nonempty array')
        for val in vals:
            string(val, key)
        if len(vals) != len(set(vals)):
            raise InputError('Duplicate ' + key)
    if case.get('base_firmware_revision') is not None:
        string(case['base_firmware_revision'], 'base_firmware_revision')
    inv = case.get('source_inventory')
    if not isinstance(inv, list):
        raise InputError('source_inventory must be an array')
    records, paths = {}, set()
    for entry in inv:
        if not isinstance(entry, dict):
            raise InputError('Inventory entry must be an object')
        sid, rel = entry.get('source_id'), entry.get('path')
        string(sid, 'inventory source_id'); string(rel, 'inventory path')
        if sid in records:
            raise InputError('Duplicate inventory source_id: ' + sid)
        if Path(rel).is_absolute() or '..' in Path(rel).parts:
            raise InputError('Inventory path must be contained and relative: ' + rel)
        path = (root / rel).resolve(strict=True)
        if not inside(path, root):
            raise InputError('Inventory path escapes case: ' + rel)
        if path in paths:
            raise InputError('Duplicate inventory path: ' + rel)
        paths.add(path)
        rec = read_document(path)
        if not isinstance(rec, dict) or rec.get('source_id') != sid:
            raise InputError('Inventory/source identity mismatch: ' + sid)
        for key in ('kind','status'):
            string(rec.get(key), sid + '/' + key)
        if rec['status'] not in {'active','historical','superseded'}:
            raise InputError('Invalid source status: ' + sid)
        if 'subject_id' in rec and rec['subject_id'] is not None:
            string(rec['subject_id'], sid + '/subject_id')
        supersedes = rec.get('supersedes', [])
        if not isinstance(supersedes, list):
            raise InputError(sid + '/supersedes must be an array')
        for predecessor in supersedes:
            string(predecessor, sid + '/supersedes')
        rec['supersedes'] = supersedes
        validate_data(rec.get('data'), sid + '/data')
        rec['_path'] = rel
        records[sid] = rec
    return root, case, records


MISSING = object()

def equal(a, b):
    if a is MISSING or b is MISSING:
        return a is b
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, Fraction)) and isinstance(b, (int, Fraction)):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a == b


def consensus(values, path='/data'):
    if all(equal(values[0], val) for val in values[1:]):
        return (None if values[0] is MISSING else values[0]), []
    if all(isinstance(v, dict) for v in values):
        result, conflicts = {}, []
        for key in sorted(set().union(*(set(v) for v in values))):
            result[key], leaves = consensus([v.get(key, MISSING) for v in values], path + '/' + key.replace('~','~0').replace('/','~1'))
            conflicts.extend(leaves)
        return result, conflicts
    if all(isinstance(v,list) for v in values) and len({len(v) for v in values}) == 1:
        result, conflicts = [], []
        for i in range(len(values[0])):
            val, leaves = consensus([v[i] for v in values], path + '/' + str(i))
            result.append(val); conflicts.extend(leaves)
        return result, conflicts
    return None, [path]


def resolve_sources(records):
    retired, invalid_links = {}, []
    for sid, rec in records.items():
        if rec['status'] != 'active' or rec.get('subject_id') is None:
            continue
        for pred in rec['supersedes']:
            old = records.get(pred)
            if old and (old['kind'], old.get('subject_id')) == (rec['kind'],rec['subject_id']):
                retired.setdefault(pred, []).append(sid)
            else:
                invalid_links.append((sid, pred))
    # No invented winner for an explicit cycle.
    def visit(sid, trail):
        if sid in trail:
            raise InputError('Cyclic same-subject supersession: ' + ' -> '.join(trail + [sid]))
        for nxt in retired.get(sid, []):
            visit(nxt, trail + [sid])
    for sid in retired:
        visit(sid, [])
    groups, reviews = {}, {}
    for sid, rec in records.items():
        disposition = 'superseded' if sid in retired else rec['status']
        reason = 'Explicitly retired by ' + ', '.join(sorted(retired[sid])) if sid in retired else 'Recorded status: ' + rec['status']
        reviews[sid] = {'source_id':sid,'disposition':disposition,'reason':reason,'path':rec['_path']}
        if disposition == 'active':
            if rec.get('subject_id') is None:
                reviews[sid]['reason'] += '; missing subject_id: unresolved association, no fallback'
            else:
                groups.setdefault((rec['kind'],rec['subject_id']), []).append(rec)
    resolved = {}
    for key, group in groups.items():
        group.sort(key=lambda r:r['source_id'])
        data, conflicts = consensus([r['data'] for r in group])
        ids = [r['source_id'] for r in group]
        if conflicts:
            for sid in ids:
                reviews[sid].update(disposition='conflicted',reason='Unresolved leaves: ' + ', '.join(conflicts), conflict_fields=conflicts, source_ids=ids)
        resolved[key] = {'data':data,'source_ids':ids,'conflicts':conflicts,
                         'representative':ids[0] if not conflicts else None,
                         '_source_data':{r['source_id']:r['data'] for r in group}}
    return resolved, [reviews[s] for s in sorted(reviews)], invalid_links


def entity(resolved, kind, subject):
    return resolved.get((kind,subject), {'data':{},'source_ids':[], 'conflicts':[], 'representative':None})


def existing_pointer(document, pointer):
    """Cite the exact leaf if present; otherwise its nearest existing parent."""
    current = document
    existing = []
    for token in pointer.split('/')[1:]:
        key = token.replace('~1','/').replace('~0','~')
        if isinstance(current, dict) and key in current:
            current = current[key]
        elif isinstance(current, list) and key.isdigit() and int(key) < len(current):
            current = current[int(key)]
        else:
            break
        existing.append(token)
    return '/' + '/'.join(existing) if existing else ''
