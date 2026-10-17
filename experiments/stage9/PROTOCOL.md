# Stage 9 ordinary raw95 cost safeguard

This is a fixed development-data feasibility study. It applies known finite
state calibration, error allocation, confidence-set intersections and empty-set
fallback. No ICML novelty or new statistical principle is claimed.

## Mathematical calibration independent of target outcomes

For each N in {154, 589, 820}, enumerate every feasible (t,s,K) state of the
unchanged published raw95 implementation. Check that each pointwise accepted
set is contiguous. Count surviving binary strings exactly using integer dynamic
programming. At fixed K, all comb(N,K) binary strings are equally likely under
uniform sampling without replacement. The maximum failure fraction over every
K certifies an upper bound u(N) on the actual raw95 interval failure probability.
Any symmetry reduction requires checking every mirrored acceptance boundary.

Allocate alpha(N) = floor(10^6 * (0.05-u(N))) / 10^6 to a prediction confidence
sequence. If alpha is zero, return raw95. This rule uses only N and the raw
algorithm, not target outcomes, history quality or experiment results.

Include a model-free calibration control: the smallest integer PPR evidence
threshold in {2,...,20} with certified worst-case failure at most .05. Verify
the selected threshold and an unsafe predecessor. This is the best threshold
on the stated integer grid, not a claim of global calibration optimality.

## Four methods on the same query ledger

1. raw95: the unchanged ordinary PPR95 intervals.
2. calibrated_raw95: calibrated PPR intervals intersected with their running
   sets; return raw95 if the calibrated interval is empty.
3. budget_zero95: intersect raw95 with a count-grid model-free betting CS
   at error alpha(N); return raw95 if the intersection is empty.
4. budget_prediction95: the same construction with the unchanged historical
   predictor, trust rule, variance prior, targeted stake heuristic and .9 cap.

All three additions return subsets of raw95, or raw95 itself. Empty outputs
never count as precision stops. On each shared path the first nonempty
width <= .10 stop is therefore no later than raw95, including failure paths.
The prediction/intersection error is bounded by u(N)+alpha(N) <= .05.
The calibrated raw error is independently certified at <= .05.

Prediction capital is accumulated as conservative lower bounds. Outward
binary64 bounds enclose the exact rational corrected draw and candidate k/N;
scaled mantissa/exponent products avoid overflow and logarithm error. The
lower capital is dominated by a valid exact-arithmetic predictable capital.
The assumptions about IEEE-754 operations and nonnegative summation are stated
in rounded_betting.py and THEORY.md. Stored integer count endpoints define
rational intervals. The usual statistical model assumes uniform randomized
sampling; pseudorandom seeds are for reproducibility.

## Frozen empirical comparison

Use exactly the 117 Stage 8 cases: 39 targets, all three WMT23 development pools,
and aligned/permuted/reversed histories. Use 100 repeats and unchanged target
seeds, uniform CDF query generation, epsilon .05, ridge features and trust.
Run two workers with one BLAS thread each. Retain German and both stresses.
No outcome-guided threshold, weight, predictor, precision or seed selection.

The primary contrast is budget_prediction95 minus budget_zero95 under aligned
history, weighting languages equally and then systems within language.
Report prediction versus raw95 and calibrated_raw95 as required diagnostics.
If calibration explains the apparent benefit, report that limitation.
Report all languages and stresses, simultaneous coverage, mean label cost,
repair and empty-set rates, stopped error, worst-path overhead, and paired
conditional query-randomization Monte Carlo standard errors.

At 100 repeats, match all raw streams and five raw metrics against Stage 8.
Independently audit certificate counts with backward dynamic programming.
Replay historical predictions, scalar enclosures, capital, intervals and
fallback flags from saved query ledgers without calling the engine. The
arithmetic primitives are shared and tested separately against exact rational
calculations. Reduced-repeat runs are software checks.

The first certificate calculation was mathematical development, before any
Stage 9 benchmark comparison. Freeze implementation and protocol before the
100-repeat run. Keep Stage 7 and Stage 8 unchanged. No new human annotation,
private data, untouched validation or future-population generalization is used.
