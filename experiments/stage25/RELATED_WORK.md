# Novelty audit and baseline admissibility

## Closest primary sources

- [Cho, Gan & Kallus, PEAK, ICML 2024](https://proceedings.mlr.press/v235/cho24a.html), [sections 2--4](https://arxiv.org/html/2402.06122v3): joint composite testing for adaptively sampled streams is established. Averaging arm capital avoids a direct union-bound construction. Our finite-pool version uses the correct conditional remaining mean and a separate proof; it is not unmodified author code or the original constant-mean guarantee.
- [Kaufmann & Koolen, JMLR 2021](https://www.jmlr.org/papers/volume22/18-798/18-798.pdf): multiplying arm mixture martingales under adaptive allocation is established. This directly blocks novelty from the product component of our candidate. Their original exponential-family setup is not asserted identical to a fixed finite matrix.
- [Waudby-Smith & Ramdas, NeurIPS 2020](https://arxiv.org/abs/2006.04347): prior/posterior-ratio finite-population CSs supply the binary likelihood control. Applying their principle to multiple streams and inverting a joint region is a standard construction.
- [Shekhar et al., UAI 2023](https://proceedings.mlr.press/v216/shekhar23a.html): arbitrary adaptive finite-pool acquisition with importance weighting and side information is established. The Stage 24 HT proof and contrast-local positivity observation are not new general adaptive inference principles.
- [Ryu & Wornell, ICML 2024](https://proceedings.mlr.press/v235/ryu24a.html): vector gambling, universal portfolios and joint confidence geometry block a broad joint-CS claim. Their full-vector algorithms are not silently renamed as partial-cell procedures. A literal finite-pool substitution needs validation before comparison; see below.
- [AnyRank](https://arxiv.org/html/2610.14603v2): active allocation, graph-guided ranking and family-error control for i.i.d. environments are close in purpose. Different estimands do not establish novelty.

## What survives the audit?

The N+L extreme-star cost characterization is a useful elementary result within a compatible-completion certificate class. It is not a lower bound for all error-tolerant sequential tests. The adaptive cell policy attains that deterministic upper bound, but existing product and mixture controls do too. A local scheduling advantage over Stage 22 does not survive the stronger matched controls as a new statistical contribution.

The candidate's equal hedge, reference-first allocation and joint projection combine known mechanisms. We explicitly reject these as an ICML novelty claim. We have not proved that every possible correlation-aware partial-cell algorithm reduces to prior work; the no-go applies to this route.

## Literal WoR substitution check: unresolved source discrepancy

The [arXiv v2 section 3.2 / Appendix B](https://arxiv.org/html/2402.03683v2) substitutes the *post-observation* remaining mean into a wealth evaluated on all past observations. Interpreted literally, its categorical formula cannot be used here: in a two-item pool with one occurrence of each of two categories, after the first observation the true remaining probability of the observed category is zero. The KT numerator is 1/2, while the denominator is zero; the resulting wealth is infinite and rejects the true population with probability one. The same elementary issue affects retrospective use of this substitution more generally.

This is a counterexample to the displayed expression under that literal interpretation, NOT a finding that all Ryu/Wornell vector gambling is invalid, nor a complete audit of their author implementation or later corrections. We did not execute their code or contact authors. We therefore do not report this expression as a matched 95%-valid baseline, and cannot claim empirical superiority over their full algorithm. Correct next-step likelihood updates, used by PPR here, avoid retrospective substitution. A faithful strongest-universal-portfolio comparison remains unresolved. This exclusion blocks a comprehensive GO; it cannot strengthen our own novelty claim.

## Research gap

A substantive new direction would need a tractable confidence region for continuous fixed-matrix scores that uses partial-cell correlations and a demonstrable instance-dependent gain over these adaptive-stream controls. New query order, graph bookkeeping, joint projection and fixed hedges are not enough. A useful theorem would identify an assumption or information pattern under which shared partial observations reduce the cost beyond what independent coordinate likelihoods can already achieve, with matching lower bounds or a computational separation. That theorem has not been established here.
