# Pre-collection task-order and ID amendment

Date: 2026-10-24. No new prospective human judgments existed when this
correction was made. Stage 34's frozen design requires randomized and
recorded order for each rater. The earlier generator wrote tasks in source
item order and exposed `_p0_` or `_p1_` in the visible task ID. That was a
handoff and blinding defect, even though the two-per-context assignment
and within-task display permutation were already randomized.

The generator now independently permutes the task order for each rater
after assigning their 40 source items and panel contexts, records
`task_order` in both tasks and private key, and exports each rater's rows
in that assigned order. Task IDs are deterministic opaque hashes rather
than IDs containing context labels. The response template includes the
assigned order. Keep the private key inaccessible to raters, and record
deviations from assigned order during actual presentation.

This change does not modify the 40-item selection, system translations,
four distinct judges per item, two judges per panel, five-way display
randomization, intended analysis, or the Stage 34 sharp-null test.
Stage 33's seven tests and Stage 34's six tests pass. A dry run with
pseudonymous placeholders is a software check, not human data. Do not
reuse task files generated before this amendment. If an earlier packet
was already sent to a rater, preserve that fact and its presentation
order in the study audit rather than silently replacing it.

The full preflight re-extracted 40 WMT25 development items from the
checksum-verified public JSONL and matched the previously recorded item
manifest byte for byte. Four clearly marked placeholder rater IDs yielded
160 distinct tasks: 40 per placeholder, each document allocated to four
different placeholders with two in each context. Both the descriptive
analyzer and the exact randomization-test CLI completed on artificial
rankings stored only in ignored local dry-run files. Their numerical
outputs are **not** research observations or evidence of a panel effect.
