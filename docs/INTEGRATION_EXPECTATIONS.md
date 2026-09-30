# Integration expectations — pinned before implementation

Version target: 0.3.0-rc.1. Author-derived arithmetic and interface expectations, not blinded external acceptance.

I01 Public case: existing CAM-B/per_variant plan costs 5. CAM-D policies shared/per_variant each require j <= 2/5 ms inclusive; costs 2 and 5. The typical value and sample cannot satisfy the guarantee.
I02 Blocked case: stipulated CAM-D power 11 W exceeds fast budget 10 W. No jitter-only sufficient request or emitted config.
I03 Renamed three variants: a=(1,3/4,5/4), biases=(0,1/2,-1/4). At zero jitter, intervals [-1,1],[-5/4,1/4],[-1,3/2]; intersection [-1,1/4]. Shared threshold 5/8; per_variant 3/4. No current guaranteed plan if it is the only candidate.
I04 Four variants: a=(2,1,3/2,5/4), biases=(0,1,0,1/2). Intersection [-3/2,0] gives shared 3/4; per_variant 1. Reordering changes no boundary.
I05 Fresh two-variant case: a=(1,3/2), biases=(0,1). Intersection [-1,1/2] gives shared 3/4; per_variant 1. Equality allowed; above shared boundary only per_variant; above 1 neither.
I06 Three-variant boundaries: j=(5/8 +/- 1/10000, 5/8, 3/4 +/- 1/10000, 3/4) yield shared up to 5/8, per_variant through 3/4, then no_feasible_plan. Check actual analyze CLI on supplied exact decimal literals.
I07 Multiple unknown required operands, identity conflict U01, missing cost/availability/firmware => unsupported single-answer sufficiency; no thresholds invented. Explicitly superseded obsolete facts do not override current facts. Missing optional description irrelevant.
I08 Already known guarantee => not_needed. Unavailable/known blocker => blocked. Target outside declared set, malformed/duplicate/nonfinite/boolean numeric input => input_error. Non-synthetic declared model => unsupported. No fallback on empty/missing case or base.
I09 Numeric encoding: bias 1000000000.00000001, speed1, limit0, jitter0, host0 has exact feasible offset but serialization residual1e-8 > tolerance1e-9: numeric_encoding_error, no emitted config/firmware. At residual1e-9 succeeds. Missing guarantee version retains mathematical zero threshold but encoding-failed witness and no sufficient guarantee-only request.
I10 Costs equal/more expensive never labeled savings. Zero speeds unbounded with guarantee still required; negative thresholds empty; mixed zero speed preserves constraints.
I11 Inputs stay byte-identical; output overlap/nonempty/symlinks refused. A single case load supplies current analysis and hypothetical witnesses. No disk rereads for nested operations. Actual IDs/locators/revision relationships retained.
I12 Adapted operation result equals standalone v0.1.2 on equivalent inputs; only outer integration metadata/knowledge identity deliberately differ. Same source resolver, engine, finite serializer and encoding guard shared by analyze and questions.
I13 For ten unchanged analyze cases all emitted file bytes equal v0.2.1. Numeric failure label/exit changes intentionally from input/analysis error2 to numeric_encoding_error4; malformed input stays2. Unsupported questions returns3, successfully assessed blocked/supported/not_needed returns0.
I14 Execute the retained 28-method camera suite and ten cases, standalone v0.1.2 DecisionQuestionsTests (16 methods) and NumericEncodingRegressionTests (8 methods), plus actual combined-CLI regressions. Overlap/repeats reported separately. Run final commands from clean ZIP extraction and unrelated cwd.

No supplier or hardware authentication, model calls, deployment approval, general optimal question selection, publication, or empirical workflow advantage is asserted.
