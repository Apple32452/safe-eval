# Stage 8 findings: historical predictions versus matched zero-trust controls

Historical predictions supply most of the aligned-history query savings in the
existing reserve pipeline. Its mean cost falls from **276.176 to 257.355 labels**
relative to the matched zero-trust reserve: **6.815% fewer labels**, using equal
weight to languages and then systems. All 39 aligned target-level means improve
against that matched control. This strengthens the mechanism interpretation of
Stage 7 without establishing a new ICML method.

## Primary aligned comparison

| Language | Raw PPR 95% | Zero-trust reserve75 | Prediction reserve75 | Prediction change vs zero |
| --- | ---: | ---: | ---: | ---: |
| English to German | 125.376 | 126.720 | 126.468 | -0.199% |
| Hebrew to English | 416.114 | 411.418 | 378.159 | -8.084% |
| Chinese to English | 292.528 | 290.391 | 267.437 | -7.904% |
| Equal-language overall | 278.006 | 276.176 | 257.355 | -6.815% |

German predictions help slightly relative to the matched reserve control, but
both reserves still cost more than ordinary raw95. The comparator matters:
there is no improvement in every language against raw95.

The primary paired difference is **-18.821 labels**, with conditional query-
randomization Monte Carlo standard error **0.229 labels**. The standard error
describes the fixed recorded pools and query randomization, not new models,
sentences or raters.

The original 7.428% total saving against raw95 decomposes into **0.658 percentage
points from the model-free reserve pipeline** and **6.770 percentage points from
enabling predictions**. Both components use the same raw95 denominator. The
6.815% figure above instead uses the matched zero-trust denominator.

## Secondary standalone comparison

The matched model-free standalone mean is **271.237 labels**; the unchanged
prediction standalone mean is **233.759**. Enabling history reduces cost by
**13.817%**, or 37.478 labels (conditional Monte Carlo standard error 0.294).
All 39 aligned target-level means improve against the matched standalone.

Its total saving against raw95 is 15.916%, decomposed into 2.435 percentage
points from the model-free betting procedure and 13.481 from enabling history.
This faster standalone branch does not inherit the reserve's stricter-raw
stopping guarantee. It still costs more than raw95 in German.

## Adverse-history mechanisms

Target outcomes and query paths are unchanged. Permuting or reversing historical
outcomes is an artificial stress rather than observed natural domain shift.

| History | Reserve change vs matched zero | Standalone change vs matched zero |
| --- | ---: | ---: |
| Aligned | -6.815% | -13.817% |
| Permuted | -0.019% | +0.006% |
| Reversed | +0.075% | +0.236% |

Permuted primary history changes the mean by -0.052 labels, with Monte Carlo
standard error 0.064; this experiment does not resolve a useful improvement.
Reversed primary history adds 0.207 labels (standard error 0.054). The reversed
standalone adds 0.640 labels (standard error 0.088).

The model-free controls are exactly invariant across the three historical
conditions. Their gains against raw95 explain nearly all the residual savings
observed in Stage 7's stresses. Those residual gains cannot be attributed to
useful historical predictions.

## Average gains do not bound path cost

The prediction reserve can cost **70 more labels than its matched zero-trust
reserve even with aligned history**: Chinese GPT4-5shot, repeat 47, stopped at
228 versus 158. Both covered the true mean throughout the path.

The largest extra cost against ordinary raw95 remains **225 labels**. On the
permuted Chinese Lan-BridgeMT repeat 71, raw95 stopped at 129; both the
prediction and zero-trust reserves stopped at 354. The stricter raw96.25 stopped
at 360. All three quoted raw/reserve paths covered throughout. The large delay
is therefore also present without historical prediction.

Both reserves retain the all-path guarantee against raw **96.25%**, not ordinary
raw95 and not their matched zero-trust counterpart. No new cost safeguard was
implemented. The main unresolved operational problem is to obtain useful
prediction gains with a guarantee against an explicitly named ordinary baseline.

## Coverage and verification

Primary prediction reserve aggregate full-path coverage ranges from 96.167% to
97.667%; the zero-trust reserve ranges from 96.333% to 97.583%. These are
empirical proportions from fixed coupled benchmark pools, not proofs. Neither
reserve had a repair before its first precision stop in this run. Earlier
coverage failures remain counted despite exact full evaluation.

The frozen run completed 117 cases and 70,200 method trajectories in **230.6
seconds**, using two workers and one BLAS thread per process. The independent
audit passed:

- 70,200 saved decisions reconstructed from all full confidence curves.
- 23,400 reserved stopping inequalities and full-path containment checks.
- 39 distinct model-free target streams replayed independently, including the
  original-grid raw PPR inversion and zero-trust capital.
- 11,700 exact paired Stage 6 raw stops and stream hashes.
- 2,340 recorded Stage 7 metric values across four preserved methods.
- All saved target and scenario aggregates.

There are **35 passing tests**: 28 preserved tests and seven new invariants.
Before the full comparison, GitHub recorded the frozen implementation/protocol
commit. All 49 Stage 7 release files remain byte identical. The new controls
also pass exact enumeration on every binary population and uniform permutation
for N=6 at error levels .05 and .20.

## Evidence limits and next work

This is a controlled mechanism diagnostic on WMT23 already inspected in Stages
6 and 7. It fixes rules, grids, confidence levels and query paths; enabling
predictions changes corrected draws and the realized variance-dependent stakes.
The target is the derived fixed-pool binary recorded-annotation mean, not
official severity-weighted MQM or latent quality. Historical-label acquisition
cost, human time, rater uncertainty and future-population performance are not
measured. Repeats do not create independent new systems.

The findings justify keeping historical prediction as a useful ingredient.
Further work should investigate an ordinary-95% cost safeguard, compare against
the matched model-free process, and use a separately selected public release for
confirmation after freezing any new method. Existing betting, prediction-powered
inference and fixed mixtures do not become novel merely through this ablation.
