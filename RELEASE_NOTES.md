# Proposed pre-release: inventree-v0.1.3-correction.1 — InvenTree change review and portable verification

**Prepared release notes; publication pending.** Created and led by Kamden Higgs. Higgs AI.

When the inputs change, know which decisions need revisiting. This experimental integration brings the existing bounded camera review into InvenTree 1.5.6. It preserves inputs/results, identifies relevant changes, and exports a decision that the matching standalone verifier can reproduce without InvenTree, a model or an API.

The [recorded demonstration](docs/DEMONSTRATION.md) follows a declared ISP change: a conditional timing question, a stale preserved assessment, a new frame-rate blocker, and offline verification that accepts the record while the camera recommendation remains blocked.

Included: unchanged tested wheel, readable source, matching verifier, three authentic screenshots, two unchanged synthetic exports and the saved verification receipt. [Installation](docs/INSTALLATION.md) · [Offline verification](docs/OFFLINE_VERIFICATION.md) · [Review status](docs/REVIEW_STATUS.md).

This is a public composition of existing software and new release documentation, not a new engineering build. The integration is `0.1.3+correction.1`; the embedded near-real wrapper is 0.1.2 and retained camera runtime is 0.3.0-rc.1. Existing camera releases remain separate.

Author testing, separate nonblind review and scripted demonstration have differing scope. Counts overlap. The C06/C09 review correction is retained. The known `1e999` opening error, exact-build verification requirement, one-platform coverage and manual host setup remain. This is a synthetic software demonstration, not hardware-qualified, generally compatible, production-ready or independently approved. No hosted service, customer savings, vendor endorsement or CogniMap superiority is claimed.

MIT for material Kamden controls, with historical notices preserved. See [current license decision](LICENSE_STATUS.md). Manufacturer material is separately qualified.

The detached final notes supplied with this package identify its ZIP SHA-256 without a circular self-hash. Use the approved public ZIP, not the larger local candidate or development workspace.
