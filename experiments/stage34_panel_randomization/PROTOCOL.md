# Stage 34: design-based audit of the five-way judgment pilot

Frozen 2026-10-24, before any prospective pilot judgments. This improves
the Stage 33 analysis plan; it is not a new statistical theorem or an ICML
novelty claim. No WMT24 evaluation is included.

## Target and design

Use Stage 33's 40 fixed WMT25-development documents and blinded A/B outputs.
For each document, choose four distinct bilingual judges independently of its
potential judgments. Randomly allocate exactly two judges to panel P0 and
two to panel P1; display A/B in randomized positions, and independently
randomize the other three positions. Record the actual assignment, A/B
positions and ranking. The same judge may see different documents but never
the same document twice. Randomize each judge's task order and record that
order for a future confirmatory collection. No new judgments exist yet.

The response `Y` is +1 if A is preferred to B, -1 if B is preferred to A,
and 0 for a tie. The statistic is the mean across documents of `mean(Y|P1)
- mean(Y|P0)`. The sharp randomization null says that for each of the four
selected judge/document pairs, changing companion triplet P0 versus P1 while
holding A/B positions fixed does not change Y. Condition on judges, documents
and A/B positions; within each document the 2-of-4 assignment has six
equally likely possibilities, independent across documents. The exact null
distribution is a convolution of those six treatment allocations per
document. The two-sided randomization p-value counts allocations whose
absolute statistic is at least as extreme as observed; include equality.

This is exact for the sharp null under the specified randomization even when
the same judge rates several *different* documents. It does not by itself
yield a confidence interval for an average panel effect, nor does it protect
against interference, carryover between tasks, violations of assignment,
or selection of the treatment comparison after seeing responses. The
contrast is Stage 33's *preselected* high/low companion comparison.

## Prospective power planning

**Correction made before collecting human data:** the first protocol commit
used variance bound 1 from independent groups. This design assigns two of
four *fixed* selected judges to each panel without replacement; its correct
worst-case within-document randomization variance bound is `4/3`. Under the
sharp null it is exactly the four-judge finite-population sample variance,
which is at most `4/3` for outcomes in `[-1,1]`; the same upper bound applies
to the difference-in-means under fixed potential outcomes. Independently
randomized documents, no between-document interference, and a normal
approximation at two-sided `alpha=.05`, power `.8`, mean effect delta give
`n ≈ (4/3)*(z_.975+z_.8)^2/delta^2` documents, each with four judgments.
Report delta `.2`, `.4` and `.6`, and Stage 33's 40-document pilot. These
numbers are planning approximations, **not measured power**, and repeated
judge carryover, ties, missed tasks, or heterogeneous treatment effects can
change them. They cannot establish a panel context effect. The recorded
[amendment](AMENDMENT.md) preserves the original mistake and correction.

## Falsification and decision

Enumerate toy allocations and verify the exact tail probability and null
type-I bound for small fixed outcome arrays, ties, task completeness,
two-per-panel balance, distinct judges per document, and position handling.
Run the planning calculation and retain the findings. The scientific next
step needs genuinely randomized human judgments; absent those, report no
context-effect or ICML claim. If a large pilot effect appears, replicate on
independent documents, raters and languages and compare protected conclusions
per measured annotation minute with published active ranking methods.
