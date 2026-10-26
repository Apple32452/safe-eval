# Acquisition classes, exact certificates, and a symmetry boundary

This note defines an exact finite diagnostic. The linear programming,
Lagrangian bounds, and symmetrization are established techniques; originality
of this particular application is not asserted.

## Model and sufficient state

A hidden fixed binary matrix Y has three systems and N items. The desired
answer g(Y) is the vector of requested signs of full-row-sum differences,
including zero for ties. The error constraint is

    P_Y(output != g(Y)) <= alpha, for every binary matrix Y.

Randomness here is solely the policy's randomness. The synthetic full-support
distribution pi over Y weights expected cost; it is never an assumption
required for validity. All policies stop after at most 3N purchased cells
and report only one complete answer. Pausing earlier can return unresolved.
Replacing the optimized policy by a different reporting or acquisition
policy is not covered by its certificate.

The state records observed cell identities and values. The common-item
class additionally records opened items and the currently active systems.
For any complete observed history leading to state s, its probability is
the same under every Y consistent with s: action choices depend only on
previously revealed scores, and the values are deterministic conditional
on Y. Thus the conditional mixture over histories that reach s is also
the same for all compatible Y. Merging these histories into a randomized
state-based action rule preserves their next-action distributions, terminal
answers, and costs under every Y. This justifies optimizing state-based
rules while bounding arbitrary history-dependent rules in each stated class.
It is sufficient to permit reports attainable by a compatible matrix: a
report impossible at s is wrong under every compatible matrix, so replacing
it by any possible report cannot increase any per-matrix error or query cost.

## Sequence-flow linear program

Let x(s,a) be the probability of reaching s and taking a, conditional on
any compatible Y. For an unseen cell query, both possible score children
receive that same flow; exactly one is compatible with any given Y. For
row-uniform queries the coefficient is 1/(number of unseen cells in that
row). For a common-item action it is 1/(number of unopened items), and the
entire selected active subset is purchased before observing its values.
Write p(t|s,a) for these coefficients on a compatible child t.

    sum_a x(s,a) - sum_{t,a: s is a child} p(s|t,a)x(t,a) = 1{s=root}.

Stop actions have no children. Their error constraints are

    sum_{s consistent with Y} sum_{a reporting != g(Y)} x(s,a) <= alpha

separately for every Y. The objective is

    sum_{s,a} pi({Y consistent with s}) * cost(a) * x(s,a).

The action costs are one for a cell or row-uniform action, and the number
of bought systems for a common-item block. All x are nonnegative. Because
every query increases the number of observed cells, the graph is acyclic.
Normalizing outgoing x at each reached state constructs a policy. Conversely,
any policy in the class induces feasible flows with its actual cost. Thus
the finite LP characterizes the optimal expected cost in that class.

## Exact upper and lower certificates

The floating-point LP is only a proposal generator. Its action probabilities
are converted to rational numbers and renormalized. An exact recursive
evaluator computes cost, terminal mass, and error for every Y. If the largest
error e exceeds alpha after rationalization, mixing with complete evaluation
with probability 1-alpha/e restores the bound exactly. Every mixture purchase
is counted. This supplies an attainable upper bound U on optimal cost.

For a lower bound, choose any nonnegative rational penalties u_Y on the
per-matrix errors. Put M(s)=pi({Y consistent with s}). Work backward through
every state and every legal action, including actions the proposed policy
never uses:

    V(s) = min over actions of
      sum_{Y consistent with s, g(Y) != report} u_Y,             [stop]
      M(s)*cost(a) + sum_t p(t|s,a)*V(t).                       [query]

Each candidate in this minimum is a dual inequality. Summing the flow
constraints with these V values gives

    expected cost + sum_Y u_Y * P_Y(error) >= V(root).

Every uniformly alpha-valid policy therefore has expected cost at least

    L = V(root) - alpha * sum_Y u_Y.

The penalties may come from a numerical dual solution; recomputing V with
exact fractions makes the resulting bound valid independently of optimizer
status or numerical dual tolerances. If U_cell < L_row_uniform and
U_cell < L_common_retirement, there is a certified separation from **all**
policies in both comparator classes for this particular expected-cost design.
It is not a pathwise advantage on every fixed matrix.

At alpha=0, any positive-probability stop at a state permitting two answers
would be wrong for at least one compatible Y. Hence stopping is allowed
only at a logically resolved state. Exact backward dynamic programming over
the permitted acquisition actions gives both the optimum and a feasible
policy; it is checked against the independently constructed LP.

