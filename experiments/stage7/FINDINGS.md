# Stage 7 findings: unchanged Stage 5 methods on WMT23

The fixed 75% reserve pipeline saves **7.428%** of mean target queries overall
on aligned WMT23 histories, using equal weight to languages and then systems.
It helps Hebrew-to-English and Chinese-to-English but costs slightly more on
English-to-German. Stage 6's extra-query mechanism remains inefficient overall.
This is a positive but mixed pipeline diagnostic, not a new method or an ICML
novelty result.

## Aligned histories

Mean unique target segment scores at the first nonempty interval of width at
most 0.10. Positive query changes mean more cost than ordinary raw 95% PPR.

| Language | Pool N | Raw 95% | Primary reserve75 | Change vs raw | Standalone count-grid prediction | Stage 6 active10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| en-de | 154 | 125.376 | 126.468 | +0.871% | 135.218 | 126.320 |
| he-en | 820 | 416.114 | 378.159 | -9.121% | 331.048 | 443.876 |
| zh-en | 589 | 292.528 | 267.437 | -8.577% | 235.011 | 312.215 |

The equal-language primary mean falls from **278.006 to 257.355 queries**.
The paired difference is -20.651 labels, with conditional query-randomization
Monte Carlo standard error 0.336 labels. This standard error concerns fixed
recorded pools and fixed algorithms, not generalization to new models,
sentences, releases or raters.

All 27 Hebrew/Chinese target rows have a lower primary mean query cost; none
of the twelve German rows do. The smaller German pool is therefore a real
counterexample to universal empirical improvement. Its conservative quality-
control exclusions and finite-pool size limit broader interpretation.

Standalone prediction has a larger aligned overall saving of **15.916%**;
legacy trust saves **12.849%**. Both have roughly 8-9% overhead in German.
The primary reserve gives up some efficiency on favorable pools to reduce
the losses of the standalone branch on unfavorable ones. The old gate remains
slow: its aligned overall overhead is **13.230%**.

Stage 6 active10 uses 294.137 queries by the same equal-language weighting,
or +5.802% versus raw. Stage 7 primary reserve75 is about 12.5% cheaper than
that active mechanism overall. In German alone active10 is slightly cheaper
than reserve75, so no every-language dominance over Stage 6 is claimed.

## Artificial adverse histories

The target outcomes and raw paths are unchanged. Only the target-excluded
historical bank is permuted or reversed. These are synthetic stresses.

| Stress | German primary change | Hebrew primary change | Chinese primary change | Overall primary change |
| --- | ---: | ---: | ---: | ---: |
| Permuted history | +1.094% | -1.079% | -0.864% | -0.677% |
| Reversed history | +1.084% | -1.023% | -0.675% | -0.584% |

The primary method has lower target-level mean cost in 23 of 39 permuted cases
and 22 of 39 reversed cases. Small overall average improvements do not guarantee
that every target or every random path benefits.

Legacy trust has overall overhead of +0.920% and +1.126% in the two stresses.
Standalone count-grid prediction still saves 2.429% and 2.204% overall. The
old gate has very large overall overhead: +45.702% and +45.910%, including
approximately +66% for Hebrew. These diagnostics remain in the report.

## What this diagnoses, and what it does not

The unchanged prediction-assisted uniform pipeline remains useful on two of
the new release's three pools, even though adding active labels with only
deterministic known-label bounds did not pay for its cost. The existing
prediction/ridge/trust rules were not retuned for WMT23.

This comparison changes both the predictor and the statistical treatment:
Stage 6 ranked a historical mean; Stage 5 uses an online SVD/ridge predictor
and prediction-corrected betting capital. It does not isolate the causal
contribution of either ingredient. The count grid, two-sided capital average
and stake rule also differ from the published PPR baseline.

