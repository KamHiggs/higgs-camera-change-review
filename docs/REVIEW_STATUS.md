# Review and execution status

This experimental integration has author testing, a separate nonblind execution review, and a recorded demonstration of the matched correction build. No blocker was found for the examined bounded local demonstration. This is not independent approval or a general security/correctness certification.

| Evidence class | Actual scope | Qualification |
|---|---|---|
| Codex correction-author execution | 36 baseline expectations; corrected parser/view sequence: 36 checks across 18 in-process requests; portable checks: 16 assertions across seven CLI invocations, one synthetic assessment and one receipt fault; 25 packaging checks and recorded quick-start | Overlapping counts; not independent cases. Earlier full A–K campaign belongs to original v0.1.3. |
| Claude separate nonblind review | 18 parser cases per build; copied-host in-process request routing: 38 requests per build at DEBUG false plus nine per build at DEBUG true; 16 CLI executions and one receipt fault | Prior lineage overlap. Reviewed builder records first. Not a fresh installation or browser run in that review. |
| Claude subsequent demonstration | Fresh offline venv, exact wheel installed, 25/25 imported package files matched; real browser workflow; two exports; separate matching verifier executed on blocked export | Copied synthetic database, superuser, one Mac/CPython 3.12.14. First export and in-host verification buttons were not verified in that run. |
| Public preparation | Archive/member identities, source-byte comparisons, export hashes, public-file/privacy inspection, documentation/path checks and final packaging | No application tests, installations, services or new demonstrations during preparation. |

## Review correction retained: C06 and C09

Claude's original correction-build host cases reused an original-v0.1.3 record. The corrected verifier refused that record at `CONTRACT_IDENTITY` before semantic verification. Therefore:

- C06, the 4,300-digit integer, parses and opens in both builds. Semantic refusal was observed only in the original build. Corrected-build semantic behavior for a matching-build C06 record remains untested.
- C09, `1e999`, parses and makes opening return HTTP 500 in both builds. The original verifier reached `SUMMARY_MISMATCH`; the corrected build stopped at identity. Corrected-build semantic behavior for a matching-build C09 record remains untested.
- Oversized integer cases (4,301 and 5,000 digits) refuse earlier at parsing in the corrected build. That result still supports the scoped V13-01 correction. V13-02 documentation of the canonical receipt matches the examined behavior.

The original review was not rewritten; its detached correction note is identified in [source identities](SOURCE_IDENTITIES.json). Do not summarize C06/C09 as newly demonstrated semantic refusals in the correction build.

## Unsuccessful checks and reviewer mistakes

The builder retained an initial temporary wheel missing `LICENSE_REVIEW.md`, then rebuilt the final wheel with the notice. The final wheel distributed here is the reviewed artifact.

Claude's C03 history check initially matched a healthy record's reused ID and produced a false positive; history counts and exclusion diagnostics corrected the interpretation. A zero-match `grep` exit and a pre-run expression cleanup are recorded harness events, not product failures. The prior review missed the stale module-version label and float-overflow opening case.

These accounts are a public summary of preserved records, not raw tool logs or a new replay. Machine-written verification receipt/comparison files included here remain distinct from reviewer prose and this summary. Detailed private workspace records remain local.

Publication does not close open observations or create customer, hardware or regulatory validation.
