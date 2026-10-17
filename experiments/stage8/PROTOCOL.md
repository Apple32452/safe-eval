# Stage 8: matched zero-trust mechanism ablation

This diagnostic isolates the effect of enabling historical predictions in the
existing count-grid and reserve pipelines. It is not a newly proposed method.
The primary comparison is the prediction-assisted 75% reserve versus the same
75% reserve using model-free count-grid betting capital.

## Fixed design

Use all 117 Stage 7 leave-one-target-out cases: 39 targets on the same three
WMT23 pools and aligned, permuted and reversed histories. Target outcomes never
enter historical features or bank transformations. Run 100 query randomizations
with the unchanged target-keyed seeds. This is already inspected development
data; repeats measure query randomness rather than new models or raters.

All six methods share one uniform-without-replacement query ledger per case.
Prediction methods preserve the Stage 7 ridge model, trust update, count grid,
variance prior, stake cap .9 and targeted stake rule. Controls set trust to zero
and cancel a constant prediction analytically, yielding the raw finite-pool draw
`Z = S/N + remaining*Y/N`. Controls use the same stake rule with their own past-Z
variance. Realized stakes change when Z changes; the ablation holds rules fixed,
not the realized numerical stakes.

| Method | Role | Nominal anytime confidence |
| --- | --- | ---: |
| published_ppr95 | Existing published raw baseline | 95% |
| raw_count_grid | Matched model-free standalone control | 95% |
| prediction_count_grid | Unchanged prediction standalone | 95% |
| raw_reserve75 | Matched model-free 75% reserve control | 95% |
| reserve_mix75 | Unchanged prediction 75% reserve; primary | 95% |
| ppr_reserve75 | Stricter raw control for both reserve guarantees | 96.25% |

The two reserve constructions retain the existing empty-set repair and the
all-path stop bound against raw 96.25%. No cost cap against ordinary raw95 or
against the matched zero-trust control is claimed. The default precision stop
requires a nonempty interval of width at most .10. Full evaluation is exact;
earlier failures still count in simultaneous coverage.

## Prespecified reporting

Report mean labels at first precision stopping, full-path simultaneous coverage,
empty-set and pre-stop repair rates, stopped error rates and worst-path overhead.
The primary contrast is `reserve_mix75 - raw_reserve75` in aligned histories,
with equal weights to languages and then target systems. Report every language
and both adverse-history stresses. Do not retune weights, predictions, seeds,
precision or filtering, or remove German to obtain improvement.

Report the analogous standalone contrast as secondary. Decompose the total
query change versus raw95 into (zero-trust control minus raw95) and (prediction
minus zero-trust control), in absolute labels and percentages of the same raw95
denominator. This is an arithmetic decomposition on matched fixed paths, not a
generalization claim. Conditional Monte Carlo standard errors use repeat-level
paired differences after the stated language/system weighting.

## Verification and freezing

Before the full run, freeze protocol and implementation hashes. Preserve all
49 Stage 7 release files byte for byte. Test prediction-branch compatibility,
history independence of controls, predictability, exact small-pool coverage,
lossless curves, unique queries and reserve containment.

The analyzer audits every saved curve and decision, independently reconstructs
the model-free capital and original-grid raw PPR, checks control invariance
across histories, and checks all matched Stage 6 raw paths. At 100 repeats it
also checks all five recorded metrics for four preserved methods against the
Stage 7 reference. One-repeat runs are software checks and omit that pairing.

Evidence is restricted to fixed recorded binary error-free outcomes. This is
not official severity-weighted MQM, latent human quality or future-population
performance. No private Hayden/Carey data are used. A favorable ablation would
still require a distinct contribution, literature audit and separate public
confirmation before an ICML claim.
