# Change log

## 0.3.0-rc.1 — local experimental candidate

- Integrates the existing camera.decision_questions method from Python CogniMap 0.1.2 through `app.py questions --case ... --camera ... --out ...`.
- Same case-folder format; one captured in-memory case for all nested analysis. No embedded-case fallback.
- Shared canonical resolver, solver, serializer and serialization guard; no second engine fork.
- Exact thresholds, source-linked guarantee requests and known blockers in result.json and explanation.md. Two saved executed demonstrations included.
- Necessary correction: analyze now reports a true numeric serialization limitation as numeric_encoding_error with exit 4, rather than input/analysis error with exit 2. No configuration is emitted on failure. Valid analyze outputs for the ten compared cases remain byte-identical.
- Retains the original 28-method suite and ten cases; adds 18 combined-command test methods. Standalone capability regressions were separately replayed.
- Updates obsolete release-status documentation and replaces stale parent release metadata with this candidate's identity. v0.2.1 itself is preserved.

This version is not published or hardware-qualified. No solver physics, policies, U01 interpretation, external acquisition, model calls or unrelated capabilities were added.

## 0.2.1 — preserved public baseline

Published at https://github.com/KamHiggs/higgs-camera-change-review/releases/tag/v0.2.1 . Its approved archive SHA-256 is 645df210728fb68d04bf82ad2e22b2676cb2c75c930b2f35be3e107d35be881e. The saved publication verification records commit 9382e4475da66cb82eaec17ef436d770ad42eead and matching public source/asset hashes. This integration task made no GitHub or Git changes.
