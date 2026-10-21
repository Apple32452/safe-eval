# Stage 23 preliminary contribution audit

## Current decision

Stage 22 is a strong empirical result, but it is not yet an ICML-level claim.
The viable contribution is narrower than "graph-aware sequential ranking."
That broad framing is occupied by recent and classical work.

## Claims already blocked

| Broad claim | Closest reason it is blocked |
| --- | --- |
| Active selection makes test evaluation cheaper | Kossen et al. (ICML 2021) formalize active testing and unbiased adaptive test-point acquisition. |
| Sequential stopping makes model evaluation reliable and efficient | Arviv et al. (Findings of ACL 2026) directly study adaptive stopping for model evaluation. |
| Anytime-valid inference ranks many systems | Arnold et al. (JRSS B 2026) provide sequential model confidence sets. |
| A hypothesis graph can guide active multi-policy evaluation with FWER control | Badithela et al. (AnyRank, arXiv 2610.14603v2) combine sequential pair tests, active policy allocation, and graphical multiple testing. |
| Adaptive allocation plus familywise best-system inference is new | Target-aware sequential-inference work already treats predictable allocation and familywise best-system identification. |
| Pairing systems on common inputs is new | Ranking-and-selection and multiple-comparison work has long studied common random numbers. |
| Without-replacement anytime inference is new | Waudby-Smith and Ramdas (NeurIPS 2020) develop confidence sequences for finite populations sampled without replacement. |
| Adaptive finite-bank question selection with valid coverage is new | Wu, Nair, and Candès (arXiv 2601.20251) propose Factorized Active Querying with finite-population Proactive Active Inference for model accuracy under an adaptive question policy. Their target is fixed-budget accuracy intervals for a new model, not this project's graph-wide anytime sign decisions. |
| Dynamic allocation of model evaluations on WMT is new | Zouhar et al. (arXiv 2608.03437) formulate model-item evaluation effort as a budgeted allocation problem and evaluate it on WMT. Their primary objective is top-model ranking quality, not this project's familywise valid exact finite-benchmark signs. |

These sources do not automatically contain the Stage 22 result. They prevent
us from claiming novelty from any one of its ingredients or from the broad
goal of efficient sequential ranking.

## The still-plausible distinction

The remaining candidate is the joint fixed-benchmark problem:

- preserve the signs obtained on the complete, already specified test pool;
- reveal bounded system-item scores without replacement;
- charge each score once even when it supports several pairwise comparisons;
- accept an arbitrary predeclared requested comparison graph; and
- remove exactly the vertices no longer incident to unresolved claims, with a
  pathwise unique-label dominance guarantee.

AnyRank instead targets means under an i.i.d. environment distribution and
actively chooses individual policies to roll out. Its paper explicitly assumes
i.i.d. environments. It is therefore very close in purpose and graph language,
but not identical in estimand, observation structure, or cost unit. That
difference must be shown to produce a nontrivial theorem, not merely listed as
an assumption change.

## Strongest theorem candidate

Let the unresolved requested-edge set before a common item be `U`. Any policy
that promises to advance every edge in `U` by one paired common-item
observation must acquire the current score of every vertex in `V(U)`. The
Stage 22 rule acquires exactly `V(U)` and no other system on that item. Thus it
is itemwise label-minimal inside the synchronous prefix-preserving policy
class. Its per-edge prefix is identical to the full-system common control, so
each edge reaches the same certificate after no greater cumulative label cost.

The restriction matters. An asynchronous policy may focus on selected edges,
a parametric method may borrow structure, an i.i.d. ranking method may sample
policies separately, and a practical-equivalence target may stop earlier.
Stage 23 must include counterexamples and cannot call the theorem globally
optimal.

## Empirical evidence already available

On WMT25, across all 255 possible references, 14 language directions, and 50
common paths, the Stage 22 rule reduces equal-language mean completion cost
from 3,557.61 to 2,250.62 labels (37.083%; repeat-block MCSE 0.032 percentage
points). All 12,750 reference tasks improve and all audits pass. Savings fall
with graph density: 28.942% for degree-2 rings, 15.188% for degree-4 rings, and
3.004% for complete graphs.

This demonstrates materiality for sparse requested graphs. It does not by
itself prove novelty, generalization to future benchmarks, or superiority to
methods with a different estimand.

## Next action

Complete the theorem-level source comparison and small-case exhaustive proof
checks before implementing another benchmark variant. Only a passing audit
licenses a frozen WMT24 confirmation. More WMT25 tuning cannot satisfy the
novelty requirement.

## Primary sources

- Kossen et al. (2021), *Active Testing: Sample-Efficient Model Evaluation*:
  https://proceedings.mlr.press/v139/kossen21a.html
- Waudby-Smith and Ramdas (2020), *Confidence Sequences for Sampling without
  Replacement*: https://arxiv.org/abs/2006.04347
- Arviv et al. (2026), *Stop Guessing When to Stop Testing*:
  https://aclanthology.org/2026.findings-acl.43/
- Arnold et al. (2026), *Sequential Model Confidence Sets*:
  https://doi.org/10.1093/jrsssb/qkag066
- Badithela et al. (2026), *AnyRank*:
  https://arxiv.org/abs/2610.14603
- Hait et al. (2026), *Target-Aware Sequential Inference*:
  https://arxiv.org/abs/2609.37873
- Nelson and Matejcik (1995), *Using Common Random Numbers for
  Indifference-Zone Selection and Multiple Comparisons in Simulation*:
  https://doi.org/10.1287/mnsc.41.12.1935
- Wu, Nair, and Candès (2026), *Efficient Evaluation of LLM Performance with
  Statistical Guarantees*: https://arxiv.org/abs/2601.20251
- Zouhar et al. (2026), *Dynamically Allocating Evaluation Effort for Model
  Ranking*: https://arxiv.org/abs/2608.03437

