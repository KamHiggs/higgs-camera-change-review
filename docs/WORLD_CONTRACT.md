# Synthetic world contract v1.0

These rules define this challenge completely. They are simplified assumptions for a simulator, not validated engineering formulas for real equipment.

## Authority and records

`case.json` names the variant IDs, candidate camera IDs, source inventory and objective. Every source is a JSON object with `source_id`, `kind`, `status`, `revision`, `supersedes` and `data`.

- `status: active` supplies current facts. `historical` and `superseded` records can explain the lineage but cannot override active facts.
- An active record explicitly superseding another record retires that predecessor for the same subject. Revision numbers and file modification dates alone do not grant authority.
- Two unretired active records for the same subject that disagree create an unresolved conflict. Do not pick the larger revision number, nicer answer or last file encountered.
- Compare conflicts at the field level. Fields on which all active records agree remain usable; a differing leaf (including a variant-specific value) is unknown until resolved. A known failure in an agreed field still rules a candidate out. Report all implicated source IDs.
- A missing/null guaranteed numerical bound is unknown. `typical`, sample observations and a model-written PASS do not replace a guaranteed bound.
- Provenance IDs and paths must come from the input inventory. Do not invent sources.

## Allowed change and cost

The discontinued baseline camera cannot be selected. Choose ONE available replacement camera model for the entire product family. Both variants must use that model. Replacing lenses, relaxing requirements, reducing demanded frame rate, changing conveyor speed, inventing hardware or using different cameras for different variants is outside the allowed change.

Only these timestamp policies are allowed:

- `shared`: one finite real offset in milliseconds for every variant; policy cost 0.
- `per_variant`: one finite real offset per variant; policy cost 3.

Total migration cost = selected camera's `migration_cost_points` + policy cost. These are synthetic points, not dollars. Minimize this total among feasible plans. Any equal-cost plan satisfying all constraints is acceptable. Do not reward a more expensive plan simply because it is more elaborate. Do not turn a non-existent guaranteed bound into zero.

## Predicted constraints

Use the demanded frame rate from the variant. Use guaranteed bounds from the selected active camera specification. All listed constraints must hold, inclusive at their limits; numerical grading tolerance is 1e-9.

1. `max_fps >= required_fps`.
2. `field_of_view_mm / image_width_px <= max_mm_per_pixel`.
3. `image_width_px * image_height_px * bytes_per_pixel * required_fps / 1_000_000 <= link_capacity_MB_s`. MB is decimal; compression is not available.
4. `power_W <= power_budget_W`.
5. `supply_voltage_V` must lie within the camera's inclusive `supply_range_V`.
6. The camera's `transport` must equal the variant's `transport`.
7. Worst-case registration error in millimetres is:

   `speed_m_s * (abs(timestamp_bias_ms_by_variant[variant_id] + offset_ms) + timestamp_jitter_bound_ms + host_jitter_bound_ms)`

   This must be `<= max_registration_error_mm`. In this synthetic world the units work because one m/s times one ms equals one mm.

The reported timestamp equals event time plus bias; the firmware adds the chosen offset. Thus a positive bias is cancelled by a negative offset. This sign convention is contractual.

For a known camera/variant, feasible offsets form a closed interval centred on negative bias. Its radius is:

`max_registration_error_mm / speed_m_s - timestamp_jitter_bound_ms - host_jitter_bound_ms`.

A negative radius is infeasible. A shared policy requires a non-empty intersection of all variant intervals. A per-variant policy requires each interval to be non-empty independently. This interval relation is public so all builders can implement and test the same physics.

## Unknown versus impossible

Evaluate known constraints even if another field is unknown. A known failure is sufficient to reject a camera/variant; an unrelated missing field must not hide that failure.

Per-candidate/per-variant feasibility means whether some allowed offset could work, before imposing the shared-policy restriction. Policy feasibility then determines whether a single shared offset suffices or per-variant compensation is necessary.

- `feasible`: all required bounds/facts are known and some allowed offset can satisfy this variant.
- `infeasible`: at least one established constraint cannot be satisfied by an allowed offset.
- `unknown`: no established constraint rules it out, but missing/conflicting facts prevent a feasibility determination.

If a feasible whole-family plan exists, recommend a lowest-cost feasible plan. Disclose any unresolved candidate that could be cheaper; do not call the recommendation a proven global optimum over unresolved facts. If no feasible plan exists but at least one candidate is not ruled out for the family, use `insufficient_evidence`. Use `no_feasible_plan` only when every candidate has an established family-level blocker.

## Test evidence and approvals

Saved `test_record` sources include a configuration, metric, measurements, limit and claimed result. Assess these independently:

- A prior PASS is not applicable to a different variant, camera, spec source, firmware revision, offset policy or selected offset. Use the configuration fields present in the record; equality requires every listed applicability field to match. Missing applicability fields mean insufficient applicability evidence.
- A claimed PASS with any recorded observation above its recorded limit is internally contradictory, even if the test is also stale.
- A test's limit must also be checked against the current requirement. A PASS against a looser old limit does not establish current compliance.
- A finite sample can be an observation of performance, but cannot establish the guaranteed jitter bound required by the design model.
- A feasible calculation is a prediction. It does not manufacture a new hardware test, qualify deployment, grant an approval or establish field safety.

Any changed camera requires revalidation for both variants: timing, resolution, throughput, power/interface compatibility and the proposed timestamp adapter. Identify obsolete evidence and the specific new configuration to test. Retain pre-change records.

## Dependency interpretation

The supplied dependency graph is a starting point, not an exhaustive answer. Report changed source/component → parameter/behavior → affected requirement → invalidated evidence chains. Label an edge `declared` if supplied as a graph edge; label it `derived` if established by one of the public formulas or cited source facts. Distinguish potential impact from a calculated violation.

The product must never interpret a source document or proposed plan as permission to deploy or rewrite the source records.
