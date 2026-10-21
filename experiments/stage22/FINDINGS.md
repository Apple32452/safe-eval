# Stage 22 findings: graph-aware reference comparison

## Primary result

The frozen development gate passes. Across all 255 possible reference systems,
14 WMT25 language directions, and 50 matched common-item streams (12,750
reference tasks), active-vertex pruning reduces the mean cost of certifying all
reference-versus-candidate conclusions from **3,557.61** to **2,250.62** unique
system-item labels. The equal-language relative saving is **37.083%** with a
conditional repeat-block Monte Carlo standard error of **0.032 percentage
points**.

Every one of the 12,750 task instances has a positive saving. Individual task
savings range from 5.856% to 76.543%, and all 14 language-level means are
positive. The smallest language mean is 12.059% (`en-mas_KE`) and the largest
is 56.762% (`en-is_IS`). Final decisions agree exactly between methods and
with the full-pool signs. The audit found zero per-edge resolution-cost
dominance violations.

| Requested graph | Mean relative label saving |
| --- | ---: |
| Reference star | 37.083% |
| Name-sorted ring, degree 2 | 28.942% |
| Name-sorted ring, degree 4 | 15.188% |
| Complete graph | 3.004% |

The monotone density pattern supports the structural explanation: pruning is
most valuable when resolving an edge removes a low-degree system from future
annotation. It has little opportunity on a complete graph because almost every
system remains incident to an unresolved edge. The complete-graph number above
uses cost to finish all requested edges and is not directly comparable to
Stage 20's 0.665% increase in conclusions at a fixed 75% label budget.

## Fixed-budget behavior

Equal-weighted reference-task means are:

| Full label budget | Method | Correct | Wrong | Unresolved | Labels actually used |
| ---: | --- | ---: | ---: | ---: | ---: |
| 25% | common | 2.920 | 0 | 14.294 | 923.56 |
| 25% | pruned | 3.462 | 0 | 13.752 | 919.50 |
| 50% | common | 7.435 | 0 | 9.780 | 1,839.87 |
| 50% | pruned | 9.214 | 0 | 8.000 | 1,738.21 |
| 75% | common | 11.072 | 0 | 6.142 | 2,739.44 |
| 75% | pruned | 14.895 | 0 | 2.319 | 2,179.33 |

Labels can be below the nominal checkpoint when every requested edge has
already resolved. No wrong declaration was observed at the saved checkpoints;
the formal claim remains the taskwise family guarantee rather than an empirical
zero-error probability.

## Verification

- Nine Stage 22 implementation and merge invariants pass.
- The full package contains 14,850 graph-task rows and 89,100 checkpoint rows.
- The audit replayed all 297 repeat-zero graph tasks and 1,782 corresponding
  checkpoints from the original unsharded runner.
- All 12,750 reference tasks and all 2,100 density diagnostics satisfy total
  cost dominance; every requested edge resolves at no greater cumulative cost.
- WMT25 source and matrix hashes match the frozen Stage 17 preparation.
- WMT24 outcomes remain untouched.

The first single-process full command was interrupted before writing output
because it was unnecessarily slow. `AMENDMENT_1.md` records the execution-only
language sharding. The method, seeds, thresholds, data, metrics, and gate were
unchanged, and the independent audit replay is unsharded.

## Claim boundary and next decision

This is the first large, broad empirical effect produced by the Stage 20
pathwise theorem, and it establishes that the mechanism is materially useful
for the reference-system comparison objective. It does **not** yet establish
an ICML contribution.

Active testing, online model selection, recent adaptive evaluation, sequential
model confidence sets, multiple comparisons with a control, and model-racing
methods may overlap with parts of the formulation. Before touching WMT24, the
next phase must perform a definition- and theorem-level novelty audit, freeze a
paper-level method and baseline suite, and decide whether exact finite-pool
shared-label graph pruning is genuinely distinct. Only then may WMT24 serve as
one untouched confirmation run.
