# Higgs Camera Change Review

An offline engineering-change assistant demonstrated through a synthetic industrial-camera replacement scenario. It compares replacement options, checks engineering constraints and test-evidence applicability, and produces a review and revalidation plan.

**Created and led by Kamden Higgs.** An experimental Higgs AI project developed through AI-assisted implementation and adversarial review.

## InvenTree integration demonstration

**When the inputs change, know which decisions need revisiting.** The experimental InvenTree integration preserves a camera assessment, flags it when relevant inventory declarations change, and exports a record that can be rechecked offline with its matching verifier.

Start with the [recorded three-screen walkthrough](https://github.com/KamHiggs/higgs-camera-change-review/blob/inventree-v0.1.3-correction.1/docs/DEMONSTRATION.md), the [integration source and installation guide](https://github.com/KamHiggs/higgs-camera-change-review/tree/inventree-v0.1.3-correction.1), or the [experimental integration release](https://github.com/KamHiggs/higgs-camera-change-review/releases/tag/inventree-v0.1.3-correction.1). This is a separate `0.1.3+correction.1` integration lineage; the standalone camera versions below are unchanged.

The demonstrated verification accepts the exported record while its camera recommendation remains blocked. Synthetic requirements, manual setup, nonblind review and known limitations remain; see [integration review status](https://github.com/KamHiggs/higgs-camera-change-review/blob/inventree-v0.1.3-correction.1/docs/REVIEW_STATUS.md). No hosted interactive service or hardware approval is claimed.

## Choose the version

- **Default branch (`main`):** the retained v0.2.1 application, with subsequent documentation updates. A normal default-branch clone does **not** include `questions`.
- **[v0.3.0-rc.1 experimental pre-release](https://github.com/KamHiggs/higgs-camera-change-review/releases/tag/v0.3.0-rc.1):** adds `questions` — **“What evidence could change this decision?”** For supported synthetic cases, it calculates the guaranteed jitter conditions a candidate must satisfy and identifies established blockers that jitter evidence alone cannot resolve.
- **Both versions use a synthetic model and are not hardware-qualified or production-ready engineering software.**

Start with the two readable, saved demonstrations:

1. [A guarantee could change the decision](https://github.com/KamHiggs/higgs-camera-change-review/blob/v0.3.0-rc.1/docs/demonstrations/public/explanation.md): an applicable CAM-D jitter guarantee at or below 0.4 ms could support a two-point plan instead of the current five-point plan. These are synthetic cost points, not measured savings.
2. [An established power blocker](https://github.com/KamHiggs/higgs-camera-change-review/blob/v0.3.0-rc.1/docs/demonstrations/blocked/explanation.md): 11 W exceeds a 10 W budget, so jitter evidence alone cannot make CAM-D suitable.

[Download the approved pre-release ZIP](https://github.com/KamHiggs/higgs-camera-change-review/releases/download/v0.3.0-rc.1/higgs-camera-change-review-0.3.0-rc.1.zip) · [Tagged source](https://github.com/KamHiggs/higgs-camera-change-review/tree/v0.3.0-rc.1) · [Tagged README](https://github.com/KamHiggs/higgs-camera-change-review/blob/v0.3.0-rc.1/README.md) · [Preserved v0.2.1 release](https://github.com/KamHiggs/higgs-camera-change-review/releases/tag/v0.2.1)

The demonstrations are saved outputs, not a hosted interactive service. [Review the pre-release explicitly](#review-the-evidence-question-pre-release) or read the [version-specific review status](docs/REVIEW_STATUS.md). The operating instructions below otherwise describe the retained v0.2.1 application.

## The problem this example explores

Replacing a camera can change timing, image resolution, throughput and power requirements. A previous test marked “PASS” may describe an old configuration or a different limit. This example asks: which replacement is supported by the current evidence, what is still unknown, and what needs to be tested again?

## What it does

- Reads an explicit inventory of JSON requirements, camera specifications, revisions and saved test records.
- Evaluates seven constraints: timing, resolution, frame rate, throughput, power, voltage and transport.
- Compares shared and per-variant timestamp offsets, identifies established failures and missing evidence, and ranks established feasible options with known synthetic costs.
- Checks whether saved test evidence applies to the proposed configuration.
- Writes a local HTML review, structured results and a revalidation plan. When justified, it also emits a proposed timestamp adapter and configuration.

It is a deterministic Python application. It does not call an AI model or require an account, API key, network connection or external Python package at runtime.

## See the example first

Download and unzip the approved release package. Open `docs/example_review.html` from the extracted folder in your browser. It is a saved, self-contained report from the synthetic public case; it does not run an interactive service.

The example selects CAM-B with per-variant offsets of −4 and −2.5 ms while explaining why old test evidence does not qualify that proposal. Costs are synthetic points, not prices. See the [demonstration guide](docs/DEMO.md).

## Run it locally

Use an existing CPython 3.9 or newer installation. Actual checked environments and platform limitations are in [validation](docs/VALIDATION.md).

In a terminal, change into the extracted `higgs-camera-change-review-0.2.1` folder, then run:

```sh
python3 -B app.py analyze --case examples/public_camera_change --out outputs/first-review
```

Open `outputs/first-review/engineering_review.html`. The folder also contains `report.json` and `revalidation_plan.md`, plus `proposed_configuration.json` and `proposed_firmware.py` when a plan is supported. These are proposals, not deployment approval.

Use a new output name for each run. Existing nonempty outputs and paths overlapping the input case are refused. To run from elsewhere, use absolute paths to `app.py`, the case and the output, quoting paths containing spaces. If your Python launcher is `python` or `py -3`, substitute it for `python3`; those alternatives do not imply Windows was tested.

## Run the bundled checks

From the extracted folder:

```sh
python3 -B test_app.py
python3 -B run_cases.py --batch demo-check public devised_shared zero_radius mixed_zero_speed descriptive_conflict bias_equalized jitter_known all_blocked insufficient own_boundary
```

The first command runs the retained 28-method suite. The second runs ten bundled synthetic cases. They create `records/`, `test_runs/` and `outputs/` locally; these generated records are not part of the release. Choose a new batch name for a repeat. Both commands return nonzero when their checks fail. The full suite requires permission to create file/directory symlinks.

## Review the evidence-question pre-release

Use an existing CPython 3.9+ installation. The integrated pre-release's recorded author and separate-review executions cover macOS arm64 with CPython 3.9.6; the later reported Linux run concerns v0.2.1 only. See [review status](docs/REVIEW_STATUS.md).

Clone the **tag**, rather than the default branch, into a new directory:

```sh
git clone --branch v0.3.0-rc.1 --single-branch https://github.com/KamHiggs/higgs-camera-change-review.git higgs-camera-change-review-0.3.0-rc.1
cd higgs-camera-change-review-0.3.0-rc.1
git rev-parse HEAD
```

The expected commit is `b1d82bd7e1b0b364b6520278be869c9ab2880f1e`. A detached HEAD is expected when checking out this tag. Stop and identify any mismatch before attributing results to this release.

**The following commands belong to that pre-release checkout only**, as documented in its [README](https://github.com/KamHiggs/higgs-camera-change-review/blob/v0.3.0-rc.1/README.md):

```sh
python3 -B app.py analyze --case examples/public_camera_change --out outputs/first-review
python3 -B app.py questions --case examples/public_camera_change --camera CAM-D --out outputs/first-questions
python3 -B app.py questions --case examples/blocked_camera_change --camera CAM-D --out outputs/blocked-questions
```

`analyze` writes the local engineering review; `questions` writes `result.json` and `explanation.md`. Use fresh output directories. The application and integration test commands for this checkout are:

```sh
python3 -B test_app.py
python3 -B test_questions.py
```

These are the retained 28-method application suite and the 18-method integration suite. Their coverage overlaps; do not sum them as independent demonstrations. Tests create local records and require permission to create symlinks. `questions` and `test_questions.py` are absent from main's retained v0.2.1 implementation.

For a future review, capture **at execution time** the tag and checked-out commit, Python version, operating system, actual command, exit status, and saved output. Keep unsuccessful attempts and reviewer-harness corrections. This is guidance for future execution; no application tests were rerun for this documentation update.

## Important limitations

This is an experimental prototype of a simplified engineering model, not a hardware-qualified product. Applying it to a real system requires engineering judgment and explicit approval. Input preparation is manual: there is no PDF/OCR ingestion, generalized unit conversion or automatic interpretation of manufacturer documents.

Copy the example before preparing a case. Follow [input preparation](docs/INPUT_PREPARATION.md), the [world contract](docs/WORLD_CONTRACT.md) and [output interface](docs/INTERFACE.md). The latter documents retain historical challenge terminology; references to a judge do not create an approval authority.

U01 remains: conflicting active camera records, including descriptive-only disagreements, can prevent selecting a specification identity even when agreed physical values remain usable. Read [all known limitations](docs/KNOWN_LIMITATIONS.md). Hardware performance, customer savings and superiority of the development method are not established by these synthetic checks.

A completed analysis returns exit 0 for `feasible_plan`, `insufficient_evidence` or `no_feasible_plan`. Input/analysis errors return exit 2. A no-plan result is not a crash.

## How this was built

Kamden Higgs directed the project, requirements, coordination of design and reviews, and release decisions. A supplied CogniMap/design handoff guided AI-assisted implementation and adversarial review. Codex assisted implementation; the design lineage records contributions attributed to Claude, Gemini, DeepSeek and Grok with differing coverage. This does not imply Kamden hand-wrote every line, provider endorsement, or review of changes a reviewer did not inspect.

See [attribution](ATTRIBUTION.md), [provenance](PROVENANCE.json) and the [change log](CHANGELOG.md). Detailed private conversations and the internal development archive are excluded.

## License and release status

MIT — see [LICENSE](LICENSE) and [license status](LICENSE_STATUS.md). Copyright notice: © 2026 Kamden Higgs. Contribution records do not establish exclusive copyright in every generated element.

This repository and the [v0.2.1](https://github.com/KamHiggs/higgs-camera-change-review/releases/tag/v0.2.1) and [v0.3.0-rc.1](https://github.com/KamHiggs/higgs-camera-change-review/releases/tag/v0.3.0-rc.1) experimental pre-releases are public. No hosted interactive demo or support service is claimed.

Main is now a documentation-updated tree with the retained v0.2.1 application; it is **not byte-identical to the historical release payload**. Its `SHA256SUMS.json` covers the current distributable files, excluding itself. Tagged packages retain their original bytes, manifests and preparation-time statements about pending publication; the release pages record publication. The retained `VERSION` file contains the preparation label `0.2.1-rc.1`; use the Git tag/commit and release page to identify a published version. A hash manifest is not a signature or approval.

The [review-status summary](docs/REVIEW_STATUS.md) supplements the historical validation record without changing it.
