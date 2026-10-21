# Stage 17 findings: continuous-score development

## Frozen result

The WMT25 continuous-score development gate passed. At the primary 75% unique
label budget, `frontier_evidence` certified 1,122.80 correct pair conclusions
per repeat on average, compared with 1,109.98 for `evidence_first`. The paired
gain was 12.82 conclusions (conditional Monte Carlo standard error 1.68), with
42 wins, two ties, and six losses over 50 repeat blocks. Its mean gain was
positive in 11 of 14 language directions. Every tested policy made zero
observed wrong declarations.

The secondary gains over `evidence_first` were 2.64 conclusions at 25% labels
(MCSE 0.98; 29 wins, six ties, and 15 losses) and 7.02 conclusions at 50%
labels (MCSE 2.09; 33 wins, one tie, and 16 losses). These comparisons use the
same frozen continuous-score estimand and the same label budgets.

## What this establishes

The result extends the scheduling signal from the Stage 16 binary proxy to the
mean recorded WMT25 human score. The accompanying theory gives a
scheduler-independent family-validity argument and an exact one-step
optimization interpretation for the modular frontier potential. The saved
table has 12,600 rows. The audit checks the source and matrix hashes, result
grid, pair and budget accounting, monotone checkpoints, and an exact 252-row
repeat-zero replay.

## Blocking baseline

The `uniform_labels` and `round_robin` controls are structurally weak for this
prefix-based certificate. Random individual labels fragment the observations
across items, so few pair paths acquire long consecutive prefixes; they certify
zero and 4.14 pairs respectively at the primary budget. Those values cannot
support a useful efficiency claim.

A common random test set is the necessary next baseline: sample one item order
per language and score every system on the same growing set of items. This is
the natural smaller-test-set design and advances all pair comparisons together.
Stage 17 therefore does not by itself establish an ICML contribution. Stage 18
must compare `frontier_evidence` with that common-item baseline under the same
continuous e-process, label budget, and family error allocation.
