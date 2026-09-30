"""Camera-only adaptation of Higgs Python CogniMap v0.1.2.
Created and led by Kamden Higgs. See docs/COGNIMAP_INTEGRATION.md.
No embedded case, power cartridge, plugin loader, or alternate engineering core.
"""
from __future__ import annotations
import copy
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import PurePosixPath
from typing import Any
import sources as cs
from camera_runtime import NumericEncodingError, analyze_memory
VERSION = "0.1.2"
APPLICATION_VERSION = "0.3.0-rc.1"
INTERFACE_VERSION = "higgs.python-cognimap/1"
CAMERA_MODEL = "EC-SYNTHETIC-1.0"
MAX_BYTES = 524288
MAX_RECORDS = 64
MAX_VARIANTS = 16
MAX_CANDIDATES = 16
MAX_SWEEP = 16
MAX_DEPTH = 32
class ContractError(ValueError):
    pass
class Unsupported(ContractError):
    pass


def exact_tree(value: Any, depth: int = 0) -> Any:
    """Bounded pure input validator. Never silently converts a binary float."""
    if depth > MAX_DEPTH:
        raise ContractError("Nesting limit exceeded")
    if value is None or type(value) is bool:
        return value
    if type(value) is int or isinstance(value, Fraction):
        q = Fraction(value)
        if abs(q.numerator).bit_length() > 512 or q.denominator.bit_length() > 512:
            raise ContractError("Numeric magnitude/precision limit exceeded")
        return value
    if type(value) is str:
        if len(value) > 16384:
            raise ContractError("String length limit exceeded")
        try:
            value.encode("utf-8")
        except UnicodeError as exc:
            raise ContractError("Invalid Unicode") from exc
        return value
    if type(value) in (list, tuple):
        if len(value) > 512:
            raise ContractError("Collection limit exceeded")
        return [exact_tree(v, depth + 1) for v in value]
    if type(value) is dict:
        if len(value) > 512 or not all(type(k) is str for k in value):
            raise ContractError("Object keys must be strings; bounded object size required")
        return {exact_tree(k, depth + 1): exact_tree(v, depth + 1) for k, v in value.items()}
    raise ContractError("Unsupported value type; use exact ints/Fractions (or JSON decimal tokens), not Python floats")


def _identity_tree(value: Any) -> Any:
    if isinstance(value, Fraction):
        return ["number", str(value.numerator), str(value.denominator)]
    if type(value) is int:
        return ["number", str(value), "1"]
    if isinstance(value, dict):
        return ["object", [[k, _identity_tree(value[k])] for k in sorted(value)]]
    if isinstance(value, (tuple, list)):
        return ["array", [_identity_tree(x) for x in value]]
    return [type(value).__name__, value]


