# Stage 29 findings: an optimistic shared-reference feasibility signal

On the 14 aligned WMT25 development matrices, the cross-fitted linear
diagnostic contains **4,394 ordered reference/candidate pairs** (both
directions for each of the 2,197 unordered pairs). With candidate query
probability `q=0.75`:

| Local variance-times-cost calculation | Eligible pairs | Median cost ratio to full paired |
| --- | ---: | ---: |
| One pair pays for the full reference | 800 / 4,394 (18.21%) | 1.0531 |
| Reference shared across all 17--19 active candidates | 4,197 / 4,394 (95.52%) | 0.9191 |

The median `R/V` is `0.6105`. All 14 language directions have a lower
median shared-reference cost proxy than the corresponding full paired
proxy; the per-language detail is in
[`results_reference/by_language.csv`](results_reference/by_language.csv).
When one reference label is amortized over a hypothetical `k` simultaneously
active candidates, the eligible counts among 4,394 ordered pairs are:

| Active candidates `k` | 1 | 2 | 4 | 8 | 17 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Eligible pairs | 800 | 2,112 | 3,397 | 3,995 | 4,193 |

The `k=17` column uses the same hypothetical degree for every language;
the 4,197 total above instead uses each language's actual initial degree
(17--19). This sensitivity matters because the active degree falls as
claims finish.
The test script independently enumerates a small randomized query design
and confirms the exact variance identity. Stage 17's data loader verifies
the source and matrix hashes before analysis.

These numbers are **not label savings**. They assume that all candidates
remain active, amortize the reference score uniformly, and charge zero for
training each predictor on most target items. They measure variance per
expected label, not the number of judgments until simultaneous anytime
certificates are obtained. Sequential procedures can pay more because
propensity correction enlarges each signal's range, a hard edge can outlive
the other edges, or learning predictions consumes many labels. The WMT25
recorded-rater mean does not establish conclusions for new annotators.

**Research decision:** a large reference star creates a mathematically
testable opportunity that the three-system Stage 28 experiment could not
adequately assess. It warrants one prospective synthetic method gate with
full paid-label accounting. This Stage 29 calculation alone establishes
neither a new statistical result nor an ICML contribution. Do not present
the 95.52% feasibility count or the 0.9191 cost ratio as achieved savings.
