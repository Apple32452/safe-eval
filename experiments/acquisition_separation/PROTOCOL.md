# Exact acquisition-class separation diagnostic

Frozen 2026-10-26 before computing this diagnostic's optima. This follows the
failed joint-order contribution: rebalanced pair factors matched 197/200
completion costs. No old candidate is retuned and no WMT or human data are read.

## Question and scope

Can an adaptive individual-cell policy have strictly smaller attainable
expected judgment cost than **every** policy in each of two acquisition
classes, when all classes can use any valid decision rule?

Fix three systems and two binary items (six cells). Enumerate all 64 fixed
matrices, without excluding ties or low-prior-probability matrices. The output
is the complete vector of full-pool comparison signs for either the reference
star (0,1),(0,2), or the triangle including (1,2). A score is purchased once
at unit cost. Every method eventually reports one complete sign vector.
Before that it may report unresolved. For **each individual fixed matrix**,
the probability of any wrong final sign must be at most alpha. Use alpha=0
and alpha=1/20; the latter is primary. The rule chooses its stopping time;
this is not a reusable confidence sequence valid for arbitrary replacement
policies.

## Acquisition classes, with unrestricted inference

- `cell`: choose any unseen system-item cell using the full observed history.
- `row_uniform`: choose any system using the full observed history, then
  sample uniformly from its unseen items. This includes the previous
  rebalanced-pair acquisition and any improved inference using that rule.
- `common_retirement`: start with all systems active. At a round, choose any
  nonempty subset of the active systems, permanently retire the rest, draw
  one unopened item uniformly, and buy that entire chosen subset before
  observing any of its scores. Never revisit an opened item. This includes
  common-item retirement, including the Stage 22 and exact paired controls.
  It even permits early retirement without a prior individual certificate,
  provided the final complete answer meets the same per-matrix error bound.

All classes may randomize and stop adaptively. Common-item methods are not
required to use Bonferroni or a particular betting factor. Histories that
lead to the same observed partial matrix (and, for the common class, opened
items and active set) can be merged because their relative probabilities
are the same for every compatible hidden matrix. The linear-program model
and a proof of this reduction must be documented and checked.

## Objective distributions, fixed before outcomes

The objective is expected paid judgments under a supplied synthetic prior;
validity must still hold separately for **all 64 matrices**, not just on
average under that prior. Items are independent draws from the following
three-bit column distributions. A bit string is in system order (0,1,2).

1. `independent`: product Bernoulli marginal probabilities (1/5,1/2,4/5).
2. `monotone`: 90% of the distribution assigning 000:1/5, 001:3/10,
   011:3/10, 111:1/5, plus 10% uniform over all eight columns.
3. `opposed`: 90% of the distribution assigning 100:1/5 and 011:4/5,
   plus 10% uniform over all eight columns.
4. `one_hot`: 90% of the distribution assigning 100:1/10, 010:3/10,
   001:3/5, plus 10% uniform over all eight columns.

All distributions have full support. This produces 4 priors x 2 graphs x
2 error levels x 3 classes = 48 optimization problems. These are exact
finite-distribution calculations, not Monte Carlo repeats or human savings.

## Optimization and certificates

Use a sequence-flow linear program. A state has a reach probability common
to every compatible hidden matrix. Outgoing action flows sum to incoming
flow. A queried cell branches to its two possible values with the same
flow, since the value is deterministic conditional on the hidden matrix;
only randomized item selection contributes a probability coefficient.
Impose one error-flow inequality per hidden matrix. Charge query flows by
their unit cost times the prior probability of the state's compatible set.

SciPy HiGHS supplies a candidate optimum, but floating-point solver success
alone is insufficient. Recover a rational randomized policy; evaluate every
fixed matrix exactly. If rationalization exceeds alpha, mix with complete
evaluation just enough to restore the bound. Recover nonnegative rational
error penalties from the dual and use exact backward Bellman inequalities
to certify a lower bound on **all** policies in each class. Report the
verified policy upper bound, verified dual lower bound and their gap.

At alpha=0, independently compute the logical-certificate dynamic-program
optimum. Check it agrees with the linear program. Check acquisition-class
inclusion, no repeat purchases, terminal probability one, and prediction
choices depending only on observed values.

## Decision

A concrete separation exists only if the exact feasible `cell` upper bound
is strictly below both exact comparator lower bounds in at least one of the
three prespecified dependent priors at alpha=1/20. Report every result even
if there is no separation. No percentage defines ICML novelty here.

Also establish or refute the symmetry prediction: under a prior invariant
to independent item permutations within every system, the optimal `cell`
and `row_uniform` expected costs agree. A proof, if obtained, is a boundary
result using standard symmetrization; do not presume it is original.

This diagnostic is deliberately tiny and computationally exponential.
Constrained decision-process linear programming and active feature
acquisition are existing ideas. Even a verified strict separation is not
a scalable evaluation algorithm or an established ICML contribution.
