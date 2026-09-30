# Higgs Camera Change Review

**Created and led by Kamden Higgs.** An experimental Higgs AI project developed through AI-assisted implementation and adversarial review.

Evaluate a camera replacement, understand the uncertainty, and identify evidence that could change the decision.

This offline Python application evaluates a supplied synthetic case against seven engineering constraints. Its new **Python CogniMap-derived evidence-question command** identifies the applicable guaranteed jitter bound a candidate would need, the policies that bound could support, and blockers that a jitter answer cannot resolve. It runs deterministically without an AI model, account, network service or external Python package.

**Version 0.3.0-rc.1 is a local release candidate, not published by this integration task.** The existing [v0.2.1 project](https://github.com/KamHiggs/higgs-camera-change-review) remains unchanged. This is synthetic software, not hardware-qualified engineering software.

## See the demonstrations

These are saved outputs from actual local executions, not a hosted or running service:

- [Existing engineering review](docs/example_review.html): CAM-B, per-variant offsets, five synthetic cost points.
- [A guarantee could change the decision](docs/demonstrations/public/explanation.md): an applicable CAM-D jitter guarantee at or below 0.4 ms could support a shared-policy plan at two points.
- [A different blocker prevents that conclusion](docs/demonstrations/blocked/explanation.md): CAM-D is stipulated to consume 11 W against a 10 W budget. A jitter answer alone is insufficient.

Typical values, finite samples and a saved PASS do not establish a guarantee. Cost points are not prices or monetary savings. These analyses do not obtain supplier evidence or authorize deployment.

## Run your case

Use an existing CPython 3.9+ installation. This candidate was actually checked on macOS arm64 with CPython 3.9.6; other platforms/versions were not executed for this integration. Python is not bundled.

From the extracted `higgs-camera-change-review-0.3.0-rc.1` folder:

```sh
python3 -B app.py analyze --case examples/public_camera_change --out outputs/first-review
python3 -B app.py questions --case examples/public_camera_change --camera CAM-D --out outputs/first-questions
python3 -B app.py questions --case examples/blocked_camera_change --camera CAM-D --out outputs/blocked-questions
```

`analyze` retains its existing case-folder interface and writes `engineering_review.html`, `report.json` and `revalidation_plan.md`, plus a proposed adapter/configuration when justified by the model and its serialization check.

`questions` uses the same case-folder format and a declared candidate ID. It writes `result.json` and `explanation.md` only. No request-format conversion or duplicate case entry is needed. Every nested analysis uses the single case snapshot captured by that command. Separate command invocations may see separate revisions; compare the source identities and preserve your input case.

Choose a fresh output directory. Existing nonempty outputs and input-overlapping paths are refused. The new command also rejects symlinked output parents. For another working directory use absolute paths to `app.py`, `--case` and `--out`, quoting paths containing spaces.

Prepare your own copied case using [input preparation](docs/INPUT_PREPARATION.md). Input preparation is manual; there is no PDF/OCR ingestion or automatic interpretation of manufacturer documents. Only the declared synthetic world is supported by `questions`.

## Read a result accurately

- `analyze`: exit 0 includes a completed `feasible_plan`, `insufficient_evidence` or `no_feasible_plan`; physical no-plan is not a software error.
- `questions`: supported, blocked or not_needed analysis exits 0. Unsupported single-answer analysis exits 3 and retains the missing prerequisites. A current-decision numerical encoding failure exits 4. A failed hypothetical witness remains labeled inside an otherwise completed conditional analysis.
- Malformed inputs return 2. Numerical encoding failure returns 4 without a justified executable configuration. Unexpected question-runtime failure returns 5.
- Exact derived values use `{"$rational":["numerator","denominator"]}` in question results. The existing finite JSON serializer is still used for proposed configurations and rechecked against its existing tolerance.

See the [integration contract](docs/DECISION_QUESTIONS_CONTRACT.md), [derivation and code trace](docs/COGNIMAP_INTEGRATION.md) and [limitations](docs/KNOWN_LIMITATIONS.md).

## Run the bundled checks

```sh
python3 -B verify_package.py
python3 -B test_app.py
python3 -B test_questions.py
python3 -B run_cases.py --batch local-check public devised_shared zero_radius mixed_zero_speed descriptive_conflict bias_equalized jitter_known all_blocked insufficient own_boundary
```

The retained application suite has 28 methods; the combined-command suite has 18 methods with 51 CLI invocations. They exercise overlapping behavior, not 46 independent demonstrations. The ten-case runner also executes the emitted synthetic adapters. Test runs create local `records/`, `test_runs/` and `outputs/`; those logs are excluded from this package. Full tests require permission to create local symlinks. Choose a fresh batch name for repeats. See [actual validation scope](docs/VALIDATION.md).

## How this was built

Kamden Higgs directed the project, requirements, review coordination and release decisions. The original camera application followed a supplied CogniMap/design handoff. Python-native methods were developed with Solara / ChatGPT and Codex assistance, then the existing camera-specific method was integrated here. No model is called by the application. This shows reuse of executable methods with their rules, provenance and qualifications; it does not establish superiority over another well-engineered package.

[Attribution](ATTRIBUTION.md), [provenance](PROVENANCE.json) and [change log](CHANGELOG.md) identify the sources and changes. No provider endorsement or independently reviewed integration is implied.

## License and release status

The existing [MIT notice](LICENSE) names Kamden Higgs. See [license status](LICENSE_STATUS.md) for the scope of the retained notice and new candidate. Publication of this exact candidate requires separate owner approval. `SHA256SUMS.json` records package bytes, excluding itself; it is not an approval or digital signature.
