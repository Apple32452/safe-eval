# Budgeted reference-star screen: one gain, prespecified gate failed

Date: 2026-10-22 (US Eastern time). **Decision: no ICML novelty claim.**
The [frozen protocol](PROTOCOL.md) was committed to `main` as `6c54b62`
before running the 40-repeat synthetic study. This is fixed-matrix replay,
not a new human annotation campaign. WMT24 and new WMT25 variants were not
run. The original Stage 22 WMT25 result remains separate.

## What was tested

The task is a seven-edge reference star on eight binary-score systems and 96
items. Each system--item cell costs one label, and the checkpoint budget is
384 cells. All three methods use the same random common item order and
Stage 17 per-edge finite-pool certificate with family threshold `280`.
`pruned` is Stage 22's active-vertex schedule; `evidence_first` is the
existing cell-by-cell pair-prefix control; `footprint` uses eight paid pilot
items to forecast an edge's certificate prefix from previously revealed
scores, then buys a pair's next missing cells based on its predicted
remaining unique-label footprint. Forecasts only choose purchases; all
declarations use the original certificate. An unresolved edge at budget is
not a correct strict conclusion.

Mean strict correct directions per fixed-matrix/path pair, over 40 seeds:

| Scenario | Stage 22 pruned | Evidence-first | Footprint | Mean labels bought by all three |
| --- | ---: | ---: | ---: | ---: |
| Independent, easy gaps | 6.100 | 6.425 | 6.375 | 368.875 |
| Shared item factor, easy gaps | 7.000 | 7.000 | 7.000 | 297.425 |
| Independent, mixed gaps | 3.000 | 4.225 | 4.325 | 384.000 |
| Independent, near ties | 0.125 | 1.400 | 2.100 | 384.000 |

The stronger evidence-first control is the relevant comparator. Relative to
it, `footprint` is behind by **0.050** strict directions in easy independent,
ahead by **0.100** in mixed, and ahead by **0.700** in near ties (a 50% relative
gain on a low base). The paired standard errors of those differences are
0.050, 0.100, and 0.130, respectively; the shared-easy difference is zero.
The paired near-tie result is positive on 23/40 paths, negative on 2/40,
and equal on 15/40. These are development descriptive statistics under the
specified generators, not evidence about unseen WMT languages or new raters.

Only the near-tie setting passes the internal gate of at least 10% more
strict conclusions than **both** controls at no greater actual cost. The
frozen overall gate required three of four scenarios: **1/4, fail**. The
shared-easy setting saturates all seven edges for all policies at 384 cells;
we report that ceiling without changing the gate after seeing it.

## Audits and boundaries

- The saved-row analyzer checks all 480 rows on 160 paired matrices, the
  protocol digest, budget, categories, completeness and actual label counts.
  It found zero wrong declarations at the 384-cell checkpoint. This is an
  observation; the 0.05 taskwise family error guarantee comes from the
  original per-edge anytime certificate and union bound, not 160 successes.
- All three methods have **identical completion cost on every one of the 160
  matrices**, although their sets of certified edges differ at the 384-cell
  checkpoint. Their mean common completion costs are 386.650, 297.425,
  526.075, and 710.700 labels in the table order. This agrees with the
  [Stage 23 max-prefix boundary](../stage23/ASYNC_PREFIX_BOUNDARY.md):
  rescheduling cannot lower total cost with the same certificates and common
  item prefix. These are sample audits, not a global claim that every
  implementation path has exact equality.
- Four tests enumerate all 512 three-system, three-item binary matrices for
  exact completion and unique accounting, check a hidden-cell perturbation
  cannot alter any preceding purchase, and enumerate the offline star
  footprint formula against every subset in a small example.
- A prospective paper would need a new joint certificate or a genuinely
  different purchase and evidence mechanism, plus a matched win against a
  strong scheduler across more than one scenario. This scheduler reuses the
  old certificate and fails that empirical screen. It must **not** be sold as
  the missing ICML contribution or tested again on WMT25 after this failed
  gate.

## Closest-work check

The score-caching star objective is narrower than [Rank Confidence
Sequences](https://arxiv.org/html/2609.32211v1), which already gives shared
item anytime ranking and retirement. [CELEUS](https://arxiv.org/html/2606.20820v2)
handles adaptive finite-pool evaluation without replacement for a model;
[AnyRank](https://arxiv.org/html/2610.14603v2) studies active allocation and
anytime familywise ranking; and [Zouhar et al. (2026)](https://arxiv.org/pdf/2608.03437)
study dynamic WMT model/item allocation and prove an oracle allocation
problem NP-hard. Their settings and risk targets are not identical to ours,
but these overlaps rule out claiming that dynamic ranking allocation, shared
items, or an elementary scheduling hardness result is inherently new.

## Reproduce

From the repository root with NumPy installed:

```bash
python -m unittest discover -s experiments/budgeted_star -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python \
  experiments/budgeted_star/run_screen.py --repeats 40 \
  --output results/budgeted_star_development
python experiments/budgeted_star/analyze_screen.py \
  --input results/budgeted_star_development
```

The saved [replicates](results_reference/replicates.csv),
[metadata](results_reference/metadata.json), and
[summary](results_reference/SUMMARY.json) preserve the full screened result.
