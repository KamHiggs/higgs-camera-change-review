# Assurance and acceptance contract — 0.1.3

Three separate identities are emitted: `verifier_software_version` identifies the dispatcher, `assessment_format_version` identifies the declared record layout, and `assurance_contract` identifies the verified semantic guarantee. `historical_verification.executing_verifier_version` identifies the actual executor; archived executors carry their pinned archive SHA-256. A format label does not authenticate origin or creation time.

`historical_verification` is retained even when `acceptance` fails. `recipient_requirement` comes from the CLI argument or operator host policy, never the record. The frozen explicit matrix in `COMPATIBILITY_MATRIX.json` controls satisfaction; there is no numeric version ordering. `HIGGS_REQUIRED_ASSURANCE` sets the host minimum (default D013); supported request overrides must explicitly satisfy that minimum. Host HTTP 200 means the verification report is available; clients must inspect acceptance. Errors in a lowering request return controlled 400.

CLI exits, in precedence order:

| Exit | Meaning |
|---|---|
| 1 | Verification or receipt persistence failed |
| 6 | Historical verification available but required contract unsupported |
| 3 | Decision level requested but only legacy engine reproduction available |
| 5 | Requested verification succeeded; external recipient requirement omitted |
| 4 | Requested verification succeeded; required assurance not satisfied |
| 0 | Requested verification and external assurance satisfied; receipt saved |

A combined failure uses the earlier rule. For example a v0.1.0 record requested at decision level returns 3 even if its engine assurance satisfies an engine requirement. JSON retains both outcomes.

Engine-only reproduction does not check the recorded decision chain or human summary. Full current decision verification checks raw snapshot → typed inputs → mapper projection → pinned engine results → structured summary → deterministic SUMMARY.md, plus coverage and allowed format. Optional `ancillary/operator-note.txt` is byte-covered, not semantically verified. Exact byte coverage does not confer authority, authorship or source truth. Ancillary approval files are forbidden by 0.1.2/0.1.3 format, not by older contracts.

## Supported JSON boundary

Each consumed assessment JSON document (including the manifest and historical preflight) is bounded to 4,194,304 bytes and 64 container levels, with the root container at depth 1. A nonrecursive lexical scan respects strings/escapes before JSON parsing. Supported parser recursion failures become `ASSESSMENT_STRUCTURE_LIMIT_EXCEEDED`; malformed/UTF-8 failures are structured refusals. Integer literals rejected by the interpreter's configured integer-string conversion limit become `MALFORMED_ASSESSMENT` (HTTP 400 at direct record access). This build does not change that interpreter limit; the focused checks used CPython 3.12 with its 4,300-digit limit. An over-limit number may be valid JSON syntax but outside this parser's supported input. This is not an arbitrary-depth, whole-directory, archive-bomb or filesystem-security guarantee. Record bytes are not repaired or removed.

## Receipt recognition

Receipt payloads have type `HIGGS_VERIFICATION_RESULT_CONTENT`, state `CONTENT_ONLY`, and a finality rule. **Only `<run-root>/VERIFICATION_RESULT.json` is the current dispatcher's receipt.** For CLI use, `<run-root>` is the exact directory supplied to `--out`; for host use it is the particular verification-run directory identified by the response. Do not discover it by recursively searching for a filename or by taking the first successful verdict.

Check that this exact root file contains complete JSON with `record_type: HIGGS_VERIFICATION_RESULT_CONTENT` and `record_state: CONTENT_ONLY`, then read its `historical_verification`, `recipient_requirement` and `acceptance` together. Root-file existence alone does not establish acceptance. `.verification-result.tmp`, partial bytes and copied snippets are not the current dispatcher receipt. Current dispatcher stored payloads never contain `receipt_saved: true` or `final: true`.

`<run-root>/historical-result/VERIFICATION_RESULT.json` is an unchanged historical executor's child output. It can truthfully report its own successful verification and persistence while the current dispatcher rejects recipient acceptance. It can also survive a failed dispatcher finalization. If the run-root receipt is absent, **there is no saved current dispatcher receipt**; a child receipt cannot replace it. Historical child fields do not establish satisfaction of the current recipient requirement.

After atomic rename succeeds, the API/CLI response supplies `receipt_saved: true`, the canonical path, byte size and SHA-256. On failed finalization, the response is a structured storage failure, acceptance is not granted, and cleanup is best effort. A surviving temporary payload has no successful-persistence claim. This is not an fsync/power-loss durability or adversarial-filesystem guarantee. Preserved historical child-verifier receipts retain their old exact semantics under `historical-result/`; their saved fields are not the current dispatcher's persistence claim.
