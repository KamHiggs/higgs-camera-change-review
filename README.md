# Higgs Camera Change Review

**Created and led by Kamden Higgs.**  
An experimental Higgs AI project developed through AI-assisted implementation and adversarial review.

An offline engineering-change assistant demonstrated through a synthetic industrial-camera replacement scenario. It compares replacement options, checks engineering constraints and test-evidence applicability, and produces a review and revalidation plan.

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

Version 0.2.1 is prepared locally for owner publication approval. No public repository, release date, hosted demo or support service is claimed. `SHA256SUMS.json` records package file identities, excluding itself; it is not a signature or publication approval.
