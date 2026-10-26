# Conditional calibration for adaptive individual-cell queries

This implements established reverse information projection and e-process
ideas for a finite binary score matrix. Neither general principle is claimed
as novel. References include [Larsson, Ramdas and Ruf](https://arxiv.org/abs/2402.18810),
[Safe Testing](https://academic.oup.com/jrsssb/article/86/5/1091/7623686),
and [EC2](https://papers.nips.cc/paper_files/paper/2010/file/1e6e0a04d20f50967c64dac2d639a577-Paper.pdf).
The experiment tests a particular computationally tractable acquisition
policy, rather than asserting originality from these ingredients.

## Full acquisition history and directional null

Let Y be any fixed K-by-N binary matrix. The history contains every purchased
cell identity and score, historical training data, and earlier policy
randomness. Before the next score is read, choose probabilities q_c over
unseen active cells and factors f_c(0), f_c(1). Predictors and probabilities
may depend on observations in the same item's other systems. Each active
unseen cell has positive selection probability.

For direction a>b, the null is T_a<=T_b, where T_v is the full row total.
Let d be the observed sum for a minus that for b. Unobserved bits obey

    d + sum_{c in row a} y_c - sum_{c in row b} y_c <= 0.

All other unobserved cells are unrestricted. To obtain a valid conditional
e-factor it is enough to require, for every compatible null completion,

    sum_c q_c f_c(y_c) <= 1.

Multiplying the factors selected at successive queries gives a nonnegative
supermartingale under that fixed null in the **full** acquisition filtration.
Dependence between systems, chosen cells, and earlier peer scores is allowed.
Prediction accuracy is unnecessary for this inequality.

## Fast exact support calculation

For each endpoint row, order its cells by decreasing increment
q_c*(f_c(1)-f_c(0)). The best factor sum among configurations with j ones is
the sum of q*f(1) on the first j entries plus q*f(0) on the remaining entries.
Compute this for all j with prefix and suffix sums. For a-count j, the b-count
must be at least max(0,d+j). A suffix maximum of b's values therefore gives
the best allowed b-count. Maximize over j, then add each other row's sum of
q_c*max(f_c(0),f_c(1)). This is the maximum over **all** compatible binary
null matrices, without enumerating them.

Sorting costs O(N log N) for the two endpoints; the remaining sums are linear
in active cells. The implementation uses sums of nonnegative numbers instead
of subtracting large likelihood ratios. This support calculation is verified
against direct enumeration in the small-state tests.

## Proposal factors from a one-dimensional convex projection

Given cell predictions r_c, the predicted distribution of the next event is
Q(c,1)=q_c*r_c and Q(c,0)=q_c*(1-r_c). The convex hull of compatible binary
null matrices is the box [0,1] with the above single integer pair inequality;
its vertices are integral. The reverse information projection minimizes

    sum_c q_c KL(Bernoulli(r_c) || Bernoulli(z_c))

over that box and inequality. Cells outside the pair use z_c=r_c. If r itself
satisfies the null, the unit factor is optimal. Otherwise the constraint binds.
For a row-a cell put t=lambda/q_c. The KKT solution is

    z_c = 2*r_c / (1+t + sqrt((1+t)^2 - 4*t*r_c)).

For row b use one minus this expression with r replaced by 1-r. Bisection
on lambda enforces the total constraint. The proposed factor is r/z for
outcome 1 and (1-r)/(1-z) for outcome 0. The variational inequality for the
convex projection proves its null expectation is at most one in exact
arithmetic. This is an application of the existing log-optimal e-variable
construction.

The implementation clips z away from 0/1, recomputes the full null maximum,
and divides by max(1,maximum)*(1+1e-9). Validity relies on this last support
calibration, not numerical optimizer optimality or correct predictions.
Floating-point calculations have a conservative buffer and audited support
checks; the software is not an interval-arithmetic formal proof.

## Simultaneous comparison decisions and paid costs

For E requested pairs, run two directional products for each pair and reject
a null when its product reaches 2E/alpha. Ville's inequality and a union
bound yield probability at most alpha of any incorrect declared sign at any
time. Logical bounds from observed sums and unknown counts can also decide
a strict sign without error. Equality is reported only after both rows have
been fully observed. Purchased cells can contribute factors to multiple
comparisons; they are charged once. On any unfinished edge, both endpoints
remain eligible, so full acquisition must eventually complete every pair.

The common-item control uses the analogous conditional factor constraint
over all integer remaining histograms of paired differences in {-1,0,1}.
Its small set of vertices is checked against every histogram in tests.
Legacy ordering-closure controls retain their original, stronger familywise
construction, rather than being forced to use Bonferroni thresholds.

## Scalability and known boundaries

The calibration step is polynomial in N and the number of requested edges;
it does not enumerate 2^(K*N) full score matrices. The study's categorical
predictor does enumerate 2^K column patterns and 3^K observation patterns.
It is practical for the tested K=3 and K=5, but a larger-system deployment
would need a different predictor. Any predictable predictor can replace it
without changing the support-calibration argument.

The EC2-based control samples 256 compatible matrices for acquisition only.
Its classification and edge-cut calculation approximate the established EC2
criterion, then randomize in proportion to gains with a fixed uniform floor.
This is not an exact reproduction of EC2 or its approximation guarantee.
Reported comparisons depend on the full frequentist calibration, not on
the sampled matrices covering every possible truth.

Polynomial inference and a fast implementation do not imply a cost advantage.
This study must beat the same-inference row-uniform ablation and the stronger
paired and ordering controls before further empirical expansion.
