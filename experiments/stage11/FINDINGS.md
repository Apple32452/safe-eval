# Stage 11: a small residual gain after the published boosting baseline

The independent audit passed. The aligned-history prediction advantage is now
**0.341%, or 0.925 labels**, against boosted PPR, compared with 0.666% against
Stage 10's finer calibrated control. Prediction improves 15 target means and
worsens 24. Its largest observed extra cost against boosting is 260 labels.
This is a small, heterogeneous development effect, not an established ICML
contribution or broad annotation-efficiency result.

## Fixed study and baseline

Protocol, source fingerprints and implementation were frozen at
7415fecdd7a38074b1901ad63baca10f17e15cee before the new comparison. Parent main
faa189d8888a7ad46afd8a007ab3cbc525a47026 contains audited Stage 10. All Stage
7–10 files remain unchanged. No source predictor, trust, stake, allocation,
seed, precision or query path was changed.

The new baseline applies Fischer and Ramdas's published Algorithm 1 to the
same PPR process; see THEORY.md for the citation and binary specialization.
It does not reproduce their particular RiLACS experiment or introduce a new
method. Both new controls use downward-rounded integer wealth on Q=2^39.
Every candidate total K is considered. The returned interval is the hull;
empty-set expansions preserve validity. Boosting has a pathwise stopping bound
against the matching grid implementation. This bound is not a new novelty
claim and does not order boosting against fine calibration or prediction.

The study compares eight methods on 117 cases and 100 repeats, totaling
93,600 trajectories. It reuses 70,200 independently audited source trajectories
and adds 23,400 control trajectories. Because histories share outcomes and
ledgers, there are 39 distinct model-free ledgers. Reuse of that computation
is checked through full input hashes and all saved case arrays.

## Label cost

Means weight languages equally, then systems equally within each language.
Only target label queries count; historical annotation, computation, human
time and deployment costs are excluded.

| Aligned method | Mean labels |
| --- | ---: |
| Ordinary raw95 / matching grid PPR | 278.006 |
| Stage 9 integer calibration | 273.337 |
| Stage 10 fine / selected repaired calibration | 272.031 |
| Published boosting applied to PPR | 271.143 |
| Unchanged prediction pipeline | 270.218 |

The aligned paired difference, prediction minus boosted PPR, is -0.925 labels
with conditional query-randomization MCSE 0.366. This is uncertainty on the
fixed outcomes and historical matrices, not a new-data confidence interval.
The new control removes about 49% of the remaining absolute mean-label
advantage reported against the Stage 10 control. Its mean reduction from
ordinary raw is 88.1% of the prediction pipeline's mean reduction from that
same raw baseline; this is an arithmetic comparison, not causal attribution.

| Aligned language | Prediction minus boosting: labels | Relative change | Conditional MCSE | Target wins / losses |
| --- | ---: | ---: | ---: | ---: |
| en-de | +2.049 | +1.662% | .122 | 0 / 12 |
| he-en | -3.762 | -0.925% | .789 | 9 / 3 |
| zh-en | -1.063 | -0.375% | .597 | 6 / 9 |
| Equal-language mean | -0.925 | -0.341% | .366 | 15 / 24 |

There are no target mean ties. Under permuted and reversed histories,
prediction costs 277.991 and 277.999 labels respectively, versus the same
boosted control mean 271.143. These are increases of 2.525% and 2.529%; all
39 target means lose in each adverse condition. All targets and unfavorable
paths are retained in the tables. The worst individual extra cost is 260
labels, larger than the 188-label worst extra cost against the fine control.

Boosting itself saves 2.469% against raw/grid PPR and improves all 39 target
means. Its largest extra cost against the matched grid control is zero.
Against fine calibration it saves 0.326% on average, but has 23 target mean
wins, 16 losses and a worst extra cost of 106 labels. It is not uniformly
better than that separately calibrated process or globally optimal inference.

## Numerical behavior, coverage and verification

The matching grid control reproduces every saved floating raw95 interval
endpoint exactly on these traces: zero differing entries, paths or stops.
This empirical identity lets us compare the observed gain without attributing
it to quantization. It is not a theorem of numerical identity on all inputs.

Boosted candidate sets have holes on five distinct repeat paths, totaling ten
timepoints, with at most four missing candidate counts inside their hull.
The same paths recur under all three history conditions. The grid sets have
no holes. The implementation explicitly checks all candidates and saves every
first rejection; it does not assume that the acceptance set is an interval.

Equal-language simultaneous coverage is 95.217% for boosting, 96.483% for
grid/raw and unchanged prediction, and 95.639% for fine calibration. Stopped
midpoint error exceeds .05 on 4.344% of boosted paths versus 3.261% for
prediction. Both new controls' output empty-ever rate is 3.150%, and no
fallback occurs before a reported precision stop. These empirical rates are
not validity proofs. Common nominal 95% validity does not mean equal actual
error rates, and this comparison does not isolate history's causal effect.
Per-target simultaneous validity is distinct from familywise coverage across
all cases. Full evaluation does not erase earlier failures.

The audit checked all 93,600 saved decisions, reconstructed the 70,200 source
decisions, preserved all 3,510 source metric values and checked 4,680 total
target metric values. It verified 11,700 matched stopping bounds and 12,313,800
new-control query steps across the saved cases. Independent replay uses 39
distinct ledgers: 4,104,600 method-query steps and 377,007,310 live candidate
wealth updates. Every first rejection time, interval, fallback and hole count
matches the independently coded observed-branch implementation.

The canonical source manifest matches. Original prediction-capital and
calibration audits are explicitly reused, not repeated. The comparison took
34.5 seconds and its new audit 20.3 seconds. Six new tests pass, including
rational conditional expectations, exhaustive small binary paths, signed-int64
bounds at actual pool sizes, independent replay and matched containment.
A separate post-freeze reporting script independently reconstructed all 120
contrasts from the 93,600 per-trial rows before drawing the figure. It changes
no inference rule or metric. See both verification JSON files.
The frozen implementation also passes all 55 repository tests and the existing
GitHub end-to-end checks on Ubuntu Python 3.9/3.12 and macOS Python 3.12.

## Research decision

A small aligned average benefit survives this baseline, while most target
means and both adverse histories favor the published model-free method.
Existing calibration and boosting substantially narrow the original headline
gain. The present evidence does not support a broadly superior method or
establish novelty. Larger repaired calibration remains unfinished, and these
controls are not claimed to exhaust all possible strong baselines.

Discuss the full result and a distinct research question with Professor
Philipp Koehn before scaling experiments or presenting an ICML proposal as
validated. A new method or a sharper scientific hypothesis needs its own
argument and fixed evaluation design. Do not keep modifying these development
pools until a favorable result appears. WMT23 remains development data; no
inspected WMT24 pool is relabeled untouched. The recorded binary error-free
outcome also remains distinct from official weighted MQM, latent quality,
new-rater uncertainty and future-population performance.
