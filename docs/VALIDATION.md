# Actual integration validation — 0.3.0-rc.1

Author-run local checks; no independent integration approval. Environment: macOS 26.6.2 arm64, CPython 3.9.6 (Clang 21.0.0). No installations, models, services or hardware used. Earlier releases' other interpreter checks do not transfer to this version.

| Check | Actual result / scope |
|---|---|
| Starting archives | v0.2.1 approved SHA-256 and 180 manifest entries; Python CogniMap 0.1.2 SHA-256 and 133 manifest entries verified. All extracted bytes match saved source copies. |
| Published-baseline app suite | 28 methods pass in separate scratch; 76 CLI invocations. |
| Integrated retained app suite | The same 28 methods pass; same 76 CLI invocations. |
| Ten bundled cases | All ten complete; emitted adapters exercised for selected plans and unknown-variant refusals. |
| Baseline regression comparison | All 44 emitted files across ten cases byte-identical. No such claim is made for the deliberately corrected numeric error response. |
| Standalone upstream regressions | Original DecisionQuestionsTests: 16/16; NumericEncodingRegressionTests: 8/8. Separate version and execution from integrated tests. |
| Combined command | 18/18 methods with 51 CLI invocations: actual case folders, exact decimals, renamed IDs, 2/3/4 variants, separate domains, equality/neighbors, blockers/unknowns, U01, supersession, malformed cases, encoding failures, output protection and snapshot isolation. |
| Standalone comparison | 12/12 inner result and normalized envelope matches; metadata and CLI exit differences explicitly documented. Same inherited solver, not independent physics oracle. |
| Demonstrations | Both saved examples are actual outputs from the integrated command on the bundled case folders. |

The final clean-extraction execution and manifest results are recorded in the detached integration receipt. This public validation table records checks actually completed during development. Repeated final runs are reproducibility checks, not additional independent cases. Counts above overlap and must not be added into a single success-rate claim.

No unplanned application/test failure occurred in the first full development suites. Expected negative cases deliberately returned refusals/errors; raw commands and results are retained in the detached local evidence record. No private execution logs or local absolute paths are bundled here.

Remaining limits: no Windows/Linux or other Python execution for this integration; no hardware calibration, supplier guarantee authentication, measured customer outcome, comparative CogniMap study or external independent review. Snapshot capture is not a lock against hostile concurrent file mutation. Local Python is trusted executable code.
