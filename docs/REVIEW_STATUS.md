# Review status by version

Main retains the v0.2.1 application with later documentation updates. The evidence-question feature is in the separate **experimental pre-release v0.3.0-rc.1**. Both use a synthetic engineering model; neither is hardware-qualified or production-ready engineering software.

This page supplements the original validation statements. It summarizes preserved author records, Claude's separate execution review and the later Grok report supplied by the project owner. It does not rewrite those records, independently authenticate every reported execution, or claim a new test run. Raw conversations, private execution logs and internal review archives are not distributed here.

## Version identities

| Version | Published source commit | Public references |
| --- | --- | --- |
| v0.2.1 | `9382e4475da66cb82eaec17ef436d770ad42eead` | [Release](https://github.com/KamHiggs/higgs-camera-change-review/releases/tag/v0.2.1), [historical author validation](https://github.com/KamHiggs/higgs-camera-change-review/blob/v0.2.1/docs/VALIDATION.md) |
| v0.3.0-rc.1 | `b1d82bd7e1b0b364b6520278be869c9ab2880f1e` | [Release](https://github.com/KamHiggs/higgs-camera-change-review/releases/tag/v0.3.0-rc.1), [author integration validation](https://github.com/KamHiggs/higgs-camera-change-review/blob/v0.3.0-rc.1/docs/VALIDATION.md), [attribution](https://github.com/KamHiggs/higgs-camera-change-review/blob/v0.3.0-rc.1/ATTRIBUTION.md) |

The table identifies release sources, not the uncaptured historical commit of a reviewer checkout. Current main documentation changes do not move these tags. Packaged preparation-time publication statements remain unchanged; the linked release pages record publication.

## Grok: reported Linux execution of v0.2.1

- Grok reports that the retained **28-method suite passed: 28 tests in 5.608 seconds**. Its checkout lacked `questions` and the 18-method integration suite.
- **CPython 3.12.3 and Ubuntu 24.04.4 x86-64 were observed afterward in the same sandbox**, rather than captured alongside the original execution.
- The original checkout was deleted. Its exact historical commit was not captured with `git rev-parse` during execution.
- Association with `9382e4475da66cb82eaec17ef436d770ad42eead` is retrospective, based on recorded contents and subsequently checked remote refs. It is not a contemporaneous commit pin.
- This is **reviewer-reported Linux execution for the described v0.2.1 checkout**, not Linux validation of v0.3.0-rc.1 and not a general cross-platform support claim.

The report adds evidence to the historical v0.2.1 record. It does not change what the authors actually tested during release preparation or attribute pre-release feature coverage to Grok.

## v0.3.0-rc.1: author testing and separate, nonblind review

The author integration records and Claude's separate execution review cover **macOS 26.6.2 arm64 with CPython 3.9.6**. Earlier v0.2.1 interpreter checks and Grok's later Linux report do not transfer to this integration.

| Evidence | Recorded scope |
| --- | --- |
| Author integration execution | Retained application suite: 28 methods / 76 CLI invocations. Integration suite: 18 methods / 51 CLI invocations. Ten-case regression comparison: 44 byte-identical output files. The linked author validation document retains the separate upstream and comparison checks with their original qualifications. |
| Claude's separate execution review | Replayed the retained 28-method suite / 76 CLI invocations, 18-method integration suite / 51 CLI invocations, ten bundled cases, quick-start commands and both saved demonstrations. Compared 44 output files with v0.2.1 byte for byte. Did not rerun the author's separate upstream 16- and 8-method suites or 12 standalone/adapted comparisons. |
| Claude's additional probes | Original saved result remains **28/29**. One expectation incorrectly predicted `not_needed` for a supplied jitter guarantee above the permitted threshold; `blocked` was the correct result. The explanation is retained separately; the original result is not relabeled 29/29. |

These counts overlap, including repeated coverage across author and reviewer runs. They must not be added into a total of independent cases.

Claude read author reports and saved outputs before executing the review. The package also attributes historical contributions and five review fixtures to Claude. This establishes reviewer-lineage overlap, not evidence that the reviewing session implemented this integration. **The review is separate and nonblind; it is not independent approval.** Its initial inaccurate statement about the attribution was corrected in the preserved review.

Reviewer-harness failures and corrections remain recorded: a missing work directory stopped an initial probe attempt, a correction command failed because of its working directory, and a shell-glob error stopped a regression attempt before application execution. The command log was transcribed afterward from session tool output; it is distinct from machine-written test records and saved outputs. Individual probe stdout/stderr were not preserved.

The recorded closure conclusion is:

> The experimental release has author testing and a separate, nonblind execution review with preserved supporting records. No release-blocking defect was found in the examined synthetic cases.

This does not establish hardware qualification, supplier-guarantee authenticity, deployment approval, measured customer savings or CogniMap superiority. No Linux, Windows or additional-interpreter execution is established for this integrated pre-release.

## Review the intended version

Use the [explicit pre-release checkout and commands](../README.md#review-the-evidence-question-pre-release). Record the commit/tag, Python version, operating system, actual command, exit status and saved output at execution time. Preserve failures and distinguish application failures from reviewer-harness failures. No completed application suites were rerun for this documentation update.
