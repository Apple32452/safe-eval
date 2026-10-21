# Stage 20 findings: active-system pruning

## Result

The pathwise dominance theorem held in every saved case, and active-system
pruning improved the aggregate total in all 50 repeat blocks. At 75% labels it
certified 1,284.18 correct pair conclusions per repeat versus 1,275.70 for the
unpruned common test set. The gain was 8.48 (conditional Monte Carlo standard
error 0.32), or 0.665%. Both methods made zero observed wrong declarations.

The gains were 0.26 conclusions at 25% labels (MCSE 0.08) and 4.52 at 50%
(MCSE 0.32). At 75%, six language directions had positive mean gains and eight
tied at zero. The frozen gate therefore failed its requirement that more than
half of the 14 languages improve, even though the aggregate gain exceeded two
MCSEs and every repeat won.

## Structural result

For every fixed common item path and label budget, the pruning policy resolved
at least every pair resolved by the common control. It skipped a system only
after all incident comparisons were frozen, and its within-item order was the
control order restricted to active systems. The observed minimum resolved-pair
difference across all 2,100 saved cases was zero; there were no pathwise losses.

The audit verifies the implementation lock, WMT25 source and matrix hashes,
exact Stage 18 reference, complete grid and budget accounting, monotonicity,
pathwise dominance, and a 42-row exact repeat-zero replay.

## Contribution assessment

The theorem is clean and the gain is real, but the effect is small and limited
to six languages under the complete comparison graph. Recent work already
covers sequential model evaluation, ranking, and multi-model confidence sets.
Stage 20 therefore does not by itself support an ICML contribution claim.

The complete graph is the hardest setting for removing a system: one unresolved
incident edge keeps it active. The next distinct question is inference rather
than acquisition. A pilot can propose a system order, a held-out finite-pool
test can certify only adjacent relations with `S-1` family tests, and transitive
closure can recover many or all `S(S-1)/2` pair conclusions. That design directly
targets preservation of the full ranking while reducing the multiplicity cost.
