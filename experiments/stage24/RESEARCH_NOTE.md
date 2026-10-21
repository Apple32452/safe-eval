# Research note: align the stopping target with system comparisons

Date: 2026-10-21. This is a post-feedback development diagnostic, not a new
method, a pre-registered validation, or an ICML novelty claim. No WMT24
outcomes were used. The Stage 22 and Stage 23 results remain frozen.

## What Professor Koehn's feedback changes

The Stage 7 pilot chose a per-system error-free-proportion tolerance of
`epsilon=0.05`: stop when an individual 95% anytime interval is nonempty and
no more than `0.10` wide. This tolerance controls score precision. It was not
derived from a desired ability to distinguish translation systems.

Koehn's [2012 IWSLT paper](https://aclanthology.org/2012.iwslt-papers.5.pdf)
studies how many human judgments are needed to statistically distinguish
systems. It reports rank ranges and groups of systems that cannot be separated
by the available judgments. Close systems can remain unresolved at a feasible
budget. The paper's observations concern pairwise preference judgments, while
our WMT25 development matrices contain direct human scores; their tests are
not interchangeable.

Stage 22 uses a different estimand from a population significance test: the
exact sign of the difference between two recorded score means on a *fixed,
fully specified item pool*. Its anytime certificate controls erroneous
directional claims about that fixed pool, with a taskwise family guarantee;
the full-pool step deterministically reveals every sign, however tiny.
That exact result alone does not establish that a difference would be
statistically significant for new items, ratings, or annotators. A finite
pool sign can be known exactly even when a conventional inference procedure
would leave the pair unresolved.

## A reproducible gap diagnostic

`diagnose_significance_gap.py` reads only the already prepared Stage 17 WMT25
matrices and requires only NumPy. For each unordered system pair it forms
paired score differences on common items, divides their mean by their usual
sample standard error, and computes a **two-sided normal-approximation**
`p` value. It applies a per-reference-star Bonferroni cutoff
`0.05/(systems-1)`. Because every unordered pair belongs to two reference
stars, the same pairwise cutoff applies in each star. This is a simple
illustration of the distinction, not an official WMT significance test or
a valid anytime test. It treats items as independent population draws and
does not model rater variability, documents, or rating dependence.

Run from the repository root:

```bash
python experiments/stage24/diagnose_significance_gap.py \
  --data results/stage17_data \
  --output experiments/stage24/results_reference
```

Across 14 WMT25 language directions, all **2,197** unordered pairs have
nonzero full-pool recorded-score differences. Under this **illustrative**
normal approximation and per-star family correction, **1,550** meet the
cutoff and **647 (29.45%)** remain unresolved. A Student `t` sensitivity
check with the same correction gives **1,543** significant and **654**
unresolved pairs. See `results_reference/by_language.csv` and
`results_reference/summary.json`. These counts are calculated after the
WMT25 data were already inspected; they are descriptive, not held-out
evidence or a method comparison. The WMT25 recorded means also cannot
recover human-rating uncertainty that the original annotations did not
fully expose at this matrix level.

## Closest work and novelty gate

| Source | Already addresses | Remaining distinction to test |
| --- | --- | --- |
| [Koehn 2012](https://aclanthology.org/2012.iwslt-papers.5.pdf) | Pairwise significance, judgment budgets, rank ranges and unresolved groups | A modern adaptive, shared annotation cost model with honest error control needs a stronger result than reproducing this goal. |
| [Riley et al. 2024](https://aclanthology.org/2024.naacl-long.275/) | MT human evaluation stability, item-to-rater allocation, multiple ratings, and a large multi-rater dataset | Modeling annotator variability and stable ranking is already established as an objective; a sequential method would need a separate technical and empirical contribution. |
| [Song et al. 2025](https://aclanthology.org/2025.acl-long.1002/) | Side-by-side human comparisons and different MT annotation protocols | A scalar score reused across pairs is a different feedback unit from one direct comparison; compare actual human time or cost before claiming one is cheaper. |
| [Arviv et al. 2026](https://aclanthology.org/2026.findings-acl.43/) | Sequential stopping for evaluation objectives including ranking and selection | Sequential stopping or saving compute alone is occupied. |
| [AnyRank 2026](https://arxiv.org/html/2610.14603v2) | Adaptive policy ranking, partial rankings, graphical familywise testing and imperfect priors under i.i.d. environments | Investigate exact finite item pool, without-replacement observation, and reuse of one system-item human label across edges; distinguish a theorem from an assumption change. |
| [Arnold et al. 2026](https://academic.oup.com/jrsssb/advance-article/doi/10.1093/jrsssb/qkag066/8676743) | Sequential multi-model confidence sets that can leave comparisons unresolved | Another generic confidence sequence or model set is not novel. |
| [Wu et al. 2026](https://arxiv.org/html/2601.20251v3) | Finite-bank model accuracy, adaptive question selection, and historical prediction | Their published confidence theorem is fixed-budget asymptotic and their recommended sampling uses replacement. An anytime finite-bank extension must offer a substantive gain over simpler valid baselines. |

**Current decision:** Koehn's feedback strengthens the *problem definition*
and exposes a mismatch in our earlier primary objective. It does not yet
establish a novel method. The Stage 22 37.083% saving applies to finishing
all exact finite-pool signs on reference stars, not to recovering the set
of population-significant differences. We cannot reuse that number as a
significance result.

## Next falsifiable method gate

1. Declare one target before the next study: finite-pool directional
   conclusions, or inference for new items and raters. Specify an allowed
   **unresolved** outcome, target family error, candidate comparisons,
   score unit, and human label cost. Do not conflate full-data test rejection
   with a claim of practical equivalence.
2. Implement the strongest directly applicable controls: paired sequential
   confidence sequences on common items, Stage 22 graph pruning, and a
   simultaneous per-system construction with the same error target and
   unique-label accounting. If adapting a published method changes its
   guarantee, label the adaptation explicitly.
3. For an actual method contribution, prove a new joint/shared-label
   certificate or acquisition result that strictly beats the Stage 23
   fixed-prefix footprint bound *by changing an assumption of that bound*.
   First construct an adversarially correlated small-pool example and run
   exact enumeration. A scheduler that only interleaves the old pair
   certificates cannot lower completion cost under the frozen premises.
4. Predeclare synthetic comparison families (large and near-zero gaps,
   varying inter-system dependence, reference stars and dense graphs),
   budgets, and failure criteria. Report wrong and unresolved conclusions
   separately, as well as labels spent. Leave WMT24 untouched until the
   proof and baseline gate passes.

If the joint method is merely an application of existing sequential
multiple testing, report this honestly and change the paper question. No
ICML-level novelty has been established by this note.
