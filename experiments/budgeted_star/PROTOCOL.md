# Budgeted reference-star scheduling: prospective development screen

Status: protocol frozen before running this screen. This is a method diagnostic,
not an ICML novelty claim. WMT24 remains reserved.

## Question and target

For a fixed `S x N` bounded-score matrix and a reference star with `S-1`
requested edges, buy at most `B=floor(S*N/2)` **distinct** system--item
judgments. At the budget, count the edges on which a justified **strict**
direction was reported; report wrong directions, exact ties, and unresolved
edges separately. Every policy uses a single precommitted, uniformly random
item permutation, identical across edges, and the unchanged Stage 17
two-sided finite-pool pair certificate with threshold `40*(S-1)` and exact
full-pool fallback. No policy may read a future score to choose a purchase.

The taskwise guarantee is `P(any wrong strict declaration ever | fixed y)
<= 0.05`, including optional stopping and adaptive scheduling. This follows
by event inclusion in the original per-edge random-permutation confidence
sequence, not by asserting that the pair process is a martingale in the
expanded score-exposure filtration. A bought judgment is cached and charged
once. No predictive model or training cost is assumed.

## Methods fixed in advance

1. `pruned`: the frozen Stage 22 active-vertex common-item policy.
2. `evidence_first`: the existing Stage 14 pair-prefix scheduler, which
   prioritizes the greatest **observed** e-evidence and reuses cached cells.
3. `footprint`: buy the first eight complete common-item rows as a paid pilot.
   For each still-unresolved edge, extrapolate its as-yet-unseen pair
   differences as the mean of its *observed paired prefix*, then run the
   original pair certificate on that hypothetical continuation to estimate
   a stopping prefix `n_hat` (or `N` if it has no early certificate). At each
   subsequent scheduling step, choose the unresolved edge with the smallest
   number of not-yet-bought endpoint cells in its first `n_hat` positions;
   break ties by the common-item priority of its next missing score, then by
   edge index. Advance that edge by its next paired item, buying either or
   both missing cells. After each pair advancement, recompute forecasts from
   actual observed paired prefixes, consume all freely available prefixes,
   and retire newly certified edges. Hypothetical values affect **only**
   scheduling; declarations use actual acquired scores and the frozen
   certificate.

For reproducibility, pilot rows are bought in the precommitted within-item
system order; a method that has resolved all edges stops and may spend less
than `B`. Method `footprint` has no parameter tuned after this file is
committed. All three policies share the same matrix, pair set, item order,
within-item label priority, threshold and budget; the e-evidence policy can
interleave prefixes.

## Independent falsification and screen

Use `S=8`, `N=96`, 40 fixed seeded matrices and independent common paths per
scenario, with reference index zero. The four scenarios are (i) independent
Bernoulli scores with rates `[.55,.95,.90,.80,.70,.30,.20,.10]`; (ii) shared
uniform item factors with those same marginal rates; (iii) independent scores
with rates `[.55,.90,.80,.60,.55,.50,.30,.10]`; (iv) near ties with rates
`[.50,.51,.49,.53,.47,.55,.45,.50]`. Scores are generated before drawing
the item path. No side information sees the generated scores. Seed namespace
starts at `20261023`. The primary metric is the mean strict correct edges at
`B`, paired by matrix/path, first across repeats and then equally across the
four scenarios. Report all scenarios, mean actual costs, full completed
costs, and any wrong directions. The prospective gate requires `footprint`
to improve mean strict certificates at `B` by at least 10% relative to **both**
controls in three of the four scenarios, while using no more actual labels,
making no additional wrong declarations, and passing the audits below. This
10% is an internal screen, not an ICML publication standard.

Check that all three policies have the same final exact signs if allowed to
run to completion, unique-label accounting, prefix validity and no future
score dependence. Enumerate small binary matrices and future perturbations
for the scheduler; separately verify the offline star footprint
`max_{e in F} n_e + sum_{e in F} n_e` and the optimal hindsight set of a
given cardinality. The hindsight set is an **upper bound**, never an online
method. At the budget, compare actual unique-label counts as well as strict
certifications; unresolved runs are not counted as inexpensive successes.

If the synthetic gate fails, do not run another WMT25 variant of this
scheduler. If it passes, freeze a single WMT25 development comparison against
Stage 22 and the evidence-first control, with the same 14 languages, 255
references and taskwise family risk; assess language-level effects and
actual cost, then audit closest literature before claiming a new mechanism.
The offline footprint formula and scheduling heuristic are not, by
themselves, presumed novel.
