# Stage 26 findings: a useful rater audit, but no new method yet

Date: 2026-10-22. All numbers below were calculated with the scripts in this
directory. The raw files passed byte-count and SHA256 checks against the
pinned [WMT25 source](https://github.com/wmt-conference/wmt25-general-mt/tree/2fc0874d85278d8c7e0807951e54d8422e7957e4/data).

## Annotator structure on Stage 17's aligned WMT25 cells

| Measure | Observed |
| --- | ---: |
| Languages / system–item cells / recorded ratings | 14 / 51,794 / 103,588 |
| Cells with two recorded ratings | 51,794 (100%) |
| Cells with two distinct annotator IDs | 37,448 (72.30%) |
| Cells whose two ratings have the same annotator ID | 14,346 (27.70%) |
| Cells whose two recorded scores differ | 43,547 (84.08%) |
| Mean within-cell absolute score difference on the 0–100 scale | 16.58 |
| Language-specific annotator IDs in the included evaluation cells | 158 |
| Requested pair–item instances with at least one shared annotator ID between systems | 298,289 / 446,883 (66.75%) |

Every included annotator ID appears on multiple system–item cells and on
multiple items. The first and second *recorded* rating slots yield opposite
full-item-pool score signs for **363 of 2,197 system pairs** (16.52%). This is
an exploratory sensitivity analysis of the recording slots, **not** a
significance test or two independent replications. The full two-rating mean
has no exact ties among those 2,197 pairs, but a nonzero sign alone does not
establish a statistically supported ordering for new items or annotators.

The separate control file contains 444 shared-control cells and 4,612
ratings in these 14 languages. It includes 143 of the 158 annotator IDs in
the main aligned cells; 15 main IDs do not occur in these controls. The
control records store their score under `human`, whereas the evaluation file
uses `score`. The common controls offer a route to studying annotator
calibration, although they do not by themselves make annotators a random
sample of future annotators. The original WMT25 README describes these as
segments shared among annotators.

## Synthetic method gate

Each row averages 100 preseeded uniform item orders of one fixed matrix in
that scenario. Costs are distinct system–item labels needed for all requested
conclusions. The middle method dynamically skips inactive systems inside an
item; the last method also adds deterministic bounds from partial labels.

| Scenario | Graph | Stage 22 labels | Dynamic only | Partial-bound labels | Saving |
| --- | --- | ---: | ---: | ---: | ---: |
| Identical systems | Star / ring / complete | 120 / 120 / 120 | 120 / 120 / 120 | 120 / 120 / 120 | 0% / 0% / 0% |
| Close generating probabilities | Star / ring / complete | 113.00 / 118.91 / 119.31 | same | 112.09 / 118.30 / 118.71 | 0.81% / 0.51% / 0.50% |
| Separated generating probabilities | Star / ring / complete | 77.10 / 114.88 / 115.36 | same | 76.67 / 114.08 / 114.60 | 0.56% / 0.70% / 0.66% |
| Anti-correlated rows | Star / ring / complete | 116.70 / 118.08 / 120.00 | same | 115.64 / 117.08 / 120.00 | 0.91% / 0.85% / 0% |

The close-probability generator happened to produce one exact tie and some
larger realized differences in its 24-item matrix; the label describes the
*generating probabilities*, not a guarantee that every realized pair is
near-tied. Baseline and partial-bound methods each made one family-level
wrong decision among the 100 weak/ring permutations and none in the other
11 groups. A 5% familywise guarantee does not promise zero errors in a
particular Monte Carlo sample, and these observations do not estimate its
worst-case error probability. No tuning or selection after viewing these
results is used to claim an improvement.

## Research decision

The deterministic partial-label step is valid and slightly cheaper in these
examples. Its largest measured saving here is **0.91%**. It is elementary
and does not beat the strongest known rank and adaptive-cell methods in a
matched comparison; it is **not an ICML contribution**. The earlier
[rank confidence sequences](https://arxiv.org/abs/2609.32211) already cover
shared item orders, multiple system conclusions, logical rank relations and
past-dependent retirement. [CELEUS](https://arxiv.org/abs/2606.20820)
already addresses surrogate-assisted adaptive finite-pool acquisition for
one target. A newer [clustered anytime-valid inference study](https://arxiv.org/abs/2610.25613)
and [target-aware sequential designs](https://arxiv.org/abs/2609.37873)
also narrow broad claims about clustered observations or adaptive allocation.

The next theorem must identify a distinct graph-wide advantage from buying
individual system–item or system–item–annotator labels, with valid conclusions
under an explicit target population and randomization. It must be compared
against those rank, adaptive-inference, and rater-aware baselines at equal
error target and annotation cost. For *new items and new annotators*, WMT25
alone cannot supply a design-based guarantee: its existing annotators and
item bank are fixed, and the assignment mechanism is not a prospective
random sample from the proposed future populations. A prospective design or
explicit, testable sampling assumptions are required. WMT24 remains untouched
until a new method passes the synthetic proof and baseline gate.
