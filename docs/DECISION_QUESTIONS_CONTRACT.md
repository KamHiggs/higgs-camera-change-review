# Integrated camera.decision_questions contract — 0.3.0-rc.1

Origin: Python CogniMap 0.1.2. The operation and threshold algebra are retained. The [upstream contract](DECISION_QUESTIONS_UPSTREAM_CONTRACT.md) is a historical source: its embedded-demo default and separate host instructions do not apply to this application.

## Input and snapshot

`python3 -B app.py questions --case CASE_DIR --camera DECLARED_CAMERA_ID --out FRESH_OUT_DIR`

The existing case loader validates the folder inventory and parses decimal numeric tokens directly as Fractions. An optional internal reader hashes exactly the bytes it parses; a post-capture check rejects a source changed during capture. In-memory copies of this one capture are used for the current decision, source resolution, threshold derivation and hypothetical witnesses. The method never reloads a case for a nested operation. There is no OS transaction/lock; recorded hashes describe captured bytes. Later commands may observe later revisions.

The thin adapter supplies model_id=EC-SYNTHETIC-1.0, case_data and source_records internally. It invents no facts or IDs. Explicit synthetic=false or another schema is unsupported. Unknown fields, costs, availability, conflicts, revisions and source locators survive unchanged. Empty/missing base never falls back to demonstration data. The inherited operation limits (64 source records, 16 variants/candidates, bounded native inputs) remain. These limits are not an untrusted-code sandbox or general hostile-input defense.

## Exact conditional boundaries

Only one missing guaranteed `timestamp_jitter_bound_ms` is considered. For positive-speed variant i:

- a_i = error_limit_i / speed_i - host_jitter_i.
- With nonnegative guaranteed camera jitter j, the offset interval is [-bias_i - a_i + j, -bias_i + a_i - j].
- Per-variant policy: j <= min(a_i).
- Shared policy: j <= [min(-bias_i + a_i) - max(-bias_i - a_i)] / 2.

Equality is included. Negative thresholds have empty nonnegative domains. Zero-speed variants add no interval restriction after required operands are supplied; all-zero speed is unbounded, but the existing guarantee prerequisite remains. Calculations use exact Fractions. None of the seven physical formulas, allowed policies, costs or U01 rules change.

## Result and evidence standard

result.json carries the existing execution envelope and integration metadata, exact derived values, current supported plan/cost, input and source identities, actual source/field/revision, controlling operands/variants, policy domains, conditional cost effects, remaining prerequisites, established blockers and qualified evidence request. explanation.md renders those fields for a reader.

The evidence request requires an applicable guaranteed upper bound for the exact candidate/revision and supplied operating conditions, with authoritative provenance and explicit supersession where applicable. Typical values, finite samples and PASS are insufficient. Source labels do not independently authenticate a guarantee.

The result distinguishes supported, blocked, unsupported and not_needed analysis. It distinguishes creating a first plan, lower modeled cost, equal-cost alternatives, more-expensive alternatives and no target plan. It does not infer probabilities, real prices, general optimal question choice or engineering approval.

One hypothetical witness per exact region runs through the same canonical solver and serialization guard. Virtual sources and selected plans stay labeled hypothetical. Witnesses do not prove finite encoding over an entire region. Only the actually selected witness plan is serialization-checked; unselected alternatives remain mathematics. A zero-only region whose witness fails encoding gets no sufficient guarantee-only request. No executable configuration is emitted by questions.

## Status separation

Malformed input: exit 2. Unsupported analysis/world: exit 3. Current-decision numerical encoding failure: exit 4. Unexpected question-runtime failure: exit 5. Completed supported/blocked/not_needed question analyses: exit 0. A hypothetical encoding failure is preserved in the witness without being mislabeled physical impossibility. The ordinary analyze command keeps successful status/outputs; its necessary numeric error correction is explicitly recorded in CHANGELOG.md.
