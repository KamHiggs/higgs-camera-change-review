"""In-memory bridge; numeric-output checks with a typed encoding-failure boundary."""
from fractions import Fraction
from sources import InputError, entity, loads, resolve_sources
from engine import analyze
from reporting import dumps, native


class NumericEncodingError(ArithmeticError):
    """Valid inputs cannot be represented by an admissible emitted numeric plan."""


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
            raise NumericEncodingError('Numeric encoding limitation: serialized offset violates timing; no physical impossibility inferred')
        checks.append({'variant_id':variant_id,'serialized_offset_ms':offset,'worst_case_error_mm':error,'limit_mm':v['max_registration_error_mm'],'within_output_tolerance':True})
    if plan['policy']=='shared' and len(set(plan['offset_ms_by_variant'].values()))!=1:
        raise InputError('Serialized shared offsets differ')
    return checks

def analyze_memory(case, records):
    resolved, reviews, links = resolve_sources(records)
    try:
        report = analyze(case, records, resolved, reviews, links)
        decoded = loads(dumps(report))
    except (ValueError, OverflowError) as exc:
        if "Numeric encoding limitation" in str(exc) or isinstance(exc, OverflowError):
            raise NumericEncodingError(str(exc)) from exc
        raise
    report["serialized_plan_checks"] = recheck_serialized_plan(decoded["selected_plan"], case, resolved)
    return native(report)
