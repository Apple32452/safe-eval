# Contribution audit, 17 October 2026

**Decision: the current SAFE-EVAL core contribution is not established as
novel.** This focused review identifies substantial overlap and checks one
proposed extension. It does not certify that no possible contribution exists.
No new WMT benchmark comparison, tuning search, or confirmatory study was run.

## Closest primary sources and the claims they block

| Source reviewed | Relevant result or released material | Consequence for our claim |
| --- | --- | --- |
| [Gao, Sicilia and Shi, Which Metrics Save the Most Human Annotation?, arXiv v2, 30 August 2026](https://arxiv.org/html/2608.26638) | Sections 4--6 study prediction-powered MT system comparison, paired/unpaired designs and annotation savings on six WMT datasets. Their experiments vary fixed labeled budgets. | Applying PPI to MT or measuring annotation savings is already explored. Our sequential precision-stopping target requires its own claim; their fixed-budget procedures are not interchangeable anytime-valid controls. |
| [Hoxha and Panxhi, MPOS replication package, posted 1 October 2026](https://doi.org/10.6084/m9.figshare.34040517) | Fixed binary populations, uniform sampling without replacement, online shrinkage of item predictions, binary-design evidence factors and integer-total confidence sequences. Selected author code also implements centered residual-variance betting and a bounded-outcome companion. | Neither this setup nor online trust adaptation can be claimed new on its own. The inspected archive has no manuscript; equivalence of every theorem has not been assessed. |
| [Mondal et al., When Can Old Evaluations Certify a New Model?, 26 September 2026](https://arxiv.org/html/2609.32267v1) | Sections 3--5 distinguish assumed historical transport from untrusted advice and give a history/current-label expert mixture valid for arbitrary advice in a finite pool. Corollary 8 gives an inflated-threshold stopping envelope; Corollary 9 analyzes expected label cost in a canonical model. | History-guided betting, drift-safe validity and a fixed raw reserve are not sufficient novelty claims. A generic mixture stopping bound is also insufficient. |
| [Fischer and Ramdas, Improving Wald's (approximate) sequential probability ratio test by avoiding overshoot](https://arxiv.org/html/2410.16076v4) | Section 2 chooses a cap and predictable boost from the conditional null expectation; Theorem 1 gives validity and earlier rejection relative to the input process. | Stage 11 applies published boosting. Adding a cap or rescaling by a valid null budget is not by itself a new framework. |
| [Wang and Ramdas, False discovery rate control with e-values, Section 4.2](https://sas.uwaterloo.ca/~wang/papers/2021Wang-Ramdas-JRSSB.pdf) | Composite-null boosting uses a supremum over null distributions; nonlinear boosting is also considered. | Requiring the worst null assignment after prediction-assisted clipping is a specialization of an existing robustness principle. |
| [Xu, Karampatziakis and Mineiro, NeurIPS 2024](https://papers.nips.cc/paper_files/paper/2024/file/6eb05d8bc6bd7bb6868c64b5802125bd-Paper-Conference.pdf) | Section 2 develops active anytime-valid risk control for an i.i.d. stream; Section 3 and Theorem 3 relate policy/predictor error to a wealth-growth surrogate. | Adaptive label collection, prediction assistance and a generic wealth-regret result are established ingredients. A finite-pool precision-cost claim needs a precise comparison. |
| [Ramdas, Ruf, Larsson and Koolen, Admissible anytime-valid sequential inference must rely on nonnegative martingales](https://arxiv.org/html/2009.03167v3) | Theorem 18 characterizes point-null admissibility; Corollary 29 supplies composite martingale admissibility conditions. | The elementary budget obstruction in THEORY.md should not be sold as a new admissibility theory. It also does not prove our implementation optimal. |

These sources have different objectives and assumptions. Their presence
blocks broad priority claims; it does not imply that they already solve every
MT evaluation problem or that their implementations are numerically identical
to SAFE-EVAL. Search terms and leads alone were not treated as theorem evidence.
This is a focused review rather than a systematic or exhaustive literature survey.

## What we derived and checked

[THEORY.md](THEORY.md) gives an exact worst-assignment budget for capped
two-outcome factors, a sorted solver for the centered residual family, and
a two-item counterexample to using historical probabilities as the null law.
Six tests passed. Independent enumeration with rational arithmetic passed
9,828 budget probes and 3,276 boost states, covering all assignments for pool
sizes 1--4 on the recorded grid. The comparator enumerates assignments rather
than reusing the sorting formula. The counterexample's actual conditional
expectation is 185/181 despite a working-model expectation of one.

**Assessment:** the correction is useful implementation mathematics, but its
current derivation combines known conditional boosting with elementary
cardinality optimization. This review does not justify presenting it as a
standalone ICML contribution. No claim is made that the counterexample has
never appeared before, that complete confidence sequences were validated,
or that this extension improves target-label cost.

## What the existing experiments actually establish

The audited [Stage 11 development comparison](../stage11/FINDINGS.md) leaves
an aligned-history prediction advantage of 0.925 labels, or 0.341%, against
the boosted raw control. Prediction wins on 15 target means and loses on 24;
both adverse histories favor the raw control on every target. This is a
small heterogeneous development effect, not evidence for a generally better
new method. The audit infrastructure and baseline diagnosis are real outputs.
They do not establish the desired novel core contribution.

A possible empirical paper angle is that apparent history-assisted savings
can shrink substantially when the raw baseline's conservatism is addressed.
That is a candidate interpretation of our development results, not a verified
new general finding. It would require independent tasks, credible competing
methods and an explanation of when the effect occurs. A new theorem is not
the only possible contribution, but a single repeatedly used benchmark cannot
establish that broader empirical claim.

## A precise unresolved research target

**Question:** Can item-level historical advice reduce precision-stopping cost
in a fixed finite pool, with a nontrivial finite-sample excess-label bound
against a strong boosted model-free control, while maintaining coverage for
arbitrary historical advice?

In plain language: determine when history saves actual human checks, and
bound the extra checks when it is wrong. This is an investigation target,
not a proven theorem or verified unoccupied gap. No method currently satisfies
this target in our work. Full confidence-set inversion, binary discreteness
and any needed progress assumptions must be stated explicitly.

The next decision should be made from a concrete mathematical statement:

1. Fix the estimand, history-error quantity, comparator, error level and
   precision rule. State an inequality for expected or high-probability
   stopping cost, and the assumptions under which it is nontrivial.
2. Derive it or find a counterexample on finite pools. Distinguish a real
   label-cost bound from a constant log-wealth gap or an inflated-threshold
   envelope. Simply applying a standard drift-to-time argument is insufficient
   to establish novelty.
3. Compare the exact statement against the primary sources above and the
   relevant references they cite. Resolve the missing MPOS manuscript before
   asserting a priority claim closely related to its released optimizer.
4. Only if a distinct claim survives, implement it and freeze an evaluation
   plan. WMT23 stays development data; confirmatory data must be checked for
   overlap and kept untouched while selecting the method. Record label-cost
   gains, adverse-history cost and coverage together.

If steps 1--3 produce only known corollaries or an impossible target, revise
the research question before another large benchmark. A positive empirical
result after repeated tuning would not resolve this novelty issue.

## What can be taken to Professor Philipp Koehn

We have an audited testbed, a baseline diagnosis and a concrete open question.
We do not yet have a verified novel method. The user's preferred sequence is
to establish a distinct result before presenting a contribution proposal.
This audit supports that sequence without promising a positive theorem or
ICML acceptance. No professor contact or message has been made.