## General symmetry boundary

**Proposition.** For any finite number of systems and items, suppose pi is
invariant under independent permutations of item positions within each
system, and g(Y) depends only on the systems' full-row sums. Under the same
uniform per-matrix error constraint and unit cell costs, the optimal expected
cost of arbitrary individual-cell acquisition equals the optimum obtained
by choosing a system adaptively and sampling uniformly from its unseen items.

**Proof.** Row-uniform policies are a subset of cell policies, giving one
inequality. For the other, take any uniformly valid cell policy and relabel
the items in each row by an independent uniform random permutation. Run the
policy on these virtual labels. A new virtual label in a chosen row can be
mapped lazily to a uniform remaining physical item in that row. The chosen
virtual label and row may depend on all previously revealed scores; the
unused part of each permutation remains uniform. The resulting physical
acquisition is therefore row-uniform. For any fixed physical Y, the virtual
matrix is a row-permuted Y; its requested answer is unchanged, and the
original error bound holds for every such matrix, hence also their mixture.
Under pi, the virtual matrix has the same distribution as Y, so expected
purchase cost is unchanged. Taking infima proves the reverse inequality.
Private virtual-label histories can be retained, or merged by the preceding
state argument. This is an expected-cost symmetry result, not pathwise
equality for an arbitrary fixed Y.

The independent Bernoulli design in the protocol satisfies this symmetry.
Same-item cross-system structure generally breaks it, leaving room for
item-specific selection informed by already purchased peer scores. The
three dependent designs test for that room; the proposition alone does
not guarantee a strict improvement in any of them.

## Novelty and practical limits

- The zero-error problem is an instance of **equivalence-class determination**
  in [Golovin, Krause and Ray (NeurIPS 2010), Section 3](https://papers.nips.cc/paper_files/paper/2010/file/1e6e0a04d20f50967c64dac2d639a577-Paper.pdf).
  In our mapping, hypotheses are complete score matrices, tests reveal cells,
  and equivalence classes collect matrices with the same requested sign vector.
  Their EC2 algorithm greedily cuts prior-weighted edges between classes and
  already has a logarithmic expected-cost approximation guarantee. Our
  exhaustive optimum beating that greedy rule is not a new algorithmic idea.
  The [post-result comparison](PRIOR_WORK_CHECK.md) evaluates EC2 directly;
  at positive error it fixes EC2 acquisition and optimizes valid stopping.
- [Naghshvar and Javidi (2013)](https://arxiv.org/abs/1203.4626) already study
  adaptive test selection, stopping, error costs, and dynamic-programming
  lower bounds. [Chen, Hassani and Krause (2017)](https://proceedings.mlr.press/v54/chen17b.html)
  give an algorithm and guarantees for correlated, noisy tests. Thus neither
  adaptive decisions nor exploiting test dependence is a sufficient novelty
  claim. These are relevant boundaries, not assertions that their exact
  guarantees equal our per-fixed-matrix constraint.
- This is a six-cell problem with all 64 matrices enumerated. Its state and
  error-constraint counts grow exponentially. It is not a deployable method
  for the WMT evaluation pools.
- Each policy is optimized for the supplied synthetic design. Validity is
  robust to a wrong design distribution, but its cost advantage need not be.
- The comparator classes are explicitly restricted. The lower bounds do not
  cover arbitrary correlated blocks that revisit opened items or choose a
  current block's remaining purchases after seeing its partial outcomes.
- Stage 22 and the previous exact common-item controls are contained in the
  common-retirement class; the previous cell sampler is contained in the
  row-uniform class. This is a comparison of acquisition capability with
  unrestricted inference, not a direct rerun of their betting factors.
- [Altman's constrained decision-process work](https://www-sop.inria.fr/members/Eitan.Altman/PAPERS/h.pdf)
  develops occupancy-measure linear programs and dual bounds. Those generic
  ideas cannot be claimed as new here.
- [Active Testing](https://proceedings.mlr.press/v139/kossen21a.html) already
  optimizes label acquisition for model evaluation; [Factorized Active
  Querying](https://arxiv.org/abs/2601.20251) already uses historical models
  for direct finite-population question selection with validity guarantees.
- [Active feature acquisition](https://arxiv.org/abs/2305.02093) already
  frames costly feature requests and final decisions as sequential planning.
  A tiny separation needs a focused prior-work comparison, a useful scalable
  algorithm, and a substantive general cost result before an ICML claim.
