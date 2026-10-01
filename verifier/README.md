# Higgs assessment verifier 0.1.3+correction.1

Created and led by Kamden Higgs. Higgs AI. Separately obtained software; no InvenTree or model dependency. Python 3.12 tested. Review the detached verifier ZIP hash and MANIFEST.json before use; a manifest is not authentication of its publisher.

Extract the assessment and this verifier in separate folders. Use a new output directory:

```sh
python3 -B /path/to/verifier/verify_assessment.py --assessment /path/to/assessment --out /path/to/new-output --level decision --require-assurance HIGGS-RECORDED-DECISION-0.1.3
```

Read `historical_verification`, `recipient_requirement`, `acceptance` and `receipt_saved` together. Exit 0 requires the requested level, required assurance and saved receipt. See ASSURANCE_CONTRACT.md for precedence and exit 1/3/4/5/6. Without a requirement, acceptance is NOT_EVALUATED, never silently derived from the record.

Exact archived 0.1.1 and 0.1.2 executors are included for historical compatibility. Their successful historical verification does not alone satisfy current recipient assurance. This is not manufacturer truth, engineering approval or an independent review.

No public release is authorized. Inherited license/attribution and source-use qualifications are retained in LICENSE_REVIEW.md and dependency_notes. The synthetic engine and source captures are unchanged.

## Correction-build identity and receipt location

The distribution is 0.1.3+correction.1. Emitted protocol/version labels and assurance requirements remain 0.1.3; the exact software hash distinguishes this build. This patch corrects over-limit integer intake and clarifies receipt recognition. It does not update historical executors or change the assurance matrix.

Only `<run-root>/VERIFICATION_RESULT.json`, at the exact directory supplied to `--out`, is the current dispatcher receipt. Read its complete type/state, historical result, external requirement and acceptance. A successful `<run-root>/historical-result/VERIFICATION_RESULT.json` is child output, not recipient acceptance; if the root receipt is missing, a child cannot stand in for it. Do not recursively search for a successful receipt. See ASSURANCE_CONTRACT.md.

Full decision verification requires matching source identities. Use this correction verifier with the candidate's new `correction1-conditional.zip` example, and the unchanged original v0.1.3 verifier for prior v0.1.3 examples. Original recorded identities must not be rewritten. This correction was not freshly installed into a live host or browser-tested. See CORRECTION_NOTES.md for the focused execution scope.
