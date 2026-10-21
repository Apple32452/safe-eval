# Theory record: shared-label frontier allocation

## 1. Scheduler-independent simultaneous validity

For each pair p, draw a complete uniform item permutation before acquisition.
Let `Bad_p` be the event that its base sequential process makes a wrong
declaration at any prefix of that complete path, and suppose
`P(Bad_p) <= alpha_p` for every fixed outcome matrix.

Any shared-label scheduler can only cause pair p to declare at one of those
prefixes. This remains true when its choice uses outcomes from other pairs,
labels shared with future entries of p, or a prefix length that is not a
stopping time for p's own filtration. Pathwise,

    {scheduler makes a wrong declaration for p} subseteq Bad_p.

Therefore

    P(any scheduled pair is wrong) <= sum_p P(Bad_p)
                                   <= sum_p alpha_p.

The first inclusion, followed by a union bound, is the entire argument. Shared
labels change cost and dependence across declarations but do not change the
base path's anytime crossing event. This result requires each complete pair
path to have its stated randomization distribution; it does not justify
outcome-dependent construction of that path.

## 2. Continuous finite-population directional process

Let fixed values x_i lie in [-1,1], and expose a uniform permutation without
replacement. Under the composite null full mean `mu <= 0`, before draw t let
`s` be the observed sum and `r` the remaining count. The conditional mean of
the next draw is at most the boundary-null value `c=-s/r`.

For `c>-1`, fix `rho` in (0,1) and set `lambda=rho/(1+c)`. Then

    f(x) = 1 + lambda (x-c) >= 1-rho > 0

for every x in [-1,1], and its conditional expectation under the null is at
most one. The product is therefore a nonnegative supermartingale. A fixed
average of such products is also a nonnegative supermartingale. Ville's
inequality controls its probability of ever crossing `1/alpha`. Applying the
same construction to `-x` controls the reverse direction. When `c<=-1`, the
deterministic remaining-range certificate either already rejects the null or
will handle the boundary after the next draw; using factor one is conservative.

Combining the two directions with the scheduler-independent result above gives
the Stage 17 family threshold `2K/0.05 = 40K`.

## 3. What frontier utility optimizes

At a scheduling state, let `M_p` be the one or two unseen labels required to
complete unresolved pair p's current item, and let `w_p>0` be its frozen
evidence weight. Define weighted remaining prefix work after buying a label
set A, without advancing to later frontiers, as

    Phi(A) = sum_p w_p |M_p \ A|.

For one candidate label l,

    Phi(empty) - Phi({l}) = sum_{p: l in M_p} w_p = U(l).

Thus `frontier_evidence` exactly maximizes the one-step decrease in this
weighted work potential. With frontiers and weights frozen for a k-label
batch, the decrease is modular in labels, so choosing the k largest utilities
is globally optimal for this surrogate. Stage 17 recomputes after each label
because free closure advances frontiers and evidence changes.

This property does not say that the rule maximizes completed pair prefixes or
certified conclusions. That exact static objective is computationally hard:
put every missing label in one item layer, make labels graph vertices and pair
frontiers weighted edges. Selecting k labels to maximize the weight of
frontiers whose two labels are selected is weighted densest-k-subgraph. Hence
the general shared-frontier completion problem contains an NP-hard problem.
The modular work potential is a tractable, explicitly stated surrogate rather
than an unproved optimum.

## Claim boundary

The validity wrapper and optimization characterization are specific to the
shared-label problem formulation, while their proof ingredients are elementary.
They do not establish minimax label complexity, approximation of the number of
certified conclusions, or novelty over every adaptive evaluation method. Those
limits must remain explicit in any submission.
