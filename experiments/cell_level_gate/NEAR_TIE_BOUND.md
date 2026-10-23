# A near-tie acquisition limit and research decision

Research note, 2026-10-22 (US Eastern time). This is a self-contained
indistinguishability argument, **not an ICML novelty claim**. It is an
instance of the standard randomized decision-tree lower-bound idea: if two
fixed inputs differ in one unread entry, an adaptive query algorithm cannot
tell them apart before buying that entry.

## Model and claim

Fix a requested graph `G=(V,E)` with at least one edge, `N` items,
and binary system--item scores. Let `V*` be the vertices incident to
requested edges. Each bought score reveals exactly one previously unknown
cell; public item information and external predictions are held fixed across
the score matrices in this argument. The algorithm may choose the next cell
and when to stop using past bought scores and private randomness.

Let `y0` be the all-zero matrix. For each cell `c=(v,i)` with `v in V*`,
let `yc` differ from `y0` only by setting that cell to 1. Choose any edge
incident to `v`; its fixed-pool mean difference is zero on `y0` and
strictly nonzero on `yc`.

Assume (a) on *every* fixed score matrix, the chance of ever reporting any
wrong **strict directional claim** is at most `alpha`; and (b) on each
`yc`, the algorithm reports the correct strict direction on a chosen
incident edge with probability at least `1-beta` before its budget or
stopping time. Then

```text
P_y0(purchase c) >= 1 - alpha - beta   for every c in V* x [N],
E_y0[unique purchased cells] >= (1 - alpha - beta) |V*| N.
```

If instead the algorithm must output the **complete correct sign vector
including ties** with probability at least `1-alpha` on every matrix, the
same argument gives `(1-2*alpha)|V*|N` as a lower bound on its expected
purchase cost on `y0`.

### Proof

Run the algorithm on `y0` and `yc` with the *same* private randomness.
Its visible histories and future choices are identical until it purchases
`c`. In the first claim, let `A_c` be the event that the algorithm reports
the strict direction caused by `c` on the chosen incident edge. On `yc`,
`P(A_c)>=1-beta` by power; on `y0`, `P(A_c)<=alpha` by familywise
false-direction control. The probability difference between two coupled
events is at most the probability that their histories diverge, namely
`P_y0(purchase c)`. Sum over all `c` and use that the expected number
of unique purchases is the sum of their purchase probabilities.

For complete signs, use the event that the output is the all-tie vector.
It has probability at least `1-alpha` on `y0` and at most `alpha`
on each `yc`. Repeat the same coupling and sum.

## Interpretation and limits

At `alpha=beta=0.05`, uniform 95% power even against *one-cell* score
differences forces **at least 90% of all active-system cells in expectation
on the all-tie matrix**. The stronger complete-sign requirement has the
same 90% bound at `alpha=0.05`. This is a worst-case boundary, not a
prediction of costs on WMT data and not a new lower bound in randomized
query complexity. A good predictor cannot defeat this model-free statement
if the same side information is allowed for the indistinguishable matrices.

The bound does **not** apply to a method allowed to abstain on one-cell
differences with no required power: condition (b) is then false. It also
does not bound savings on well-separated system pairs, average-case data,
or another target that allows a practical indifference zone. Scores that
change with rater assignment need their own explicit sampling model.

## Decision for SAFE-EVAL

Do not require a new cell method to complete *every* close comparison
cheaply. Preserve the fixed-pool familywise wrong-direction guarantee and
measure a **budgeted selective objective**: for a predeclared graph and
unique-judgment budget, how many correct pairwise directions can be
certified, with the rest explicitly unresolved? This answers the practical
question even when ties and tiny gaps cannot be settled economically.

Stage 22 already has a strong budgeted reference-star control: at its
50%-of-full-score budget, its WMT25 development replay averaged
**9.214 certified edges**, **8.000 unresolved**, and **1,738.21 labels
actually purchased** across the same reference tasks; see
[Stage 22 findings](../stage22/FINDINGS.md). Any new adaptive-cell method
must beat this and a strong cell-aware control at *matched actual unique
cost*, requested edges, family error, and target matrix. Record abstentions
and language-level variation. Do not compare a cheaper but unresolved run
with another method's completed conclusions.

The statistical ingredients for adaptive finite-pool inference and
shared-item ranks already exist in
[CELEUS](https://arxiv.org/html/2606.20820v2) and
[Rank Confidence Sequences](https://arxiv.org/abs/2609.32211);
partial rankings under adaptive evaluation also appear in
[AnyRank](https://arxiv.org/abs/2610.14603). The proof above motivates a
more useful objective; it is **not** sufficient novelty. A paper would
still need a method or graph-dependent performance result beyond a direct
composition of these tools, plus a matched empirical gain.
