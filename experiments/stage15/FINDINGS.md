# Stage 15 findings: frontier utility development test

The protocol and implementation were committed before the full WMT23 run.
The experiment used all 237 within-language pairs, 50 matched random-order
blocks, the family threshold 9480, and fixed checkpoints based on the number
of unique system-item labels. All source and data hashes matched the
implementation lock. The first 12 blocks of all three controls exactly
reproduced 324 saved Stage 14 rows.

## Result

Mean correctly certified comparisons, summed over the three languages (237
possible), were:

| Policy | 25% labels | 50% labels | 75% labels |
| --- | ---: | ---: | ---: |
| Random pair focus | 6.90 | 18.08 | 38.66 |
| Fixed pair focus | 10.78 | 22.90 | 42.10 |
| Evidence-first pair scheduling | 9.28 | 28.64 | 83.66 |
| Unweighted frontier count | 0.00 | 1.68 | 11.90 |
| Evidence-weighted frontier utility | 8.50 | **29.46** | **94.46** |

The locked primary difference at 50% was **+0.82 pairs** for frontier utility
over evidence-first, with conditional Monte Carlo standard error 0.664. It won
27 repeat blocks, tied 6 and lost 17; block differences ranged from -11 to
+10. This is a positive mean under the literal development gate, but it is
small and statistically unstable across the randomized orders.

At 75%, the difference was +10.80 pairs (MC SE 1.547; 43 wins, 1 tie, 6
losses). All three languages improved: +2.32 en-de, +1.34 he-en and +7.14
zh-en. The policy advanced more pair prefixes per paid label at this budget,
consistent with actual shared-label reuse. At 25%, it lost 0.78 pairs (MC SE
0.324), so it does not uniformly dominate evidence-first.

No wrong declaration was observed for any of the five policies at any saved
checkpoint. This empirical count is distinct from the nominal family guarantee.
Unresolved comparisons remain in every partial-budget result.

## Decision

Stage 15 supplies a candidate scheduling idea, not an ICML contribution. The
primary 50% gain is too weak for a contribution claim, and the large 75% gain
was observed on the same WMT23 development data that motivated the policy.
The unweighted coverage heuristic failed badly, showing that label reuse alone
does not identify useful comparisons. The evidence term is essential here.

The next valid step is external validation of the frozen
`frontier_evidence` rule without changing its formula. A newer benchmark must
be parsed and its evaluation protocol committed before its complete outcome
matrix is examined. A later paper target also needs a practical MQM margin and
a theorem specific to sparse shared annotation allocation.
