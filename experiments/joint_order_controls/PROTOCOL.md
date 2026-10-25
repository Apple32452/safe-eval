# Missing controls for the joint-ordering screen

Date: 2026-10-25. Frozen before computing these additional control outcomes.
This is an explicitly **post-result diagnostic on the same 100 matrices**
from `joint_order_gate/results_reference/cases.json`, not independent
validation. The original expansion gate remains failed. No new repeats,
WMT outcomes, human responses, or changed candidate parameters are allowed.

## Questions

1. Does the candidate still save labels when a matched cell control may
   rebalance its pair evidence at every step?
2. Does it save labels against prediction-aware exact paired-difference
   tests that purchase active systems on a common item order?
3. When do the joint null constraints provide additional expected log
   evidence, beyond an implied pair null? This is a mechanism diagnostic,
   not a sample-cost theorem or an originality claim.

The fixed target is the sign of each requested full-pool binary mean
difference, including exact ties. Use the original reference star and
triangle, alpha=.05 per graph task, and unique purchased cells as cost.
Every incorrect completed path is charged the full 48-cell budget in
comparisons, while raw cost and incorrect declarations are saved separately.

## New controls

### `rebalanced_pair_order`

Replay exactly the original adaptive cell stream, extending it with the
same RNG if necessary. Keep the original exact directional pair factors,
predictions, and proposal unchanged. For each hypothesized weak order,
take its implied *requested* pair factors plus the unit factor. Before
the next outcome, choose simplex weights maximizing predicted expected
log growth of their convex combination. Multiply these combined factors
over time; reject each order at 1/alpha and use the original nonvacuous
surviving-order decision rule. This isolates per-step capital reallocation
from the additional joint-null calibration in the candidate.

Use SLSQP with ftol=1e-10, maxiter=500, uniform initialization. Normalize
nonnegative finite weights explicitly. A nonfinite/negative-growth fit
falls back to the best single factor including one. Every convex combination
remains valid under the order null independently of optimizer success.
Record numerical issues and the largest independently checked expectation.

### `paired_exact_closure` and `paired_exact_bonferroni`

Use the original saved Stage 22 item permutation. Before revealing an item,
purchase exactly the systems incident to unresolved requested pairs; charge
each cell once. Each pair observes a uniform common prefix until resolution.
No new item is chosen using its unseen scores, and all factors for a round
are fixed before any scores from that item are exposed.

For an ordered pair (a,b), the observed difference D is in {-1,0,1}.
With observed sum d and m items left, the exact compatible null histograms
are nonnegative integer triples (c-,c0,c+) with sum m and
`d+c+-c- <= 0`. Optimize a three-event factor against every such histogram
divided by m. This allows arbitrary within-item system dependence.

Predict the next difference using its past categorical counts plus four
prior observations. Prior masses are `(1-pa)*pb`,
`pa*pb+(1-pa)*(1-pb)`, and `pa*(1-pb)`, using the same external marginal
priors as the candidate. Thus this control can learn paired dependence.
Use the original factor solver's bounds, tolerances, feasibility shrink
and unit fallback. Freeze both directional wealths once an edge resolves.

The closure control averages the current directional wealths implied by
each order among requested pairs, and uses the original order rule at
1/alpha. Bonferroni uses threshold 2*number_of_requested_pairs/alpha;
simultaneous opposing crossings abstain. Both use exact remaining-total
bounds, preserve first decisions, retire inactive systems and resolve ties
only from exact endpoint totals. Their acquisition histories may differ.

## Reporting and verification

Report all five original scenarios, both graphs, all new controls and the
unchanged joint/Stage 22 costs. Use 10,000 paired bootstrap resamples with
seed 20261027 for descriptive 95% intervals. These are post-result
descriptions without a new pass/fail expansion rule or multiplicity claim.

Check predictability by perturbing a just-purchased outcome; check no
duplicate charges, exact ties, full completion, and retirement accounting.
Independently enumerate small binary matrices and all item permutations
for the common-item controls, including heterogeneous correlation patterns.
Audit every saved path by reconstructing purchases, first decisions, costs,
and conditional expectations against compatible integer null completions.

For the mechanism note, derive the nested-null log-growth inequality and
the equality condition when a pair-null KL projection already lies in the
joint null. Numerically verify the adjacent-swap example at the initial
state; do not infer a stopping-cost bound from a log-growth calculation.

A positive comparison still needs an independent, larger validation and a
distinct contribution beyond existing growth-optimal e-values and rank
closure. A failure narrows or rejects the present candidate. Preserve all
results and do not tune the candidate on these additional controls.
