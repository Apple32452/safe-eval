# Focused novelty review, 17 October 2026

This review assesses the actual Stage 9/10 construction. It is a focused
primary-source comparison, not a proof that every related method has been
exhaustively surveyed. None of the ingredients below establishes an ICML
contribution by itself. The benchmark comparison concerns one calibrated PPR
family and does not yet implement every stronger published procedure.

| Primary source and location | Established overlap | Consequence for SAFE-EVAL |
| --- | --- | --- |
| Waudby-Smith & Ramdas, [Confidence sequences for sampling without replacement](https://arxiv.org/html/2006.04347v4), Theorem 2.1 and Section 2.3 | Finite binary pools, hypergeometric PPR confidence sequences, running intersections, and choice of working prior. | Ordinary raw95 is an implementation of this known construction. Finite-population anytime validity and a useful working prior are not new claims. |
| Waudby-Smith & Ramdas, [Estimating means of bounded random variables by betting](https://arxiv.org/html/2010.09686v7) | Betting-based confidence sequences, predictable choices, variance adaptation and without-replacement extensions. | Our predictable betting and capital inversion reuse this framework. Implementation and numerical audits do not independently establish a new statistical method. |
| Csillag et al., [Prediction-Powered E-Values](https://arxiv.org/html/2502.04294v2), Theorem 2.1, Proposition 2.3 and Section 2.1; [ICML 2025 proceedings](https://proceedings.mlr.press/v267/csillag25a.html) | Prediction-corrected e-values/e-processes, anytime confidence sequences, and prediction/collection rules updated from past observations. The construction uses predictable Bernoulli label collection. | The broad claim that predictions plus sequential correction yield anytime validity is already established. Our fixed-pool query design differs, but a setting difference alone is insufficient novelty. No reduction between the exact implementations has been established here. |
| Ashouritaklimi et al., [Prediction-Powered Active Testing](https://arxiv.org/html/2607.08347v1), Propositions 3.1/3.2 and Section 4 | Finite-pool control-variate correction with active sampling, unbiasedness for fixed trust, variance analysis, and asymptotic confidence intervals. | Prediction-assisted finite-pool unbiasedness and useful proxies are not new. Its stated asymptotic interval result differs from our finite-pool time-uniform certificate; that difference must also be assessed against the already-anytime-valid e-value literature. |
| Li et al., [Robust Sampling for Active Statistical Inference](https://arxiv.org/html/2511.08991v1), Theorem 1 | Budget-preserving paths between active and uniform allocation, with asymptotic variance no worse than either endpoint under consistent tuning. | Robust fallback ideas have substantial precedent. Stage 9 instead leaves acquisition uniform and bounds stopping cost against a specified raw rule. Variance and pathwise stopping cost are distinct guarantees. |
| Fischer & Ramdas, [Improving Wald's approximate sequential probability ratio test by avoiding overshoot](https://arxiv.org/html/2410.16076v4), Section 2, Section 4.1 and Section 4.2 | Sequential boosting improves martingale tests while preserving error control; the improved tests stop no later than their base tests. Extensions include confidence sequences and sampling without replacement. | A never-later sequential safeguard is not a first-of-its-kind claim. The published boosting construction is a material missing comparison. Stage 10 refines thresholds but does not implement boosted PPR or prove dominance over it. |
| Ding et al., [Reference-Null Calibrated Thresholds for E-Processes](https://arxiv.org/html/2609.32678v1), Theorem 2.2 | Finite-horizon boundary calibration from exchangeable independent null trajectories, preserving type-I error. | Improving universal Ville thresholds using the particular null law is an established research direction. Our exact integer enumeration over all finite totals avoids simulated reference trajectories, but this is an implementation/setting distinction requiring further novelty analysis. |

The review inspected the cited theorem/section text rather than inferring
missing guarantees solely from abstracts. No claim is made that PPR
calibration, unbiased residual correction, predictable trust, e-process
mixtures, union bounds, confidence-set intersection or empty-set fallback
is individually novel.

## Exact current claim and its limits

The current construction certifies the implemented raw PPR rule's worst
full-path error for three fixed binary pool sizes. It spends only the
certified spare error allowance on an unchanged prediction confidence
sequence, intersects with raw95, and falls back to raw95 on empty output.
Containment supplies a pathwise ordinary-raw95 stopping bound at the same
nominal .95 coverage. Stage 10 asks how much empirical advantage remains
when model-free PPR calibration is finer and repair is explicitly examined.

This is a clear, reviewable engineering/statistical claim. The current
derivation combines known arguments. The strong reference-null information
used in exact finite-state calibration must be stated, as must the cost of
certification and the limited pool sizes. A small gain on inspected WMT23
data cannot establish generality, novelty or total annotation-cost benefit.

## Decision gate before an ICML claim or new confirmation campaign

1. Implement or rigorously compare the applicable sequential-boosting
   baseline, including its candidate-wise inversion and numerical validity.
   Do not treat a finer constant PPR threshold as the best model-free CS.
2. Explain a nontrivial new technical insight or compelling new empirical
   finding beyond the combinations above. Ask a knowledgeable supervisor
   whether the exact contribution is substantial enough to pursue.
3. If that case survives, lock an uninspected public annotation pool, retain
   all languages/systems/shifts, and account for historical-data costs.
   Previously inspected WMT23/WMT24 pools remain development data.
4. If stronger controls remove the useful-history advantage, report that
   result and revise the research question before scaling experiments.

No private benchmark data, additional human annotation or external messages
were used or sent for this study.
