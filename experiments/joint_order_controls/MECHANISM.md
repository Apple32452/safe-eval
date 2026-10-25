# What joint null calibration can and cannot improve

This is a mechanism characterization using existing growth-optimal e-value
principles, not a new sample-complexity theorem or an ICML novelty claim.
It is written for the finite conditional event law used by `joint_order_gate`.

## Conditional information calculation

Fix a past history and a predictable system-selection distribution q. Let a
be the strictly positive predicted distribution on available (system, value)
events. Let K_H be the nonempty convex hull of conditional event laws of all
fixed-pool completions satisfying null H. Assume it contains a distribution
positive on the support of a. Define

    G(H,a) = sup_f sum_j a_j log(f_j)
             subject to f_j >= 0 and z dot f <= 1 for every z in K_H.

Then

    G(H,a) = min_{z in K_H} KL(a || z).

For completeness: at the minimizing z*, first-order optimality of the convex
KL objective gives `sum_j z_j*a_j/z*_j <= 1` for every z in K_H. Thus
`f*_j=a_j/z*_j` is feasible and attains KL(a||z*). Conversely, for any
feasible f and any z in K_H, Jensen's inequality yields
`sum a log(f*z/a) <= log(sum z*f) <= 0`; hence its log growth is at most
KL(a||z). This proves both directions. The numerical factor caps in the
implementation can only reduce this unrestricted optimum.

## Equality is possible even for a joint ordering test

If ordering W implies pair null H, then K_W is a subset of K_H and
`G(W,a) >= G(H,a)`. With a positive on every available event, the KL
minimizer is unique. Equality holds **if and only if** the pair-null
minimizer z*_H is also in K_W. This follows directly from set inclusion
and uniqueness, without any stopping-time argument.

At the initial equal-size pool, let independent predictive marginals satisfy
`p0 < p1 < p2` and let each q_v be positive. For the wrong order
`T1 <= T0 <= T2`, the projection for its violated pair `T1 <= T0` pools
the first two predictive means:

    r0 = r1 = (q0*p0 + q1*p1)/(q0+q1),   r2 = p2.

The pooled value lies between p0 and p1, so it is below p2. The pair
projection already satisfies the entire wrong ordering. Joint calibration
therefore has exactly the same best predicted one-step log growth as this
pair test. The analogous statement holds for swapping systems 1 and 2.
These are genuine neighboring alternatives to the predicted ranking.

Other orderings can give a strict information gain. For example, for uniform
q, p=(.1,.2,.9), and reversed order `T2 <= T1 <= T0`, the full projection
pools all three means at .4. The extreme-pair projection instead has
r=(.5,.2,.5), which violates that full ordering. Joint log growth strictly
exceeds that pair's log growth. `mechanism_check.py` compares it also with
all implied pair tests and their predictable convex mixtures.

## Why this is not a judgment-cost theorem

- G uses the predictive distribution a. It equals actual expected log
  growth only when a is the actual next-event law. Reversed priors need
  not improve actual evidence.
- Histories, remaining pools, predictions and proposals change after each
  purchase. An initial-state equality or strict inequality does not imply
  an ordering of expected stopping costs or realized costs.
- A fixed mixture of accumulated pair wealths and a product of rebalanced
  pair factors are different controls. Beating the former does not isolate
  an advantage over the latter.
- Certification requires eliminating every relevant wrong ordering.
  Improving an easy ordering may leave the difficult neighboring orderings
  unchanged. The full cost comparison is therefore essential.
- This calculation prices one cell at a fixed q. It does not compare its
  information per paid judgment with a correlated common-item observation.

The remaining research task is a cost characterization under clearly stated
conditions, together with matched comparisons that survive all these
controls. There is no general percentage threshold for novelty.

## Relationship to prior work

[Safe Testing](https://arxiv.org/abs/1906.07801) develops growth-optimal
e-variables for composite nulls. The conditional KL identity here is an
instance of those principles. [Rank Confidence Sequences](https://arxiv.org/html/2609.32211v1)
already combines pairwise e-processes with ordering elimination and model
retirement. [CELEUS](https://arxiv.org/html/2606.20820v2) already handles
adaptive finite-pool evaluation with surrogate-assisted signals. These
overlaps prevent interpreting this note or a recombination of these
ingredients alone as an established new contribution.
