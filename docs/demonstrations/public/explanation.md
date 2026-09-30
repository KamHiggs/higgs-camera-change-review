# Camera evidence questions

Case: PUBLIC-01

**Conditional synthetic analysis. Not deployment approval.**

## Current supported decision

completed / feasible_plan

Selected CAM-B, per_variant, 5 synthetic cost points.

## Target evidence

Camera: CAM-D
Requested field: /data/timestamp_jitter_bound_ms
Source revision: 1

- CAM-D-R1: sources/CAM-D-R1.json#/data/timestamp_jitter_bound_ms (requested /data/timestamp_jitter_bound_ms)

## Conditional result

Candidate: CAM-D. Current decision: feasible_plan.

Analysis: supported.

shared: 0 <= guaranteed jitter <= 2/5 ms, inclusive; cost 2 synthetic points; if feasible: reduce established cost.

per_variant: 0 <= guaranteed jitter <= 2/5 ms, inclusive; cost 5 synthetic points; if feasible: add equal cost alternative.

j = 0 ms: reduce established cost; best target policy shared, 2 points. Conditional mathematics only.

0 < j < 2/5 ms: reduce established cost; best target policy shared, 2 points. Conditional mathematics only.

j = 2/5 ms: reduce established cost; best target policy shared, 2 points. Conditional mathematics only.

2/5 < j ms: no target plan. Conditional mathematics only.

Ask: Obtain an applicable guaranteed upper bound in ms for CAM-D (CAM-D-R1), covering every listed variant operating condition. Compare it with the exact policy domains above. A typical value, finite observations or a PASS statement will not establish this guarantee. Preserve the specification revision, provenance and any explicit supersession; then rerun the ordinary solver and its finite-encoding checks.

Synthetic model only; facts are supplied, not independently authenticated.

Cost comparison covers established plans only; unresolved other candidates can still matter.

Representative previews are hypothetical witnesses, not a proof of encoding over a whole region.

Mathematical conditions are not a guaranteed executable configuration. No supplier fact, deployment approval, or hardware qualification was created.

## Boundary derivation

- V-SLOW: speed=2/5 m/s; error limit=2/5 mm; host jitter=1/10 ms; bias=0 ms; timing allowance=9/10 ms.
  - CAM-D-R1#/data/timestamp_jitter_bound_ms
  - CAM-D-R1#/data/timestamp_bias_ms_by_variant/V-SLOW
  - REQ-SLOW#/data/speed_m_s
  - REQ-SLOW#/data/max_registration_error_mm
  - REQ-SLOW#/data/host_jitter_bound_ms
- V-FAST: speed=2 m/s; error limit=1 mm; host jitter=1/10 ms; bias=0 ms; timing allowance=2/5 ms.
  - CAM-D-R1#/data/timestamp_jitter_bound_ms
  - CAM-D-R1#/data/timestamp_bias_ms_by_variant/V-FAST
  - REQ-FAST#/data/speed_m_s
  - REQ-FAST#/data/max_registration_error_mm
  - REQ-FAST#/data/host_jitter_bound_ms

shared controls: {"lower_controlling_variants": ["V-FAST"], "upper_controlling_variants": ["V-FAST"]}

per_variant controls: {"limiting_variants": ["V-FAST"]}

Exact rational domains, hypothetical witnesses, source identities and supplied operating conditions are retained in result.json.
This report uses one captured case. Separate analyze and questions invocations each capture their own inputs; a later command may see a later revision.
