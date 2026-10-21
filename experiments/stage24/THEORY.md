# Joint design-based finite-pool betting: proof and boundary

## 1. General acquisition model

Fix arbitrary scores X_vi in [0,1], v=1..m, i=1..N, and mu_v=N^{-1}sum_i X_vi. The filtration contains all past acquisitions, scores, randomization and fixed auxiliary information. Let O_t be observed cells just before acquisition, S_v their sum for system v. Choose a randomized subset B of unobserved cells, with known strictly positive marginal inclusion probabilities pi_vi for every unobserved cell, measurable BEFORE revealing B's scores. Any within-batch dependence is allowed. Outcomes must not be used to retroactively choose pi. Define

    Z_v = (S_v + sum_{i:(v,i) in B} X_vi / pi_vi) / N.

By linearity of conditional expectation, E[Z_v|past]=mu_v for each coordinate. No independence, transport, covariance or correctness-of-advice assumption is needed. Cached observations are counted in S once, never reacquired. A deterministic next cell with zero probabilities elsewhere does NOT satisfy these premises. More efficient augmented prediction corrections are possible but not used here.

## 2. Joint CS

For every vector null theta, choose a predictable vector b_t(theta) such that 1+b_t(theta)'(z-theta)>=0 on the entire possible next-step support. Then

    M_t(theta)=product_{s<=t}[1+b_s(theta)'(Z_s-theta)]

is a nonnegative martingale at theta=mu (or a supermartingale with conservative arithmetic). Conditional expectation of the factor equals one. Ville gives P(exists t:M_t(mu)>=20)<=0.05. Intersect all earlier acceptance sets and deterministic remaining-range constraints. One joint set C_t contains mu at every acquisition time with probability >=0.95. Projecting C_t onto ANY predeclared pair differences gives 95% anytime-valid familywise coverage, with no pair-count union penalty. Only declare a sign if all surviving vectors have that strict sign; a tie requires every survivor's difference be exactly zero. If the set is empty, make no new declaration. Keep previous declarations irreversible. At full acquisition, the deterministic totals are exact and may be reported regardless of an earlier statistical failure. A new sign error anywhere implies exclusion of the true vector at some time, so optional stopping and all requested comparisons are covered by the same event.

There is no union over theta: only the process at the one true vector matters. Covariance can choose bets predictably; plugging an empirical covariance into an unproved Gaussian boundary would NOT be justified.

## 3. Implemented whole-row specialization

Unseen rows have integer weights w_i>=1; W=sum_i w_i and p_i=w_i/W. Draw one row I and reveal all systems. The joint innovation is Z=(S+W*X_I/w_I)/N. Choose integer d(theta) in {-1,0,1}^m by the sign of (C+I/4)^{-1}(past_smoothed_mean-theta), where C is the empirical covariance of PREVIOUS rows. The diagonal ablation deletes off-diagonals. This direction is a heuristic, not a proven optimal bet; integerization is deliberately simple and frozen.

Let K=N theta be an integer binary-total vector; D=d'(S-K), A=sum_v min(d_v,0), wmin=min_i w_i, and L=max(wmin,-wmin*D-W*A). Then b=N*wmin*d/(2L) and

    factor = 1 + wmin*(w_I*D+W*d'X_I)/(2L*w_I).

For every possible binary/bounded row and every I, d'X_I>=A and W/w_I<=W/wmin. Thus d'(Z-theta)>=-L/(N*wmin), giving factor>=1/2. The formula uses exact integers in the binary solver. The factor expectation is exactly one at the true K under the specified weighted draw. Weights may depend on all previous labels and auxiliary features. Use all-one weights for the uniform arm. No claim of optimal covariance exploitation is made.

## 4. Numerical and model scope

Inversion enumerates {0,...,N}^m: it is exact for binary observations, NOT continuous MT scores. Integer numerators/denominators are restricted below 2^53 so binary64 represents their inputs exactly. Round each rational factor downward using nextafter; multiply nonnegative wealth downward as well. This capital is dominated by the real-valued martingale, so rejection at lower-wealth>=20 is conservative. Underflow is safely rounded to zero; no overflow is allowed. Covariance calculations need not be interval-certified because they only select a predictable, bounded integer bet. The proof assumes IEEE binary64 with ordinary rounding and no unsafe fast-math. Fraction tests independently check domination on small states, not every machine/platform implementation.

At within-row acquisition times, hold C fixed until the batch completes: no unproved mid-batch update is used. The general theorem allows randomized subsets but only whole rows are tested. Full-grid cost grows as (N+1)^m, blocking realistic multi-system WMT use. Replacing this solver by a coarse grid can discard the true vector and invalidate coverage. Empty sets are not evidence of arbitrary signs.

## 5. What has been added, and what has not

This is a self-contained specialization of known inverse-probability design correction plus vector test-martingale inversion. The confidence-set proof and joint projection are standard; no original theorem is asserted. Stage 23's fixed-certificate lower bound does not apply because these are different certificates. An empirical win would not itself establish novelty, and a loss of this particular integer-direction strategy would not disprove benefits of all joint CSs.
