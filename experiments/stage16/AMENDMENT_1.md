# Stage 16 amendment 1: recognized WMT25 severity

## Trigger

The source and implementation locks were committed before the complete WMT25
file was downloaded. The first frozen parsing attempt stopped with
`Unknown or malformed retained error`; it produced no derived matrix and no
method result.

A schema-only diagnostic then enumerated error severity strings and dictionary
key sets. It did not aggregate annotation scores, system outcomes, pairwise
results, or method performance. The exact source contained 100,911 `major`,
167,980 `minor`, and 250 `undecided` error records. All errors used the keys
`end_i`, `severity`, and `start_i`.

## Frozen amendment before rerun

Recognize `undecided` as a valid WMT25 error severity in addition to `minor`
and `major`. The binary outcome does not change: an annotation is one only
when its score is exactly 100 and its error list is empty, so every annotation
with an `undecided` error remains zero. Unknown severities still fail.

No inclusion rule, outcome calculation, seed, threshold, policy, checkpoint,
comparison, or external gate changes. A new implementation lock and commit
record this amendment before the parser or experiment is run again.
