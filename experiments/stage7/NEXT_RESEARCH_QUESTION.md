# Next question after Stage 7

The current findings are useful but do not establish a new ICML method:
prediction assistance helps two public pools, the naive active-label guard
loses efficiency, and the successful reserve pipeline can still use 225 extra
queries on a path where both it and ordinary raw95 cover the truth.

## First priority: isolate the historical predictor's contribution

Compare the fixed count-grid prediction process against a **zero-trust,
model-free process with the same stakes, grid and two-sided capital average**.
When trust is zero, the corrected draw is the raw finite-pool draw; its betting
rule can still outperform PPR. The residual savings under reversed histories
make this control necessary before attributing all gains to historical data.
This ablation has not been run in Stage 7.

Keep the current predictor and settings. This is a mechanism diagnostic on
WMT23 development data. Do not select a new primary weight, filter out German,
or change the precision threshold to obtain a favorable result.

## Operational question: useful predictions with an ordinary-95% cost safeguard

Stage 6 protects paid cost relative to raw95 by using only deterministic
additional information, but did not save labels. Stage 7's stochastic
prediction process is useful, but reserves a stricter raw control. A proposed
new design must explain how it obtains useful statistical information while
protecting an explicitly named ordinary raw baseline.

One candidate worth checking is whether the finite binary raw sequence has
certifiable **unused error probability** below its nominal 0.05. If a bound
u(N) on its worst-case simultaneous failure probability is strictly below
0.05, a prediction CS at error at most 0.05-u(N) could be intersected with the
unchanged raw95 CS. Empty-intersection repair would return the raw interval.
The union bound would give total error at most 0.05, while the intersection or
raw fallback would stop no later than the raw precision stop on the same
uniform path. No extra queried labels would be needed.

This is a candidate **only**. It requires a rigorous error certificate for the
actual raw construction, a valid prediction process at the remaining error
level, careful boundary/numerical treatment, and a literature audit. Nominal
conservatism or empirical coverage in 100 runs is not such a certificate. The
remaining error allowance could be too small to be useful. No new theorem,
novelty or efficiency result is claimed here.

If that route is tested, include a **calibrated model-free raw control** as
well: exploiting raw conservatism alone could explain apparent improvement.
Exact calibration, error-budget intersections and empty-set repair are known
ideas; their combination must not be treated as automatically novel.

For any newly designed method, WMT23 remains development evidence. A later
confirmatory study needs a separately selected public release and a fixed
protocol, along with relevant published active/prediction-assisted baselines.
The research proposal to Professor Philipp Koehn should state this unresolved
methodological question alongside the reproduced gains and measured failures.
