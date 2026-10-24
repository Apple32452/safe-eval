# Joint cell bets: a valid cancellation, but no individual certificate

Research diagnostic, 2026-10-23 US Eastern. This follows the failed
[budgeted scheduling screen](../budgeted_star/FINDINGS.md). It is **not** a
new ICML theorem, a complete ranking method, or a measured label saving.
It neither reads WMT24 nor reruns WMT25.

## The tempting idea

For a fixed `S x N` matrix `y[v,i] in [0,1]`, two directed reference-star
nulls can have opposing reference coefficients:

```text
H1: T1 = sum_i (y[r,i] - y[b,i]) <= 0
H2: T2 = sum_i (y[c,i] - y[r,i]) <= 0.
```

Their sum is `T1+T2=sum_i(y[c,i]-y[b,i])`: the reference cancels.
Could we buy only the `b` and `c` cells and obtain joint evidence that
certifies which candidate is better than the reference?

### What is valid

At each observed history, set predictable nonnegative weights `w_e` for any
set of directed nulls `T_e<=0`, and let the signed coefficient of cell `d`
in `sum_e w_e T_e` be `h(d)`. Let `A` be the sum of observed contributions.
Randomly purchase one unbought cell `C` using probabilities `p(d)>0`
whenever an unknown `h(d)` is nonzero. Zero-coefficient cells need not be
bought for this particular test. The signal

```text
X = A + h(C) y[C] / p(C)
```

has conditional expectation `sum_e w_e T_e` for every fixed matrix. It has
the predictable lower bound

```text
L = A + min(0, min_{d:p(d)>0} h(d)/p(d)).
```

For `0<rho<1`, `F=1+rho*X/max(1,-L)` is nonnegative (at least `1-rho`)
and has conditional expected value at most one when **all** the selected
nulls hold. Multiplying such factors yields a valid e-process for their
intersection under outcome-adaptive cell selection. The proof uses
conditional importance weighting and nonnegative betting; these are
standard tools. The [existing cell-level audit](../cell_level_gate/THEOREM_NOVELTY_AUDIT.md)
already establishes the single-contrast case. The construction does not
establish originality relative to multivariate e-processes or rank
confidence-sequence closure.

### What it cannot establish

When the two reference coefficients cancel, the joint test observes the
`c-b` difference. If `T1+T2>0`, it may reject `H1 intersect H2`: **at least
one** directed null is false. It cannot say **which** reference edge has
the positive sign. To see the failure without any probability calculation,
fix every score of `b` at `.25` and every score of `c` at `.75` for two
items. In world A, every reference score is `0`; in world B, every reference
score is `1`. Both worlds yield exactly the same purchased leaf scores
and joint total `T1+T2=1`, yet:

| World | `T1 = r-b` | `T2 = c-r` |
| --- | ---: | ---: |
| A, reference scores 0 | -0.5 | +1.5 |
| B, reference scores 1 | +1.5 | -0.5 |

A leaf-only policy has identical observations in these worlds, so it cannot
reliably orient either individual edge uniformly over fixed matrices.
Purchasing some reference cells and combining individual and intersection
tests might still help. This counterexample only rules out identifying
reference comparisons from *complete reference cancellation alone*.

## Exhaustive check

[`probe.py`](probe.py) examines every `2^6=64` binary three-system,
two-item matrix and every `2^6=64` exposure mask: **4,096** matrix/mask
states. The unequal acquisition probabilities depend on already exposed
scores, exclude reference cells because their joint coefficient is zero,
and never use a hidden score. All conditional means equal the fixed joint
target; all factors are at least `.2` with `rho=.8`; and the **1,664**
matrix/mask states satisfying both nulls have conditional expected factor
at most one. A binary pair of worlds shows ambiguous tie/strict directions;
the fractional worlds above show strictly opposite directions. These checks
validate the algebraic implementation, not an end-to-end error rate.

Run from the repository root:

```bash
python -m unittest discover -s experiments/joint_cell_probe -p 'test_*.py' -v
python experiments/joint_cell_probe/probe.py
```

## Research decision

Do **not** count an intersection rejection as a certified individual system
comparison or count unpurchased reference labels as a cost saving for the
original task. The missing step is a joint certificate that *identifies
individual signs* with taskwise family error control and actually reduces
unique purchased judgments over Stage 22 and the evidence-first cell
control. A simple combination of adaptive-cell importance weighting and
rank/order closure is already close to [CELEUS](https://arxiv.org/html/2606.20820v2)
plus [Rank Confidence Sequences](https://arxiv.org/html/2609.32211v1),
and [adaptive multiple testing](https://arxiv.org/html/2609.26651v1)
is additional relevant prior art. It needs a distinct mechanism and a
matched empirical advantage before anyone calls it a paper contribution.