def digest(value: Any) -> str:
    raw = json.dumps(_identity_tree(value), sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def keys(value: dict, allowed: set[str], required: set[str] = frozenset()) -> None:
    if not isinstance(value, dict):
        raise ContractError("Object required")
    extra, missing = set(value) - allowed, required - set(value)
    if extra or missing:
        raise ContractError("Unexpected fields: %s; missing fields: %s" % (sorted(extra), sorted(missing)))


def finite_number(value: Any, label: str, *, nonnegative: bool = True) -> Fraction:
    if type(value) is bool or not isinstance(value, (int, Fraction)):
        raise ContractError(label + " requires an exact number, not a boolean/null/string")
    q = Fraction(exact_tree(value))
    if nonnegative and q < 0:
        raise ContractError(label + " must be nonnegative")
    return q


def _camera_prepare(inputs: dict, *, allow_hypothesis: bool = False) -> tuple[dict, dict]:
    keys(inputs, {"model_id", "case_data", "source_records"}, {"model_id", "case_data", "source_records"})
    if inputs.get("model_id") != CAMERA_MODEL:
        raise Unsupported("Only the declared synthetic camera model is supported; no real-case suitability is inferred")
    case, rows = copy.deepcopy(inputs.get("case_data")), copy.deepcopy(inputs.get("source_records"))
    if not isinstance(case, dict) or not isinstance(rows, list):
        raise ContractError("case_data and source_records are required together")
    # The required model_id explicitly selects the synthetic world. Preserve an
    # absent legacy synthetic field; never manufacture it or accept an explicit
    # contradictory declaration. This is a scope declaration, not a fit proof.
    if case.get("schema_version") != "1.0" or ("synthetic" in case and case["synthetic"] is not True):
        raise Unsupported("The schema/model declaration must select the synthetic world without a contradictory synthetic flag")
    cs.string(case.get("case_id"), "case_id")
    for field, limit in (("variant_ids", MAX_VARIANTS), ("candidate_camera_ids", MAX_CANDIDATES)):
        vals = case.get(field)
        if not isinstance(vals, list) or not vals or len(vals) > limit:
            raise ContractError(field + " must be a bounded nonempty list")
        for val in vals:
            cs.string(val, field)
        if len(set(vals)) != len(vals):
            raise ContractError("Duplicate entity identity")
    if case.get("base_firmware_revision") is not None:
        cs.string(case["base_firmware_revision"], "base_firmware_revision")
    inv = case.get("source_inventory")
    if not isinstance(inv, list) or len(inv) > MAX_RECORDS or len(rows) > MAX_RECORDS:
        raise ContractError("Bounded source inventory required")
    row_map = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ContractError("Source record must be an object")
        sid = row.get("source_id"); cs.string(sid, "source_id")
        if sid in row_map:
            raise ContractError("Duplicate source record")
        if row.get("epistemic_kind") == "hypothetical_assumption" and not allow_hypothesis:
            raise ContractError("Hypothetical source cannot enter ordinary analysis")
        for field in ("kind", "status"):
            cs.string(row.get(field), field)
        if row["status"] not in {"active", "historical", "superseded"}:
            raise ContractError("Unknown source status")
        if row.get("subject_id") is not None:
            cs.string(row["subject_id"], "subject_id")
        preds = row.get("supersedes", [])
        if not isinstance(preds, list):
            raise ContractError("supersedes must be an array")
        for pred in preds:
            cs.string(pred, "supersedes")
        row["supersedes"] = preds
        cs.validate_data(row.get("data"), sid + "/data")
        row_map[sid] = row
    records, seen_paths = {}, set()
    for entry in inv:
        keys(entry, {"source_id", "path"}, {"source_id", "path"})
        sid, rel = entry["source_id"], entry["path"]
        cs.string(sid, "inventory source_id"); cs.string(rel, "inventory path")
        p = PurePosixPath(rel)
        if p.is_absolute() or ".." in p.parts or "\\" in rel or ":" in rel or str(p) != rel:
            raise ContractError("Inventory locator must be canonical relative POSIX path")
        if sid in records or rel in seen_paths:
            raise ContractError("Duplicate inventory identity/path")
        if sid not in row_map:
            raise ContractError("Inventory source missing: " + sid)
        row_map[sid]["_path"] = rel
        records[sid] = row_map[sid]; seen_paths.add(rel)
    if set(records) != set(row_map):
        raise ContractError("Unlisted source records are not admitted")
    _guard_supersession_work(records)
    return case, records


def _guard_supersession_work(records: dict) -> None:
    """Bound inherited resolver traversal before it recurses; no winner invented."""
    links = {}
    for sid, rec in records.items():
        if rec["status"] != "active" or rec.get("subject_id") is None:
            continue
        for pred in rec["supersedes"]:
            other = records.get(pred)
            if other and (other["kind"], other.get("subject_id")) == (rec["kind"], rec["subject_id"]):
                links.setdefault(pred, []).append(sid)
    work = 0
    for root in links:
        stack = [(root, frozenset())]
        while stack:
            node, trail = stack.pop(); work += 1
            if work > 4096:
                raise ContractError("Supersession traversal work limit exceeded")
            if node in trail:
                raise ContractError("Cyclic same-subject supersession")
            stack.extend((n, trail | {node}) for n in links.get(node, []))


def camera_evaluate(inputs: dict) -> dict:
    case, records = _camera_prepare(inputs)
    result = analyze_memory(case, records)
    return {"decision_status": result["status"], "run_kind": "analysis", "report": result,
            "input_identity": digest({"case": case, "records": records}),
            "rule_ids": ["R-AUTH", "R-FPS", "R-RES", "R-BW", "R-POWER", "R-VOLT", "R-TRANSPORT", "R-TIME", "R-SELECT", "R-EVIDENCE", "R-SERIAL", "R-U01"],
            "source_ids": sorted(records), "model_applicability": "synthetic_model_only"}


def camera_decision_questions(inputs: dict) -> dict:
    from decision_questions import decision_questions
    return decision_questions(inputs, sys.modules[__name__])


def _scenario(case: dict, records: dict, camera_id: str, bound: Any, index: int) -> tuple[dict, dict, dict]:
    resolved, _, _ = cs.resolve_sources(records)
    ent = cs.entity(resolved, "camera", camera_id)
    sid = ent["representative"]
    if sid is None:
        raise ContractError("Simulation target needs an unconflicted active source identity")
    if bound is not None:
        bound = finite_number(bound, "hypothetical jitter bound")
    if len(records) >= MAX_RECORDS:
        raise ContractError("No capacity for a scenario source within the declared record limit")
    c, rs = copy.deepcopy(case), copy.deepcopy(records)
    new_id = sid + "--HYP-" + str(index)
    if new_id in rs:
        raise ContractError("Hypothesis source identity collision")
    rec = copy.deepcopy(rs[sid]); rec.pop("_path", None)
    rec.update(source_id=new_id, status="active", revision="hypothesis-" + str(index),
               supersedes=list(ent["source_ids"]), epistemic_kind="hypothetical_assumption")
    rec["data"]["timestamp_jitter_bound_ms"] = bound
    path = "scenario_sources/hypothesis-%02d.json" % index
    if path in {r["_path"] for r in rs.values()}:
        raise ContractError("Hypothesis path identity collision")
    rec["_path"] = path; rs[new_id] = rec
    _guard_supersession_work(rs)
    c["case_id"] = case["case_id"] + "--SIM-" + str(index)
    c["source_inventory"].append({"source_id": new_id, "path": path})
    return c, rs, {"base_source_id": sid, "source_id": new_id, "virtual_path": path,
                   "source_record": {k: v for k, v in rec.items() if k != "_path"},
                   "field": "/data/timestamp_jitter_bound_ms", "hypothetical_value_ms": bound,
                   "evidence_kind": "hypothetical_assumption", "promoted_to_fact": False}


def camera_simulate(inputs: dict) -> dict:
    keys(inputs, {"base", "camera_id", "bounds_ms"}, {"camera_id", "bounds_ms"})
    base = inputs.get("base", {})
    case, records = _camera_prepare(base)
    cid = inputs["camera_id"]; cs.string(cid, "camera_id")
    if cid not in case["candidate_camera_ids"]:
        raise ContractError("Simulation camera must be a declared candidate")
    bounds = inputs["bounds_ms"]
    if not isinstance(bounds, list) or not 1 <= len(bounds) <= MAX_SWEEP:
        raise ContractError("bounds_ms requires 1..16 explicit values")
    before = digest({"case": case, "records": records})
    runs = []
    for i, bound in enumerate(bounds, 1):
        c, rs, assumption = _scenario(case, records, cid, bound, i)
        report = analyze_memory(c, rs)
        # Labels travel with a detached scenario report or extracted plan too.
        report["run_kind"] = "simulation"
        report["decision_scope"] = "hypothetical_only"
        report["hypothetical_source_ids"] = [assumption["source_id"]]
        report["limitations"].insert(0, "HYPOTHETICAL SCENARIO: the added bound is assumed, not observed or guaranteed by a supplier")
        if report["selected_plan"] is not None:
            report["selected_plan"]["hypothetical"] = True
        runs.append({"scenario_id": c["case_id"], "input_identity": digest({"case": c, "records": rs}),
                     "assumption": assumption, "report": report})
    unchanged = before == digest({"case": case, "records": records})
    if not unchanged:
        raise RuntimeError("Simulation changed base data")
    return {"decision_status": "hypothetical_results_only", "run_kind": "simulation",
            "base_input_identity": before, "base_unchanged": True, "scenarios": runs,
            "rule_ids": ["R-SIM", "R-TIME", "R-SELECT", "R-EVIDENCE"],
            "limitations": ["No supplier guarantee was obtained or stored", "Scenario sources are returned virtual records, not edits to the evidence directory", "No random distribution or hardware model validation is claimed"]}

OPERATIONS = {"camera": {"evaluate": camera_evaluate, "simulate": camera_simulate, "decision_questions": camera_decision_questions}}

def execute(cartridge: str, operation: str, inputs: dict | None = None) -> dict:
    """Common host interface. Domain conclusion and software status stay separate."""
    envelope = {"interface_version": INTERFACE_VERSION, "cartridge_id": cartridge, "cartridge_version": VERSION,
                "operation": operation, "execution_status": "not_started", "decision_status": None,
                "deployment_qualified": False, "human_approval_recorded": False}
    try:
        data = exact_tree({} if inputs is None else inputs)
        if not isinstance(data, dict): raise ContractError("inputs must be an object")
        if len(json.dumps(_identity_tree(data), ensure_ascii=True)) > MAX_BYTES * 4:
            raise ContractError("Native input-size limit exceeded")
        if not isinstance(cartridge, str) or cartridge not in OPERATIONS: raise Unsupported("Unknown cartridge")
        if not isinstance(operation, str): raise ContractError("operation must be a string")
        if operation in OPERATIONS[cartridge]: out = OPERATIONS[cartridge][operation](data)
        else: raise Unsupported("Unsupported operation: " + operation)
        envelope.update(execution_status="completed", decision_status=out.get("decision_status", "described"),
                        request_identity=digest({"cartridge": cartridge, "operation": operation, "inputs": data}),
                        run_kind=out.get("run_kind", "reference" if operation in {"describe", "knowledge", "query"} else "analysis"),
                        result=out)
        return envelope
    except Unsupported as exc:
        envelope.update(execution_status="unsupported", error=str(exc))
    except NumericEncodingError as exc:
        envelope.update(execution_status="numeric_encoding_error", error=str(exc))
    except (ContractError, cs.InputError) as exc:
        envelope.update(execution_status="input_error", error=str(exc))
    except (OverflowError, ValueError) as exc:
        # The inherited finite serializer uses ValueError for encoding limits.
        label = "numeric_encoding_error" if "Numeric encoding limitation" in str(exc) or isinstance(exc, OverflowError) else "runtime_error"
        envelope.update(execution_status=label, error=type(exc).__name__ + ": " + str(exc))
    except Exception as exc:
        # Unexpected bugs are software failures, not invalid engineering cases.
        envelope.update(execution_status="runtime_error", error=type(exc).__name__ + ": " + str(exc))
    return envelope
