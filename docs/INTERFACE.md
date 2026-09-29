# Executable contract v1.0

Use Python 3 standard library. The judge supplies a previously unseen case directory with the same record schema.

```
python3 app.py analyze --case /absolute/path/to/case --out /absolute/path/to/new_output
```

Produce `report.json` with these required fields. Extra fields are allowed. IDs and citations must be input-derived. Output JSON must contain no NaN/Infinity. Ordinary case analysis should finish in 30 seconds on a laptop, without a network connection or user input.

```json
{
  "schema_version": "1.0",
  "case_id": "from case.json",
  "status": "feasible_plan | insufficient_evidence | no_feasible_plan",
  "source_review": [
    {"source_id": "input ID", "disposition": "active | superseded | historical | conflicted", "reason": "..."}
  ],
  "evaluations": [
    {
      "camera_id": "...", "variant_id": "...",
      "status": "feasible | infeasible | unknown",
      "metrics": {"mm_per_pixel": null, "bandwidth_MB_s": null},
      "feasible_offset_interval_ms": null,
      "blockers": [], "unknowns": [], "source_ids": []
    }
  ],
  "policy_evaluations": [
    {"camera_id": "...", "policy": "shared | per_variant", "status": "feasible | infeasible | unknown", "reason": "...", "cost_points": 0}
  ],
  "selected_plan": null,
  "evidence_review": [
    {"source_id": "test ID", "flags": [], "reason": "...", "source_ids": []}
  ],
  "impact_chains": [
    {"nodes": ["..."], "edges": [{"from": "...", "to": "...", "basis": "declared | derived", "source_ids": []}], "consequence": "..."}
  ],
  "findings": [
    {"category": "impact | stale_evidence | conflict | missing_evidence | approval_boundary", "statement": "...", "source_ids": [], "locator": "JSON field or other exact locator"}
  ],
  "required_retests": [],
  "limitations": []
}
```

`metrics` may contain more fields; null means unavailable, not zero. A known feasible interval is `[lower, upper]`. Enumerate every candidate × variant and candidate × policy exactly once.

When a plan exists, `selected_plan` has:

```json
{
  "camera_id": "input candidate ID",
  "spec_source_id": "active unconflicted camera source ID",
  "policy": "shared",
  "offset_ms_by_variant": {"actual variant ID": 0.0},
  "firmware_revision": "base revision for shared; a distinct proposed revision for per_variant",
  "cost_points": 0,
  "optimality": "minimum_among_established_feasible_plans",
  "unresolved_cheaper_candidates": [],
  "requires_human_approval": true,
  "deployment_qualified": false
}
```

Every variant must be present. For `shared`, all offsets must be equal. Using the base firmware with an updated shared configuration is allowed; a per-variant adapter requires a new proposed firmware revision. Do not falsify configuration identity to inherit old test evidence.

Evidence flags are a set drawn from:

- `applicable_to_selected_configuration`
- `stale_configuration`
- `insufficient_applicability_data`
- `internally_contradictory`
- `requirement_limit_mismatch`
- `finite_sample_not_guaranteed_bound`
- `no_selected_configuration`

Multiple flags can apply. Explain which fields disagree. With no selected plan, use `no_selected_configuration`; still check internal contradictions, current requirement limits and sample limitations.

For a feasible plan write `proposed_firmware.py` exposing:

```python
def normalize_timestamp(sensor_timestamp_ms, variant_id, plan):
    # Return timestamp plus plan['offset_ms_by_variant'][variant_id].
    ...
```

Unknown variants must raise an explicit error, not silently inherit an arbitrary calibration. The judge will inspect the generated code before execution. Also write the selected plan to `proposed_configuration.json`.

For every case write `engineering_review.html` or `engineering_review.md`, and `revalidation_plan.md`. A recommended plan must be clearly marked proposed, unapproved and not validated on real equipment.

Provide readable errors for invalid input. Do not edit inputs or silently replace absent fields with plausible defaults.
