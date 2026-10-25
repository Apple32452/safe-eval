# Joint ordering factors under adaptive cell purchases

Frozen 2026-10-25 before this experiment's target matrices or cost outcomes.
This is a small binary, three-system mechanism screen. It is not an ICML
novelty claim or a new sample-complexity theorem. WMT24, WMT25 and human
responses are not read. The previous panel proposal remains a failed result.

## Question and hypotheses

Does directly calibrating an evidence factor against an entire possible
ordering help identify **individual** comparison signs, compared with
order closure of separate pair factors, on the same purchased cells?

Fix three systems, 16 binary items per system and alpha=.05. Purchase one
unseen system-item score per action. A previously purchased score is cached
and used by every relevant test. Inspect both the reference-0 star (two
edges) and the complete triangle (three edges). A strict sign is certified
only if all surviving weak orders agree; ties require exact endpoint totals.
An empty survivor set does not license a vacuous conclusion.

## Acquisition and prediction, shared by the three cell methods

At each step, let s[v] be observed successes, m[v] the remaining cells and
prior[v] a fixed external synthetic prediction. Use
`pred[v]=clip((s[v]+4*prior[v])/(16-m[v]+4), .05, .95)`.
Let `u[v]=sum(w!=v) 1/max(abs(pred[v]-pred[w]),.1)` and
`q[v]=.2*m[v]/sum(m)+.8*m[v]*u[v]/sum(m*u)`.
Choose a system by q, then an unseen item uniformly within that system.
Choose the proposal and every factor before exposing the new outcome.
The common cell path depends only on observed scores, never on a method's
future results. All methods charge the same paid prefix up to their stops.

## Four comparisons

1. `joint_order`: a separate conditional factor for each of all 13 weak
   orders, calibrated against every compatible fixed total vector satisfying
   that order's weak inequalities and within-group equalities. Solve the
   six-event expected-log-factor problem in THEORY.md. Reject each order at
   wealth 1/alpha; certify signs from its surviving orders.
2. `exact_pair_closure`: six directional pair nulls, with the **same exact
   factor optimizer**, predictions and acquisition. For each weak order,
   average current wealths of its implied directional nulls and reject at
   1/alpha. Never average independently maximized past wealths.
3. `centered_pair_closure`: finite-pool centered inverse-probability scores,
   the established six-stake mixture (.02,.05,.1,.2,.4,.8), and the same
   order-averaging rule and cell path. This is a CELEUS-style baseline
   composition, not a claim to reproduce every implementation detail of CELEUS.
4. `stage22`: the frozen common-item pair certificates and active-vertex
   purchase schedule, at threshold 2*requested_edges/alpha. It receives an
   independent precommitted random item permutation on the same score matrix.
   Record its first declarations, including errors; do not abort on an error.

The exact factor optimizer is SLSQP, ftol 1e-10, maxiter 500, factors in
[.001,10000], starting from ones. Re-evaluate every null-vertex constraint
and shrink a finite candidate by `(1+1e-9)*max(1,max_null_expectation)`.
Use the unit factor if the candidate is nonfinite or has negative expected
log growth after that shrink. Record numerical fallbacks. Optimizer status
alone does not certify conditional validity or global optimality.

## Frozen synthetic settings

| Scenario | Actual marginal probabilities | Prior | Within-item dependence |
| --- | --- | --- | --- |
| independent_strong | .15,.50,.85 | .20,.50,.80 | Independent |
| independent_moderate | .30,.50,.70 | .30,.50,.70 | Independent |
| correlated_strong | .15,.50,.85 | .20,.50,.80 | One shared uniform per item |
| reversed | .85,.50,.15 | .15,.50,.85 | Independent |
| near_ties | .45,.50,.55 | .30,.50,.70 | Independent |

Use 20 repeats per scenario and the first eight little-endian SHA256 bytes
of `20261025|joint_order_gate|scenario|repeat` as the case seed. The matrices
are sampled once and then treated as fixed. Predictions are deliberately
favorable in aligned cases and misspecified in others; they are not learned
from an independent real dataset. Tied realized totals remain in the study.

Record all paid cells, decisions, correct completions, wrong declarations,
and numerical diagnostics. Report raw stop cost; charge the full 48-cell
budget in the summary when a method makes any wrong requested declaration.
This prevents erroneous early decisions from being rewarded as efficiency.
Report paired bootstrap descriptive 95% intervals for the reduction in mean
charged cost, with 10,000 resamples and seed 20261025, for all comparators.

## Validity and expansion gate

Before the cost run, independently enumerate compatible integer totals for
every small-pool state and check the vertex reduction, factor conditional
expectations, exact ties, and the individual-sign rule. Enumerate the full
adaptive decision tree at N=2 for all 27 total triples (covering all 64
binary score matrices) and check the familywise error of every cell method.

Expand only if the joint method has no wrong requested declaration and has
a strictly positive lower bootstrap endpoint for savings against **both**
exact pair closure and Stage 22 in the two independent aligned scenarios,
for both graphs, with at most 10% mean-cost regression to those controls
in the reversed case. Report all scenarios regardless of the decision.
This is an internal expansion rule, not an ICML percentage threshold.

A positive result still needs a prediction-aware complete-item control,
scalability, independent real-data validation and a distinct cost result.
Growth-optimal e-factors and order closure already exist. This screen isolates
the particular joint finite-pool mechanism; it cannot prove originality.
