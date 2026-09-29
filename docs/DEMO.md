# Read the synthetic camera-change example

After following the README quick start, open the generated `engineering_review.html` locally.

1. Start with the boundary: a synthetic prediction and unapproved proposal, not a hardware qualification.
2. Find `TEST-B-FAST`. Its saved PASS conflicts with observations 3.35 and 3.4 mm against its own 1 mm limit. The report also distinguishes stale firmware/policy/offset fields. A contradiction and stale applicability are different findings.
3. Compare CAM-B's slow interval `[-4.8, -3.2]` with its fast interval `[-2.8, -2.2]`. They do not overlap; the selected per-variant offsets are −4 and −2.5 ms.
4. Inspect CAM-D's missing guaranteed jitter bound. Its typical value and finite sample do not supply a guarantee. The selected CAM-B cost is 5 synthetic points; unresolved CAM-D could be cheaper. This is a minimum among established feasible plans, not a proven optimum over unknown facts.
5. Review the exact proposed configuration and required retests. The generated adapter only adds the selected offset and rejects unknown variants. It does not read a camera or actuate equipment.

For a justified refusal, run a separate named batch:

```sh
python3 -B run_cases.py --batch refusal-example descriptive_conflict
```

The result is `insufficient_evidence`. Explain U01: a descriptive source conflict can prevent selecting one specification identity even though the agreed physical fields pass. Do not call this proof of physical impossibility.

All supplied cases and observations are synthetic. Source IDs, units and failure records are part of the demonstration; no hardware result or customer endorsement is implied.
