# Stage 31 exploratory result: five-way panels

Under the 2012 Koehn-style 15-system normal-quality model, both panel
policies certified at least 74 of 105 direct system pairs in all 20 matched
replicates within the 6,000-panel cap. The active selector preferred one
of 16 randomly offered five-system panels containing more unresolved pairs.
Every panel supplied ten related pair outcomes; the cost below counts one
five-way judge task per panel, not ten independent human judgments.

| Policy | Completed / 20 | Mean five-way tasks | Mean certified pairs | Mean rank-range width | Wrong direct signs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Uniform panel | 20 | 2,349.95 | 74 | 5.13 | 0 |
| Unresolved panel | 20 | 1,575.40 | 74 | 5.13 | 0 |

The matched saving is **774.55 tasks (32.96%)** on average; the active
policy finished sooner in all 20 matched replicates. A descriptive
repeat-level bootstrap interval for the ratio-of-mean saving is
**27.71% to 37.37%** (10,000 resamples, seed 314159). This interval
describes variability over the generated 15-system problems, not the
probability that a directional declaration is valid. The zero observed
errors likewise is not a proof of 95% familywise validity; the conditional
supermartingale argument in the README supplies the guarantee for the
stated fresh-input model.

**Research decision:** this answers a useful feasibility question posed by
Koehn's judgment-count study, but it is a development comparison against
uniform panels only. Adaptive subset selection and anytime pairwise ranking
already appear in the literature. We have **not** established an ICML-level
new theorem, an advantage over strong published active-ranking baselines, or
a saving in actual human annotation time. The next work is a theorem-level
comparison with existing subset-wise ranking and anytime leaderboard methods,
then a matched panel-budget comparison on independently sampled human
judgments. Real panel context effects must be included or explicitly ruled
out before transferring the pairwise target guarantee.

Reproduce with the commands in [README.md](README.md). The exact 40 rows and
aggregate summary are in [`results_reference`](results_reference).
