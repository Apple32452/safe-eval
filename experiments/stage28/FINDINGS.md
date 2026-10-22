# Stage 28 decision: coupled queries help partial labeling, but fail the paired-label cost gate

Date: 2026-10-22. This was a **frozen synthetic gate** for the prospective
item–rater target in [the protocol](README.md). The full data are the
[3,500 method trajectories](results_reference/REPLICATES.csv) and the
[summary plus exact audit](results_reference/SUMMARY.json). An
[independent saved-result analysis](analyze_stage28.py) verifies the digest,
population signs, accounting, decisions, aggregates and predeclared gate.

## Cost to completion

The table reports mean purchased judgments per run, from 100 shared item/rater
ledgers per scenario. Every method completed **100/100** runs in the four
non-tie scenarios, and none completed an exact tie by the 1,600-round cap.
Zero false directional declarations were recorded across 3,500 trajectories;
the worst-case error guarantee comes from the stated prospective iid design
and pre-draw e-process proof, **not** from that observed count.

| Method | Aligned | Weak | Reversed | Opposing residuals |
| --- | ---: | ---: | ---: | ---: |
| Paired, fixed mixture | **207.41** | **597.98** | **246.70** | **752.28** |
| Paired, adaptive mixture | 233.52 | 656.93 | 270.89 | 758.65 |
| Independent queries, fixed mixture | 495.35 | 913.30 | 527.92 | 1,181.32 |
| Coupled queries, fixed mixture | 342.91 | 732.58 | 371.33 | 1,186.47 |
| Independent queries, adaptive mixture | 510.31 | 937.55 | 543.93 | 1,185.70 |
| Coupled queries, adaptive mixture | 353.90 | 758.51 | 383.54 | 1,193.16 |
| Coupled queries, adaptive allocation | 403.25 | 914.86 | 490.14 | 1,198.17 |

Coupling at identical marginal propensity `0.75` reduced label cost by
**30.8%, 19.8%, and 29.7%** relative to independent partial queries in the
aligned, weak, and reversed scenarios. It increased mean cost by 0.4% in
the opposing-residual scenario. That last difference is uncertain: a paired
bootstrap across the 100 ledgers gives a descriptive 95% interval for the
extra labels of `[-122.26, 133.73]`. The exact conditional query variance
calculation explains why positive residual covariance favors a shared coin
and negative covariance can hurt. This is a known common-randomness
mechanism, not a new statistical principle.

The strongest coupled variant here, with fixed mixture, still required
**135.50, 134.60, 124.63, and 434.19 more labels** on average than the
paired fixed control in the four scenarios. Paired ledger bootstrap 95%
descriptive intervals for those differences were respectively
`[119.40, 152.60]`, `[109.33, 160.70]`, `[110.32, 140.13]`, and
`[332.20, 543.14]`. Both methods completed all 100 runs, so these are
costs to actual conclusions rather than costs of unresolved runs.

The particular history-based regularized Kelly component reduced efficiency
relative to a fixed mixture in this pilot, including on complete paired
labels. History-based residual allocation was also more expensive than
fixed coupled propensities. These results do **not** rule out established
variance-adaptive confidence sequences; the pilot did not implement the
stronger empirical-Bernstein off-policy method.

On exact ties, no method resolved all three edges. Paired labeling cost
4,800 judgments at the cap, while the partial methods cost about 4,000;
the lower partial cost did not produce a supported ranking and is excluded
from the efficiency gate.

## Scientific decision

All three joint variants met the non-tie completion requirement but were
cheaper than neither paired control in **zero of four** scenarios. The
predeclared gate required at least three of four. **Stage 28 fails.**
There is no ICML-level contribution from this rule or this result.

Prior work already covers [variance-adaptive anytime-valid off-policy
inference](https://arxiv.org/abs/2210.10768),
[dynamic allocation in human model ranking](https://arxiv.org/abs/2608.03437),
and [anytime pairwise ranking](https://arxiv.org/abs/2609.32211).
The present pilot did not implement these stronger comparators and therefore
does not establish superiority to them. WMT25's existing annotation bank
does not supply the prospective rater sampling assumed here; WMT24 remains
uninspected. A further proposal needs a distinct theorem or a material
gain over those methods under matched annotation cost, completion, and
error guarantee, ideally with genuinely randomized annotator collection.
