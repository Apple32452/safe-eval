# Stage 19 findings: common-core adaptive tail

## Result

The frozen 75% development gate failed. The common-core adaptive-tail candidate
certified 1,170.94 correct pair conclusions per repeat, compared with 1,275.70
for the Stage 18 common random test set. The deficit was 104.76 conclusions
(conditional Monte Carlo standard error 1.57), or 8.21% of the control total.
The candidate lost all 50 repeat blocks and had positive language-level mean
differences in four of 14 directions. Both methods made zero observed wrong
declarations.

As required by the paired design, the methods were exactly equal at 25% labels:
241.58 conclusions each. At 50%, immediately after the common core, the
candidate gained 7.92 conclusions (MCSE 0.29), or 1.00%. That early advantage
reversed as more pair-specific tail labels fragmented across items. At 75%, the
common test set was decisively better.

## Audit

The protocol and implementation lock were committed before the one-repeat and
50-repeat runs. The audit verifies the implementation lock, WMT25 source and
matrix hashes, the exact Stage 18 reference, all 2,100 candidate rows, complete
budget and pair accounting, monotonicity, exact equality at the paired 25%
checkpoint, and a 42-row exact repeat-zero replay.

## Conclusion

Retaining a 50% common core reduces the deficit of Stage 18's fully fragmented
frontier from 152.90 to 104.76 conclusions, but it does not make the adaptive
tail competitive at the primary budget. The precommitted protocol prohibits
further WMT25 searches over core fractions or frontier utilities.

The next method should remain on one common item stream and skip only labels
that cannot advance any unresolved comparison. Such active-system pruning can
be proved to weakly dominate the unpruned common test set pathwise in label cost;
it tests a distinct structural contribution rather than another tuned mixture
of common and pair-specific paths.
