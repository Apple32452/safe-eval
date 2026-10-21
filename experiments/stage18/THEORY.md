# Stage 18 validity note

Let `X[s,i]` be the fixed recorded score for system `s` on item `i`. The common
test-set control draws one item permutation independently of the scores and
reveals every system's label in precommitted random order within each item.
For any pair `(a,b)`, its completed observations are therefore the differences
`X[a,i]-X[b,i]` in a uniform without-replacement order from the fixed finite
population of item differences.

The Stage 17 e-process is anytime valid along each complete pair path. A
shared-label scheduler can reveal completed prefixes at times depending on
other pairs and on already observed shared labels. Any wrong declaration it
makes is still contained pathwise in the event that the corresponding complete
pair path ever crosses the wrong boundary. Applying the per-pair bound and a
union bound therefore controls the family event without independence across
pairs or a stopping-time condition for the global scheduler.

The common control and frontier candidate differ only in acquisition design.
They use the same fixed matrices, estimand, pairwise certificate, family
threshold, and total number of unique system-item labels at each checkpoint.
The comparison consequently tests whether targeted frontier acquisition adds
certification utility beyond the usual practice of shrinking one common test
set for all systems.
