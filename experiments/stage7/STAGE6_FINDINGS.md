# Stage 6 findings

The direct cost guard is valid and passed every saved-path check. The primary
historically ranked extra-query policy failed its prespecified efficiency
requirement: it increased mean paid queries in all three aligned-history
language cells. This mechanism should not replace Stage 5 as an efficiency
improvement or be described as a successful active-evaluation method.

## Aligned histories: primary result

Mean unique target segment scores revealed by the first nonempty interval of
width at most 0.10. A positive percentage means more paid labels than raw 95%.

| Language | Pool size | Raw 95% | Active 10% | Query change | Random 10% |
| --- | ---: | ---: | ---: | ---: | ---: |
| en-de | 154 | 125.376 | 126.320 | +0.753% | 129.205 |
| he-en | 820 | 416.114 | 443.876 | +6.672% | 443.918 |
| zh-en | 589 | 292.528 | 312.215 | +6.730% | 312.147 |

With equal weight to languages, then target systems within languages, raw
evaluation uses 278.006 queries and active10 uses 294.137: **+5.802%**. The
paired difference is +16.131 labels. Its conditional query-randomization
Monte Carlo standard error is 0.058 labels. This measures simulation error on
fixed recorded pools; it is not uncertainty for new datasets, models or raters.
Random10 costs +6.145% by the same weighting. Active ordering therefore helps
slightly relative to random extra labels, but does not repay its cost relative
to the raw baseline.

Only four of the 39 aligned target rows had lower mean paid cost with active10.
On individual aligned paths it advanced the raw stopping step 20.67% of the
time, but reduced paid cost only 8.87% of the time. Earlier raw-step stopping
and lower total paid cost are different quantities.

## Artificial adverse histories

These preserve target outcomes while permuting background columns or reversing
background binary scores. They are not naturally observed domain shifts.

| Stress | en-de active10 overhead | he-en | zh-en | Equal-language overall |
| --- | ---: | ---: | ---: | ---: |
| Permuted history | +2.972% | +6.672% | +6.708% | +6.129% |
| Reversed history | +3.514% | +6.716% | +6.687% | +6.225% |

No target row had a lower mean paid cost in either stress with the primary
policy. The raw and random-query controls are identical across history
scenarios for a matched target and seed.

The larger 25% allowance does not rescue the method: aligned overall overhead
is +13.265%, versus +15.143% for random25. Its tiny German saving of 0.051%
is a diagnostic cell, not a replacement for the failed 10% primary policy.
All comparisons remain reported rather than selecting a favorable cell.

## What caused the loss

Known-label bounds tightened an endpoint before the primary stop on 71.67% of
German paths, 0.50% of Hebrew paths and 26.27% of Chinese paths. Tightening was
often too small or too late to reduce paid cost.

| Language | Mean raw steps at active10 stop | Extra labels | Free cached raw hits | Total paid |
| --- | ---: | ---: | ---: | ---: |
| en-de | 121.347 | 11.635 | 6.662 | 126.320 |
| he-en | 416.114 | 41.045 | 13.283 | 443.876 |
| zh-en | 292.469 | 28.707 | 8.961 | 312.215 |

The accounting identity is `paid = raw steps + extras - cache hits`. Hebrew's
mean raw stopping step is unchanged; Chinese's advances by just 0.059 steps.
The added labels dominate those gains. German does advance, but its extra
labels still exceed the saved raw cost.

This diagnoses this particular deterministic-bound mechanism. It does not
establish that every active policy or prediction-assisted inference method
fails. The deterministic interval's intrinsic width is 1-q/N; ordering can
move its endpoints, while the unknown-label mass remains large. Stronger
statistical use of active labels would require a separately justified process.

## Guard, coverage and verification

For active10, on every matched raw path,

`paid_stop <= min(N, raw95_stop + floor(raw95_stop / 10))`.

The comparison is against ordinary raw **95%**, unlike Stage 5's stricter
reserved-raw comparison. The output inherits the raw simultaneous coverage
event by intersecting with deterministic information, with empty-intersection
repair and exact all-known completion. It does not require a valid raw
martingale in the enlarged active-label filtration.

The largest observed active10 extra cost was 38 labels; its largest relative
overhead was 9.926%, within the 10% cap. Across the 25% diagnostic methods the
largest observed extra cost was 88 labels. These observed maxima are distinct
from the proved allowances. No primary empty-intersection repair occurred
before the first stop in the reference run.

Primary aggregate simultaneous coverage ranges from 95.833% to 97.083% over
the nine scenario/language cells. Rare raw coverage failures are retained,
and exact full evaluation does not erase earlier failures.

- All 18 tests passed, including exhaustive small-pool coverage over all
  64 binary populations and 720 raw permutations for N=6.
- The faster PPR endpoints matched the original implementation in 46,746
  separate pre-run endpoint comparisons through N=50.
- The independent analysis replayed all 117 query ledgers, using the original
  count-grid raw computation on all 39 distinct target streams.
- It verified all 70,200 saved decisions and all 46,800 active stopping
  inequalities, as well as every saved cache cost and interval endpoint.
- Full reference experiment runtime: 54.8 seconds with two workers.

## Limits and research implication

The 39 WMT23 target rows are new to Stages 1–5, but folds share background
systems and fixed benchmark items. Repeats do not create additional independent
models or datasets. There is no provider/family holdout in Stage 6. Conservative
quality-control exclusions reduce en-de to 154 segments and zh-en to 589;
results do not describe the whole official WMT test set.

All retained scores have one recorded rater. The binary score and fixed-pool
mean do not quantify official severity-weighted MQM, rater reliability, future
sentence quality or actual human annotation time. Historical label cost is
excluded. No private Hayden/Carey material is used.

The simple guard is useful for defining a safe comparison, but neither its
budget argument nor these negative results establish an ICML contribution.
Keep the result as development evidence. A next method must justify how active
labels create enough statistical information to pay for acquisition, or focus
on prediction-assisted uniform evaluation if that is where the evidence points.
