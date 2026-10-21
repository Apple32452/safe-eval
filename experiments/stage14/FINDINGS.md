# Stage 14 exploratory shared-annotation pilot

This retrospective WMT23 development pilot used fixed recorded binary
error-free annotations, 237 unordered within-language system pairs, and 12
precommitted random query orders per pair. Each pair used its own uniform
item permutation and the previously validated standalone categorical PPR.
The threshold 9480 provides nominal 95% family directional error control
over 237 pair conclusions, separately for each scheduling method. One
system-item annotation was charged once and shared by every eligible pair.
The pilot did not obtain new human labels.

The first three schedulers and the primary 50% unique-label budget were
declared before running. Two more concentrated controls (`focus_first` and
`focus_random`) were added **after** the initial results; see PROTOCOL.md.
The table below uses the final matched rerun; all original three-policy rows
matched their saved initial run exactly.

| Scheduler | Mean certified correct pairs at 25% | at 50% | at 75% |
| --- | ---: | ---: | ---: |
| Round robin across pairs | 0.00 | 0.17 | 1.83 |
| Prefer an item needing one new label | 0.00 | 0.33 | 3.17 |
| Finish lowest-index pair first (post-pilot) | 10.67 | 23.08 | 42.00 |
| Finish pairs in seeded random order (post-pilot) | 6.25 | 16.33 | 34.67 |
| Prefer current PPR evidence | 9.17 | 28.25 | 86.67 |

Totals sum the three languages' correct comparisons, out of 237. The
50% budget costs 10,261 unique labels across the three languages, versus
20,523 for complete annotation. At that budget evidence priority certifies
28.25/237 comparisons (11.9%); the remaining 208.75 remain unresolved on
average. The 75% budget costs 15,392 unique labels and certifies 86.67/237
(36.6%). These are **not** full ranking certificates or a demonstration that
the complete pairwise comparison set can be resolved with half the labels.

At 50%, the evidence scheduler exceeds the fixed focus control by 5.17
correct pairs on average across the 12 matched query-order blocks (conditional
Monte Carlo standard error 1.12), and exceeds randomized focus by 11.92
(MC SE 1.28). At 75%, the respective gains are 44.67 (MC SE 1.84) and
52.00 (MC SE 1.91). At 25%, fixed focus exceeds evidence priority by 1.50
pairs, so it does not dominate at every budget. The expanded controls were
post-pilot and the standard errors describe only these seeded random orders.

There were **zero observed wrong declarations** across all saved budget
checkpoints, methods and orders. This finite observation does not mean the
actual error probability is zero; the PPR and union-bound argument in
PROTOCOL.md supplies the stated nominal guarantee under the fixed-pool
design. No tie was called at a partial budget.

The stronger concentration controls show that a large part of the comparison
with round robin comes from focusing work on promising pairs. The improvement
over the two focus controls is a useful signal for a better acquisition
algorithm, but it is neither an ICML contribution nor an optimality result.
The current priority ignores the cost of acquiring a pair's next labels and
does not solve the practically-equivalent-system problem. Existing active
evaluation and anytime leaderboard methods remain essential baselines.
The earlier Stage 13 reserve-cap issue is outside this pilot's PPR-only
inference. No historical predictions were used, so their added value is
untested here.

The next decision should be whether a cost-aware allocation policy can
significantly outperform these controls on a new, uninspected benchmark,
with a predeclared practical MQM difference margin and a proof covering
adaptive querying. Keep zero-history and historical-advice versions paired.
