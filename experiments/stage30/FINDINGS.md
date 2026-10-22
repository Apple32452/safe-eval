# Stage 30 decision: shared reference saves some labels, but misses the gate

The fixed 100-repeat prospective synthetic run produced 1,500 method
trajectories. The saved-result audit checked every cost and edge-state row,
recomputed all aggregate values and gate decisions, and replayed 30 endpoint
trajectories against their item/rater/query ledgers. Four focused tests pass.

Every method completed **100/100** runs in each non-tie scenario, with no
observed wrong directional declarations. The 95% intervals below are
descriptive paired-ledger bootstrap intervals for the percentage saving of
`partial` over `paired`; they are not confidence intervals for validity or
a new-rater coverage claim.

| Synthetic scenario | Paired labels | Partial labels | Degree-switch labels | Best saving | Partial 95% descriptive interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| Shared easy | 458.57 | 435.90 | 436.16 | 4.94% | [3.94%, 5.91%] |
| Shared weak | 638.86 | 628.51 | 627.05 | 1.85% | [0.39%, 2.74%] |
| Independent | 726.49 | 658.17 | 671.78 | 9.40% | [7.47%, 11.06%] |
| Long tail | 498.63 | 478.87 | 475.51 | 4.64% | [2.94%, 4.96%] |

The `best saving` column selects the cheaper of the two frozen partial
methods in each scenario. The interval always refers to `partial` alone;
the independent interval overlaps 10%, but its observed saving is 9.40%,
below the frozen gate. All four scenario gates and the overall requirement
of three passing scenarios **fail**. The degree switch did not rescue the
late-edge cost enough to clear a scenario gate.

On the exact-tie control, all methods left that edge unresolved at the
2,000-round cap. The paired, partial, and switched mean costs were
4,409.41, 3,870.13, and 4,365.97 labels respectively. The partial method's
lower cost there is **not** an inexpensive ranking conclusion. No wrong
directional declaration was observed across the 1,500 trajectories;
the finite-sample family error claim follows instead from the prospective
iid sampling and conditional e-process argument in the README.

This pilot supports a small, specific shared-cost effect relative to its
full-paired control. Its binary item/rater population, repeated paid labels,
online predictor, fixed `q=0.75`, and simple betting mixture are synthetic.
It neither establishes savings on actual human judgments nor outperforms
the strongest published off-policy and rank-confidence methods in a matched
comparison. The WMT25 Stage 29 cross-fitted cost screen was optimistic;
its 0.919 local ratio did not translate into a 10% stopping-cost saving in
any of these scenarios. **We have not found an ICML contribution.**

Further tuning this same partial-query rule after seeing these failures
would be exploratory. A new claim needs a distinct joint allocation or
inference theorem, full paid-label accounting, a strong published-method
baseline, and a genuinely untouched external confirmation. WMT24 remains
reserved and uninspected.
