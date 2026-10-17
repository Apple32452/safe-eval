# Stage 10 stronger-calibration and novelty study

This is a development study on the existing fixed binary WMT23 pools. It does
not introduce a new prediction method or claim untouched confirmation. Stage
7, 8 and 9 files remain byte-identical. Parent main commit:
90b44f3175568704f37a3703d086f27b26437a19, tree
690dddbc06624c8e3a0244123ed5a4aa3534ae84.

## Outcome-independent mathematical search

For each N in {154,589,820}, reproduce the Stage 9 ordinary raw and integer-grid
calibration certificates on the current runtime. Let h be the integer-grid
threshold. Starting with [h-1,h], verify that its lower endpoint has unrepaired
full-path error greater than .05 and its upper endpoint has error at most .05.
Perform exactly twelve dyadic bisections. At every midpoint, count binary
strings with exact integer dynamic programming for every feasible total K.
Keep the unsafe lower endpoint and valid upper endpoint. The final bracket
has width 1/4096. Use the upper endpoint as fine_raw95. This is fine-grid
calibration for this one PPR family, not globally optimal model-free inference.
The search uses only N and the implemented algorithm, never target labels,
history quality or observed label-cost comparisons.

fine_raw95 returns the running intersection at its certified threshold; if
empty, it returns the unchanged running raw95 interval. Empty outputs are
never precision stops. Full evaluation is exact. Because every nonempty fine
PPR pointwise set is contained in raw95's pointwise set, its output is a subset
of raw95 or fallback equality. The ordinary-raw95 stopping safeguard remains
valid. No pathwise dominance over the integer-grid repaired control is assumed.

## Empty-set repair investigation

Implement an exact path-aggregation recurrence for the full-path error of the
repaired rule. State consists of success count, surviving count interval and
whether the calibrated running intersection has already become empty. Before
fallback, update the calibrated intersection. At its first empty intersection,
retain the old surviving interval intersected with the current raw pointwise
set and switch permanently to raw updates. Later outputs are raw, but coverage
survival retains all earlier calibrated restrictions. Drop empty survival
states. At full N, count accepted binary strings by their final success count.

Verify this recurrence by exhaustive enumeration on small pools. Examine
whether repaired risk is monotone in threshold rather than assuming it.
At the actual three pool sizes, attempt the selected fine threshold with fixed
resource limits: at most 1,000,000 distinct states in a layer and 20,000,000 state
transitions per attempt. If this completes, also examine exactly three lower
thresholds: fine-1/2, fine-1/8 and fine-1/64. Evaluate all three without assuming
monotonicity. If the initial fine attempt is capped, skip those further probes
and record why. Record every completed, capped or skipped attempt. A capped
attempt is not a certificate. repair_raw95 uses the smallest threshold among
fine and the completed lower probes with certified repaired full-path error
at most .05. If none qualifies, it equals fine_raw95. This is a limited fixed
grid, not optimal calibration. No incomplete count licenses a threshold.

## Frozen empirical comparison

Use all 117 Stage 9 cases and all 100 repeats, with the unchanged query paths,
precision .05, historical predictor, trust, stakes and alpha allocations. Only
the model-free comparison is added; no prediction branch is tuned or retrained.
Reuse lossless Stage 9 curves only after checking their saved protocol, case
metadata, every ledger hash, reconstructing all 46,800 saved stopping decisions
and verifying their summaries against the source's completed audit/reference
records. Generate fresh Stage 9 outputs if unavailable;
never substitute a different number of repeats for this comparison.

Compare unchanged Stage 9 prediction with both new controls under all three
history conditions. The primary contrast is prediction minus repair_raw95 with aligned
history, weighting languages equally then systems within language. Report
language-specific and equal-language means, paired query-randomization MCSE,
coverage, stopped error, empty/fallback rates, target mean wins/ties/losses,
worst-path extra labels and the integer-to-fine/repair calibration effects. Report all
systems and both adverse histories. Do not choose a favorable subset.

Independently verify the final unrepaired safe and unsafe certificates by
backward integer counting. Cross-check any completed repaired certificates with
an independently coded forward recurrence using explicit returned intervals
and candidate-survival bitmasks, in addition to exhaustive small-pool checks.
Replay every new baseline curve from the actual parent PPR interval
function, and verify query uniqueness, raw95 containment, decisions, summaries,
and all preserved Stage 9 method metrics. Sharing the tested parent gate
function is explicit. Do not rerun the unchanged prediction-capital audit just
to produce new-looking evidence; preserve the original completed audit and
verify the saved traces against a separately frozen trace manifest.
For local reproduction, an independently audited local Stage 9 source may have
its own runtime-dependent prediction paths; preserve and report those source
metrics rather than silently replacing them with archived prediction means.

## Novelty and decision record

Resource revision before benchmark comparison: initial limits of 100,000 states
and 5,000,000 transitions stopped the N=154 attempt after 102 layers despite
using only 41,283 peak states, and capped both larger pools. Preserve those
attempts and increase the final fixed mathematical limits as stated above.
This change uses computational feasibility only; no Stage 10 benchmark costs
have been examined. Independent explicit-state audits use at most 1,000,000
states and 50,000,000 transitions. Record any audit cap as an unresolved check,
not a successful independent verification.

Compare the exact setting, estimator, inference rule, acquisition, guarantee
and limitations with finite-population PPR confidence sequences, betting
confidence sequences, Prediction-Powered E-Values, Robust Sampling for Active
Statistical Inference and Prediction-Powered Active Testing. Add directly
relevant calibration/boosting work found during the review. Use primary sources
and distinguish a known ingredient from a candidate difference. Do not infer
absence of a guarantee merely because an abstract omits it.

Freeze implementation, this protocol and the Stage 9 trace manifest before
examining the new benchmark comparisons. Record tests, search attempts,
computational limits, every result and unfavorable regime. An advantage that
vanishes against this stronger control is a reportable limitation. A remaining
advantage is development evidence requiring a separate novelty argument and
new-data confirmation. Do not label inspected WMT24 data untouched.
