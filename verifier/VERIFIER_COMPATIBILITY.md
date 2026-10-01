# Explicit historical compatibility

E = HIGGS-ENGINE-OUTPUT-1; D011/D012/D013 = HIGGS-RECORDED-DECISION-0.1.1/0.1.2/0.1.3.

| Declared format | Exact executor | Engine | Decision | SUMMARY.md checked at decision level | v0.1.2+ format guarantee |
|---|---|---|---|---|---|
| 0.1.0 | archived 0.1.1 | E | unavailable | no | no |
| 0.1.1 | archived 0.1.1 | E | D011 | no | no |
| 0.1.2 | archived 0.1.2 | E | D012 | yes | yes |
| 0.1.3 | current 0.1.3 | E | D013 | yes | yes |

| Verified assurance | E required | D011 required | D012 required | D013 required |
|---|---|---|---|---|
| E | accepts | unmet | unmet | unmet |
| D011 | accepts | accepts | unmet | unmet |
| D012 | accepts | accepts | accepts | unmet |
| D013 | accepts | accepts | accepts | accepts |

This inclusion policy was adopted explicitly before implementation. D013 retains D012 decision/format checks with bounded intake and external acceptance; D012 includes the prior decision-chain checks. It is not a general rule about larger version numbers. Successful evidence of a historical contract cannot alone satisfy a newer requirement.

Archived 0.1.1 verifier: SHA-256 `96f99c16314a57e7c1eb6c6e769e3cae7af2e0cb4081b5423eb23e3554b6bfb6`.
Archived 0.1.2 verifier: SHA-256 `ef322e698e0c4c7f283f98b0136877cf1926f2504210beae88b36c6ceb310b69`.
These archives are unchanged. Missing or altered required executors refuse explicitly; there is no silent fallback. Current preflight bounds and structural checks do not retroactively add current semantics to historical success.

Current source identity includes the policy JSON. The current verifier archive's final identity is in the detached delivery receipt, avoiding a self-hash. The frozen matrix's null current-archive pin records that its bytes did not exist before implementation; final distribution binding is completed by that detached receipt.
