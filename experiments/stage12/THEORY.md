# Finite-assignment budgets for capped prediction factors

This is a checked derivation for the novelty audit. It is an elementary
specialization of robust null budgeting and published sequential boosting,
not a claimed new statistical framework. The reference program implements
one-step calculations only.

## Conditional experiment

Before a query, r items remain. Their binary labels y_i are fixed and unknown,
with sum k under the candidate total being tested. The next item I is uniform
over the remaining items. All predictions m_i and the stake theta have been
fixed using information available before I and y_I are observed. Predictions
may be arbitrarily inaccurate. Let mu = sum_i m_i/r and q = k/r.

Consider the nonnegative factors

    f_i(y) = 1 + theta * (y - m_i + mu - q).

For every feasible assignment, averaging over the next uniform item gives

    E[f_I(y_I) | past, fixed assignment] = 1.

This follows directly from sum_i(y_i-m_i+mu-q) = 0. Nonnegativity must hold
for all possible next outcomes; the code rejects stakes that violate it.

## Assignment maximum after clipping

For any nonnegative two-outcome factor table, multiplier b >= 1 and cap H > 1,
write u_i(y) = min(b*f_i(y), H), and d_i = u_i(1)-u_i(0). Then

    max_{y in {0,1}^r: sum y_i = k} E[u_I(y_I)]
      = (sum_i u_i(0) + sum of the k largest d_i) / r.             (1)

Proof: every assignment contributes the same sum_i u_i(0), plus d_i for
exactly k indices. Selecting the k largest increments maximizes that sum.
Negative increments and ties cause no difficulty. This is a fixed-cardinality
selection identity, not a new general optimization theorem.

For the centered factors above, d_i is nondecreasing in m_i for either sign
of theta. If theta > 0, increasing m_i shifts both untruncated factors down,
so their positive clipped difference increases or remains constant. If
theta < 0, increasing m_i shifts both factors up; their negative difference
becomes less negative or remains constant. Thus a worst assignment places
the k ones at the largest predictions, for every b. The theta = 0 case is
constant. The reference checks both signs, endpoints and ties.

Let v_i be the factor realized by that assignment. Choosing a feasible boost
reduces to the piecewise-linear budget

    sum_i min(b*v_i, H) <= r.                                   (2)

The v_i sum to r, so b = 1 is feasible. Sort positive v_i in decreasing order.
With j of them saturated, the equality root is

    b = (r - j*H) / sum_{unsaturated i} v_i.

Accept it when it lies before the next saturation point H/v_i; otherwise
saturate that value and continue. If H times the number of positive values
is <= r, no finite largest multiplier exists. The code returns a finite
multiplier that saturates every positive value, which has the same factors
as the limit. Zero factors stay zero.

At a sequential state with wealth 0 < W < B, use H = B/W. Satisfying (1)
conditionally at every step makes the product a nonnegative supermartingale
under every fixed null assignment. With unit initial wealth, the usual
threshold B = 1/alpha therefore controls crossing probability by alpha.
Handle zero wealth, absorbed rejection and exhausted pools separately.
This is the standard conditional-expectation argument underlying sequential
boosting [Fischer and Ramdas, Section 2.1, equations (9)--(12)](https://arxiv.org/html/2410.16076v4).
It does not establish optimality against other methods. No full confidence
sequence or WMT implementation is supplied in this stage.

## Why historical probabilities cannot supply the null expectation

Take r = 2, k = 1, m = (1/10, 9/10), theta = 1 and H = 3/2. The factor table is

| Item | f_i(0) | f_i(1) |
| --- | --- | --- |
| 1 | 9/10 | 19/10 |
| 2 | 1/10 | 11/10 |

Under the working Bernoulli probabilities m_i, the capped expectation near
b = 1 is (181/200)*b + 3/40. Setting it to one gives b = 185/181.
For the feasible fixed assignment y = (0, 1), neither observed branch clips,
and the actual conditional expectation is instead

    ((9/10)*b + (11/10)*b)/2 = 185/181 > 1.

The robust budget forces b = 1 in this state. The example refutes the
conditional supermartingale justification for the proposed shortcut; it
does not demonstrate a complete confidence-sequence miscoverage rate.
Neither Stage 11's raw PPR boosting nor our preserved prediction processes
use this shortcut. The example belongs to a proposed extension only.

## Limits of stronger proposed claims

An exact martingale already spends its full conditional expectation budget.
If its next wealths a_i(y_i) average to W for every feasible assignment, a
proposed update from the same W cannot be at least a_i(y_i) on every branch
and strictly larger on any feasible branch while still averaging <= W.
For a fixed assignment, the nonnegative differences must sum to zero; varying
the assignment covers all feasible branches. This elementary obstruction
concerns one-step wealth domination. It does not prove that the Stage 11
integer implementation is globally optimal, or rule out better intervals,
average stopping costs, or methods with additional assumptions.
The broader admissibility theory is already developed in
[Ramdas et al., Theorem 18 and Corollary 29](https://arxiv.org/html/2009.03167v3).

A constant wealth regret also does not give a constant query delay by itself.
For a threshold B > 1, take an event of null probability 1/B. A reference
martingale starts at 1, becomes B on that event and zero otherwise at time 1,
and then stays fixed. Another valid nonnegative supermartingale starts at 1,
becomes c times the reference for any 0 < c < 1, and stays fixed. On the event,
the log-wealth gap is only -log(c), but the second process never reaches B.
This generic example shows why converting evidence regret to a label-cost
bound needs further progress or margin conditions. It is not a new
finite-population impossibility theorem.
