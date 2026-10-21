# Stage 18 findings: common random test-set baseline

## Decisive result

The frozen development gate failed. At the primary 75% unique-label budget,
the Stage 17 `frontier_evidence` candidate certified 1,122.80 correct pair
conclusions per repeat, while evaluating every system on the same growing
random test set certified 1,275.70. The candidate deficit was 152.90
conclusions (conditional Monte Carlo standard error 2.07), or 11.99% of the
control total. The candidate lost all 50 repeat blocks. Its language-level
mean difference was positive in five of 14 directions. Both methods made zero
observed wrong declarations.

The candidate also lost at the secondary checkpoints. At 25% labels it
certified 88.72 pairs versus 241.58 for the control, a deficit of 152.86
(MCSE 1.41). At 50% labels it certified 431.90 versus 790.68, a deficit of
358.78 (MCSE 1.96).

## Audit and integrity

The common-test-set protocol and implementation were committed before the
50-repeat control was computed. The first one-repeat smoke simulation completed,
but its summarizer stopped before comparison because it loaded all 50 archived
candidate repeats. `AMENDMENT_1.md` records the grid-filter correction. The
corrected checker and lock were committed before the full experiment, without
changing the protocol, outcomes, scheduler, gate, or seeds.

The final audit verifies the implementation lock, WMT25 source and matrix
hashes, the exact archived Stage 17 candidate, all 2,100 Stage 18 result rows,
budget and pair accounting, monotone checkpoints, and an exact 42-row
repeat-zero replay.

## Scientific conclusion

The present annotation-level frontier scheduler is not a competitive method
for shrinking a common MT test set. Its separate pair paths fragment labels
across items. A common item supplies a completed observation to every system
pair, so the common-test-set control obtains substantially more usable prefixes
at the same unique-label cost.

This result rejects the current scheduler as the proposed ICML contribution.
It also identifies a precise next candidate: retain a common random prefix for
all systems, then spend only the remaining label budget on unresolved pair
frontiers. That common-core design must beat this Stage 18 control under a new
frozen gate before any external confirmation or contribution claim.