Shared predictor strength is near its 0.5 cap at primary aligned stops. It
shrinks substantially under permuted histories and is zero or almost zero
under reversed histories, especially for Hebrew. Residual savings in those
stresses can therefore come from a different raw betting process even when
historical predictions contribute little. A matched zero-trust count-grid
baseline is the next important ablation; it is not present in this stage.
Do not attribute all observed savings to historical information alone.

Every Stage 7 query is still uniform. Historical data change the confidence
process, not acquisition. No improved active-querying claim is justified here.

## Guarantee and worst-path cost

The primary mixture has nominal 95% anytime coverage and retains fixed raw
capital. Its all-path stopping inequality is

`tau_reserve75 <= tau_raw_PPR_at_96.25_percent`.

The stricter control has aligned mean costs 127.088, 432.317 and 303.289 for
German, Hebrew and Chinese. These are not equally 95% controls. The proof is
unchanged and included in `STAGE5_THEORY.md`.

This guarantee is **not** a cost cap against ordinary raw 95%. The largest
observed primary extra cost in Stage 7 is **225 queries**: a permuted-history
Chinese Lan-BridgeMT path used 354 queries versus 129 for raw95. Both methods
covered the true mean throughout that path. Thus large overhead is not limited
to raw coverage-failure paths. A small log-evidence reserve penalty can still
translate into a large stopping-time difference.

Stage 6's direct 10% paid-query cap does not carry over to this pipeline.
Combining its operational cap with Stage 7's favorable inference efficiency
remains an unresolved research question.

## Coverage, audit and implementation corrections

Primary aggregate full-path coverage ranges from **96.167% to 97.667%** over
the nine scenario/language cells. Earlier failures remain counted even when
the final exact mean is returned. No primary empty-mixture repair occurred
before first precision stopping; those repairs cannot explain the cost gains.

The release has **28 passing tests**, comprising unchanged prior statistical
tests and new compatibility/audit checks. All 117,000 saved precision decisions
were audited from full saved curves. Every stop is nonempty, has width at most
0.10, and has midpoint error at most 0.05 on its full-coverage event.

The independent analysis also:

- Replayed original-grid raw PPR at all four confidence levels on 39 distinct
  target streams; verified identical nonempty confidence sets.
- Checked 35,100 reserved stopping inequalities and full-path mixture/raw
  containment in all 117 case bundles (ten method curves per bundle).
- Matched all 11,700 Stage 6 paired raw stops and query-stream hashes exactly.
- Verified every saved target/scenario aggregate against the path records.

The first audit compared arbitrary numeric endpoints even when both intervals
were empty. It was corrected to compare empty confidence sets semantically
while requiring exact equality of every nonempty endpoint. A regression test
enumerates interval-set equality on a finite grid. There are 110,829 differing
empty representations across coupled case/time/confidence positions; this is
not a count of independent failing paths. All underlying coverage failures
are retained. Original analyzer, failure output and revision hashes are saved.

Visual QA also shortened repeated plot labels to avoid inter-panel overlap.
Both revisions affect audit/presentation only; statistical modules, rules,
data, weights, queries, intervals and performance results are unchanged.

Reference experiment runtime was **288.3 seconds**, with two workers and one
BLAS thread per process. The independent audit adds time.

## Evidence limits

WMT23 was already inspected in Stage 6. This is a follow-up diagnostic, not
untouched validation. Folds share historical systems and items; repetitions
measure sampling randomness and do not create additional models. There is no
provider/family holdout in this comparison.

The score is a derived binary recorded-annotation outcome on fixed common
pools, not official severity-weighted MQM or latent true quality. All retained
system/item ratings have one rater. Historical annotation cost, human labeling
time, uncertainty from raters and future populations are outside scope.
No private Hayden/Carey data or unpublished results are used.

The evidence supports further work on prediction-assisted inference and gives
a concrete counterexample to ordinary-95% query-cost protection. It does not
establish a novel ICML contribution. First isolate the contribution of
historical prediction against a matched model-free betting control, then
investigate a statistically valid operational cost safeguard with appropriate
published-method comparisons and separately held-out data.
