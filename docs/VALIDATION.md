# Validation scope and recorded checks

## Historical 0.2.1-rc.1 checks — 29 September 2026

Checked on macOS 26.6.2 arm64 in separate relocated scratch copies. No frozen build was executed in place or edited. These checks concern packaging and bounded software behavior, not hardware qualification or customer value.

| Check | Actual result |
|---|---|
| Retained application suite on installed CPython 3.9.6 | 28 methods passed; 76 CLI invocations; zero failures/errors. |
| Same retained suite on installed CPython 3.12.14 | 28 methods passed; 76 CLI invocations; zero failures/errors. |
| All ten bundled case-runner cases on Python 3.9.6 | Ten completed, with expected feasible/insufficient/no-feasible statuses and unchanged inputs. |
| README quick start on both interpreters | Passed. All five public outputs match the frozen public outputs byte for byte. |
| Relocation | Passed from paths containing spaces and non-ASCII characters, with both package-local and unrelated working directories. |
| Refusal behavior | Nonempty application output refused unchanged; existing runner batch refused unchanged; escaping batch name rejected. |
| Browser check | Actual generated HTML opened locally in already-installed Chrome. No page errors or HTTP(S) resource requests; no horizontal document overflow at 1440 or 1280 pixels. Top and evidence sections visually inspected. |
| Runtime source identity | Four application modules remain byte-identical to frozen implementation 0.2.1-build1.2. |

The two suite runs are compatibility checks of the same 28-method suite, not 56 independent cases. The full suite also executes generated adapters against emitted configurations, including unknown-variant refusals.

Seven case-runner results are feasible plans. `descriptive_conflict` and `insufficient` return insufficient evidence; `all_blocked` returns no feasible plan. A no-plan analysis is not an application crash.

One browser-check attempt stopped before opening the HTML because the bundled automation browser binary was absent. The check then used already-installed Chrome; nothing was installed. That tooling stop is retained in detached release records and was not an application failure.

Linux, Windows and other Python versions were not executed here. A Windows account without symlink privileges may not run the full path-refusal suite. No OS-wide network isolation test, security certification, hardware run or customer-case validation was performed. Dense report formatting and broader platform coverage are optional follow-up work, not newly added features in this candidate.

Final archive extraction, manifest, privacy and frozen-source preservation checks are recorded in the detached owner-facing release report/receipt. Raw execution logs contain local workspace paths and are deliberately excluded from this distributable.

## Portfolio package 0.2.1

The six Python application/runner files and every retained example/fixture file are byte-identical to 0.2.1-rc.1. The table above records the prior candidate checks, not a claim of new cross-platform coverage. Current clean-extraction quick-start and bundled-check results are recorded in the detached owner handoff and receipt for this exact archive. Those records are excluded from the public payload because they include local execution paths. No new hardware or customer experiment is part of this preparation.
