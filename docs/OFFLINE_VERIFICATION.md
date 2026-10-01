# Recheck the recorded blocked decision

Use an existing Python 3.12 installation. The recorded demonstration used CPython 3.12.14 on macOS arm64. No other platform coverage is inferred. The verifier uses the standard library; it does not require InvenTree, an AI model or a network connection.

Start in the extracted public-package root, with a new `work/` directory:

```sh
mkdir work
python3.12 -m zipfile -e examples/exports/second-assessment-isp-on.zip work/assessment-isp-on
python3.12 -B verifier/verify_assessment.py --assessment work/assessment-isp-on --out work/verification-isp-on --level decision --require-assurance HIGGS-RECORDED-DECISION-0.1.3
```

These commands translate the recorded absolute-path invocation to the supplied public layout. They were checked against the saved command, argument parser and file paths during packaging, but were not executed again. Use a fresh output directory each time. If `python3.12` has another name on your machine, confirm its version before substituting it; that does not imply your platform was tested.

The demonstration's observed result was exit 0, `historical_verification.status = VERIFIED_RECORDED_DECISION`, and `acceptance.status = ACCEPTED`. The underlying assessment remains `ESTABLISHED_BLOCKER`.

**Read only `work/verification-isp-on/VERIFICATION_RESULT.json` as this invocation's current dispatcher receipt.** A successful historical child output cannot replace a missing root receipt. Read the externally chosen requirement and acceptance together. `record_state: CONTENT_ONLY` is expected in the persisted payload; the current dispatcher recognizes it by its completed canonical location. See the unchanged [assurance contract](contracts/ASSURANCE_CONTRACT.md).

The saved receipt in `evidence/recorded-verification/` belongs to Claude's earlier demonstration, not your run. Its identity is `76d4965c61c22d1396bba0a55d174a80494251b92f6f571b0b5ecbd49a7ae223`.

## Keep the build and verifier together

Matching verifier archive: `HIGGS_ASSESSMENT_VERIFIER_v0.1.3+correction.1.zip`

SHA-256: `cf8241bf295cd02ea0635913023bc34836cb12ddd0e47723b33fb5ba84002616`

It is supplied unchanged in `downloads/` and extracted byte-for-byte in `verifier/`. Full verification binds exact software bytes, not just a version label. Original v0.1.3 records require their original verifier; automatic dispatch between original v0.1.3 and this correction was not added. Switching a host to this corrected build can make old v0.1.3 records return `CONTRACT_IDENTITY` in-host. Preserve their original verifier; do not rewrite old record identities.

The first, conditional export is included as recorded evidence. It was not separately verified in the demonstration, and packaging did not add such an execution claim.
