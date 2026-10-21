# Stage 16 findings: WMT25 external validation

## Result

The frozen external gate passed on all 14 included WMT25 language directions,
covering 2,197 system pairs. At the primary 75% unique-label budget,
`frontier_evidence` certified 801.10 correct pairwise conclusions per repeat on
average, compared with 724.34 for `evidence_first`. The paired gain was 76.76
conclusions (conditional Monte Carlo standard error 5.44), or 10.60% relative
to the matched evidence-first scheduler. The gain was positive in 49 of 50
repeat blocks and in all 14 language means. Both policies made zero observed
wrong declarations.

The secondary paired gains were 2.56 conclusions at 25% labels (MCSE 0.57;
35 wins, 3 ties, 12 losses) and 35.48 at 50% labels (MCSE 3.82; 46 wins and
4 losses). Thus the effect grows with the label budget on this benchmark.

## Integrity record

The protocol and initial implementation were committed before downloading the
complete WMT25 outcome file. The first parser invocation failed before writing
a matrix because WMT25 also uses the severity string `undecided`. A schema-only
diagnostic counted severity labels without summarizing scores, systems, pairs,
or methods. `AMENDMENT_1.md` then precommitted recognition of `undecided`; the
binary outcome remained unchanged because every nonempty error list maps to
zero. The amended lock was committed before parsing or running again.

The saved table contains 6,300 rows. The audit verified source and matrix
hashes, the full result grid, pair and budget accounting, monotonic checkpoints,
and an exact 126-row repeat-zero replay. The primary 50 repeat differences are
stored in `SUMMARY.json`; the sole aggregate loss was -11 conclusions.

## Interpretation and limits

This is strong external evidence that annotation-level frontier scheduling can
produce more certified pairwise conclusions than pair-level evidence-first
scheduling at the same unique-label budget. It reproduces the larger-budget
WMT23 development signal on a newer dataset with more languages and systems.

This result alone is not yet an ICML contribution. The strict error-free
consensus target is a binary proxy rather than the official continuous WMT25
human score. The next scientific work is to formalize the scheduling objective
and guarantee, then compare against matched active-ranking and submodular
allocation baselines on a practical score-margin target. Stage 16 should remain
frozen as external evidence for the present candidate, not become tuning data.
