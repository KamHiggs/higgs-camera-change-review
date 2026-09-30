# Implementation and rule trace

`app.py questions` -> `questions_cli.load_snapshot` -> canonical `sources.load_case` -> explicit in-memory base -> `camera_cognimap.execute("camera", "decision_questions", ...)` -> `decision_questions.decision_questions`.

The current decision and hypothetical witnesses call `camera_runtime.analyze_memory`, also used by `app.py analyze`. Both share the sole root engine.py, sources.py and reporting.py. There is no second camera_core fork.

- decision_questions.py is copied from Python CogniMap 0.1.2 with imports changed to the canonical root modules only.
- camera_cognimap.py extracts exact validation/digest, source preparation, supersession bound, evaluation, simulation and dispatch helpers. It retains their API names. It removes embedded cases, shared power, guided practice, graph queries and generalized host operations from this camera application.
- Its _camera_prepare requires all base fields. No fallback facts are included. Metadata keeps cartridge version 0.1.2 and reports integration application version 0.3.0-rc.1 separately.
- camera_runtime.py adapts the existing 0.1.1/0.1.2 bridge imports and centralizes its typed NumericEncodingError. Serializer range failures receive that same numeric category. Both command paths use the unchanged serializer and 1e-9 serialized-plan recheck tolerance.
- sources.load_case has one optional internal read callback to capture input byte hashes. Its default behavior, source authority, validation and exact parser remain. The engineering solver and reporting modules are byte-identical to v0.2.1.
- New case-folder CLI statuses are deliberately more informative than the standalone host's exit 0 for a completed unsupported conditional analysis. Its inner result and request identities match on the 12 compared inputs. The outer integration source-byte metadata replaces reference-context knowledge_identity and standalone-host runtime identity. Neither is an approval.

| Rule | Canonical implementation / qualification |
|---|---|
| R-AUTH, R-U01 | sources.resolve_sources; explicit supersession, consensus, conservative unconflicted scalar identity |
| R-FPS, R-RES, R-BW, R-POWER, R-VOLT, R-TRANSPORT, R-TIME | engine.evaluate; original seven constraints |
| R-SELECT | engine.select_plan; minimum among established feasible cost-comparable options |
| R-EVIDENCE | engine.evidence_review; applicability, contradiction, changed limits and samples remain distinct |
| R-SERIAL | camera_runtime.recheck_serialized_plan; finite output check, not physical epsilon |
| R-SIM | camera_cognimap.camera_simulate; virtual assumptions and hypothetical labels |

Boundaries and exact formulas are in DECISION_QUESTIONS_CONTRACT.md. Independent arithmetic expectations were recorded before implementation in INTEGRATION_EXPECTATIONS.md. Development expectations and comparisons are not blinded independent reviews.

Actual upstream checks replayed without modifying their tests: tests/test_decision_questions.py, DecisionQuestionsTests, 16 methods; tests/test_numeric_error_regression.py, NumericEncodingRegressionTests, eight methods, from archive SHA-256 5dc7cebd6e37847787fe44b42eeded803dd8edb78a2fdd5de31467c589694eb9. They validate the standalone source package, not automatically this integration. The separate 18-method test_questions.py exercises the combined application. Provenance includes the original file hashes and names. The complete internal upstream archive is intentionally not distributed recursively here.
