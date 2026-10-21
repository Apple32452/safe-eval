# Adaptive partial-cell inference: guarantees, separation, and reduction to known methods

## 1. Sampling filtration and joint coverage

Fix any binary matrix X in {0,1}^{m x N}; system totals K_v are unknown. At cell time t choose a system A_t using only past scores and external randomization. Conditional on this choice, draw I_t uniformly among that system's unobserved items, using fresh randomness. Other systems may already have exposed the same item: this does not alter the uniform draw over the selected system's fixed remaining entries. The system-item outcome is charged once and cached. There is no i.i.d. or cross-system independence assumption.

For candidate total k and chosen system v with s observed successes out of n observations, the next outcome's null probability is p_k(1)=(k-s)/(N-n). Let the alternative predictive probability be q(1)=(s+1)/(n+2), fixed before the draw. Update only that system's capital by q(Y)/p_k(Y), others stay unchanged. At the true total the conditional expectation is sum_{y:p_k(y)>0} q(y)<=1. It equals one for interior null probabilities; at support boundaries this is a SUPERmartingale, not necessarily a martingale. Candidate totals inconsistent with observed successes/failures are removed deterministically. Values assigned to zero-probability paths do not affect validity at the true null. Use factor zero there rather than division by zero.

For every joint null vector k, the product P_t(k)=product_v M_{v,t}(k_v) is a nonnegative supermartingale: only one factor changes, with conditional mean <=1 in the FULL acquisition filtration. Multiplying arbitrary correlated simultaneous e-values would not be valid; the single updated factor and its conditional guarantee are essential. The arithmetic mixture A_t(k)=sum_v M_{v,t}(k_v)/m is also a supermartingale. Hence H_t=(P_t+A_t)/2 is one. Ville yields

    Pr(exists t: H_t(K)>=20) <= 0.05.

Intersect the acceptance region H_t(k)<20 over times and with the exact coordinate ranges [s_v,s_v+N-n_v]. Project the surviving full grid onto all requested pair differences. Report strict + or - only when all survivors have that sign; report equality only when all survivors have zero difference. Empty confidence sets yield no new declarations. Previously declared signs are irreversible. Any wrong declaration implies exclusion of K at some time; thus probability of ANY wrong requested sign, at ANY cell time or stopping rule, is <=0.05. The same proof applies separately to P and A. It does not grant joint 95% coverage across all methods.

This is a standard likelihood/test-supermartingale construction. The confidence principle and product/mixture aggregation are NOT new. The tested hedge is not the universal portfolio algorithm.

## 2. PEAK-style matched finite-pool control

The original PEAK assumes a constant conditional arm mean. For a fixed finite pool the correct predictable null center at a selected-system draw is c_k=(k-s)/(N-n), not k/N. Use its scalar factor

    1+(a-c_k)(Y-c_k)/(13/50),

where a=s/n for n>0 and a=c_k initially. For a,c_k,Y in [0,1] the product (a-c_k)(Y-c_k)>=-1/4, so the factor is >=1/26>0. At the true K its expectation is exactly one, including support boundaries. Update only the chosen arm and average its capitals as in PEAK. This establishes the same 95% joint event. It is a finite-pool adaptation with a new conditional-expectation check here, not a claim that PEAK's unmodified i.i.d. formula is valid on a finite pool. No published PEAK optimality or convexity claim is inherited.

## 3. Strict cost advantage: a conditional, elementary separation

Consider a star with L leaves, N items, reference scores all one and every leaf all zero. Let a reference ones and b_l leaf zeros have been revealed. Without a structural assumption, compatible completions give reference lower total a and leaf upper total N-b_l. A zero-error strict reference-win certificate is therefore possible exactly when

    a+b_l>N, for every leaf l.

Its unique-label cost obeys

    a+sum_l b_l >= L(N+1)-(L-1)a >= N+L.

Querying the N reference scores and one zero from each leaf attains N+L. Thus N+L is the exact minimum inside the compatible-completion, zero-error certificate class on this matrix. This is NOT a lower bound for all 95%-valid randomized procedures: those may accept some error risk and use statistical certificates.

For the unchanged Stage 22 certificate, call its first all-one-difference resolution prefix t_N(L), which is deterministic on this population. With common within-item order reference then leaves, every edge resolves after the same t_N paired observations and Stage 22 uses (L+1)t_N labels. Therefore the partial-cell rule costs at most N+L and is strictly cheaper whenever

    N+L < (L+1)t_N(L).

For L=2, the original frozen engine gives t_4=3, t_6=4, t_8=5: upper costs 6/8/10 versus 9/12/15. Any earlier statistical stop can only reduce the partial-cell upper cost. These are exact benchmark-specific separations, not novel sample-complexity theory. Product-PPR and mixture-PPR controls with the SAME allocator inherit the same deterministic upper bound. Accordingly this witness cannot establish novelty or a gain against the strongest joint alternatives.

This escapes Stage 23's max-prefix identity by changing the pair certificates and permitting unequal coordinate prefix lengths. Merely reordering fixed pair certificates would not do so.

## 4. Why correlation and full generality remain unresolved

Under arbitrary bounded matrices, observed correlations do not make unobserved cells equal or predictably known. If two matrices agree on every queried cell but have opposite requested signs, every zero-error completion-based certificate must remain unresolved. A minimal example observes system 0's first entry as 1 and system 1's first as 0 in a two-item pool. Completion (system0 second=0, system1 second=1) is a tie; completion (1,0) is a strict win. An observed one-item ordering alone cannot justify a strict full-pool ordering.

For general unequal-probability acquisition, an unbiased linear contrast correction needs positivity only on unobserved cells with nonzero contrast coefficient. Zero probability on an unknown cell with nonzero coefficient omits its contribution and breaks the correction. If the next system is deterministic, this particular unbiased HT construction cannot bet nontrivially on other systems' unknown scores at that step. This is a limitation of that construction, not a general impossibility theorem. Randomizing across systems or adding justified structure changes the problem and its variance costs.

The present joint set is driven by coordinate likelihoods, not a new correlation-sharing certificate. Its binary inversion costs (N+1)^m; arbitrary continuous scores require a new solver or valid outer region. A coarse numerical grid would not preserve the guarantee. Unknown propensity, deterministic outcome-biased item selection, or retrospective changes to bets invalidate this proof. A genuinely new continuous-score, correlation-exploiting partial-cell method with an instance-dependent efficiency theorem is still open here.
