# Camera evidence questions

Case: DEMO-CAM-D-POWER-BLOCKED

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

Analysis: blocked.

Jitter alone cannot overcome: V-FAST: power: established failure.

V-FAST power: value 11 must satisfy <= 10; source locators are retained in blocker_details.

No jitter-only request is issued as sufficient to improve or add a tied option to this decision.

Synthetic model only; facts are supplied, not independently authenticated.

Cost comparison covers established plans only; unresolved other candidates can still matter.

Representative previews are hypothetical witnesses, not a proof of encoding over a whole region.

Mathematical conditions are not a guaranteed executable configuration. No supplier fact, deployment approval, or hardware qualification was created.

## Boundary derivation


Exact rational domains, hypothetical witnesses, source identities and supplied operating conditions are retained in result.json.
This report uses one captured case. Separate analyze and questions invocations each capture their own inputs; a later command may see a later revision.
