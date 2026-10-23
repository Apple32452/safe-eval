# Three-system cell-purchase lookahead diagnostic

This protocol is fixed before computing any target-matrix result. The toy
study asks whether planning for *remaining* judgment cost changes which
individual system--item score should be purchased next when the same score
may support two requested comparisons. It does not test the Stage 36 e-factor
or claim a new ICML contribution.

## Fixed-pool task and certificate

There are three binary-scored systems and three fixed items. An action buys
one previously unobserved `(system, item)` cell for unit cost. The primary
graph is the star `(0,1),(0,2)`; the triangle adds `(1,2)` as a diagnostic.
The target for an edge is the sign of the difference of its full-pool score
sums, with ties recorded as zero. A sign is announced only if every binary
completion compatible with the purchased cells has that same sign. Thus all
announcements are logically exact, independent of the predictive model.
All methods use this *same* stopping and decision rule. Each bought cell is
counted only once, including when it contributes to two edges.

## Pre-target planner and methods

For planning only, the nine unseen scores are independent Bernoulli with
specified per-cell probabilities `p`. This is deliberately an oracle-like
synthetic design, not a learned historical predictor.

1. `lookahead`: exhaustive Bellman recursion chooses a cell to minimize
   `1 + (1-p) V(state after 0) + p V(state after 1)`. The terminal value is
   zero when all requested signs are logically fixed.
2. `greedy`: choose the cell with largest expected one-step reduction in the
   *sum* of the numbers of still-feasible signs for all requested edges.
   This is a transparent one-step proxy, **not** Stage 36's log-e-factor rule.
3. `pruned_blocks`: fixed item order 0,1,2; at the start of each item, buy
   every system incident to an unresolved edge, finishing that block even
   when an edge resolves within it. This is the Stage 22 acquisition pattern
   paired with the common logical certificate.
4. `common_blocks`: fixed item order 0,1,2 and all three scores at each item
   until the graph is resolved, with the same logical certificate.

Lookahead and greedy tie-break by higher current unresolved degree, then by
system index and item index. No policy may inspect an unpurchased score.

## Frozen probability matrices

Each matrix has three rows and three columns:

- `easy`: planning and target probabilities are row-constant `.9,.5,.1`.
- `moderate`: planning and target probabilities are row-constant `.7,.55,.4`.
- `heterogeneous`: planning and target probabilities are
  `[[.9,.7,.6],[.55,.35,.65],[.3,.4,.15]]`.
- `shifted`: plan with `easy`; target probabilities are row-constant
  `.1,.5,.9`. This tests behavior under misleading predictions.

Enumerate all `2^9=512` fixed binary score matrices for each setting.
Weight each matrix by its product Bernoulli probability to obtain *exact*
expected label costs under the target distribution. No Monte Carlo interval
is needed for these design-distribution expectations. Save every matrix,
its probability, its decisions, purchase ledger, and cost. Report mean cost,
paired expected cost differences, percentages relative to each control,
ties, wrong signs, and a first differing state if any.

## Integrity and interpretation

An independent exhaustive completion check must confirm every terminal
edge's sign. The Bellman value must agree with an independent recursive
minimum over available actions on a smaller two-item instance. Verify
no duplicated purchases, independence of policy choices from hidden cells,
and `lookahead` expected cost no greater than `greedy` under its own planner.

This diagnostic counts as a lead worth scaling only if it finds a concrete
policy difference and a material expected cost gap against both greedy and
pruned blocks in at least the easy and moderate star settings, without a
large shifted-model regression. For transparency, use >=10% as the *internal*
materiality line against both controls and <=10% shifted regression against
pruned blocks. These are research triage thresholds, not ICML criteria.
Failure stops this specific lookahead scaling route. Even a pass would need
a new validity or cost theorem and a locked independent real-data study.
