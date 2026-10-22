# Stage 27 decision: the simple two-stage population baseline fails on cost

Date: 2026-10-22. The full
[protocol and proof sketch](README.md), [code](two_stage.py), and
[saved exact audit plus replicates](results_reference/RESULTS.json) are
available in this directory. This is synthetic evidence under a specified
prospective item–rater sampling design, not a WMT25 significance result.

## A concrete identification boundary

Suppose the only observed rater always gives reference/candidate scores
`(1,0)`. Consider two possible future-rater populations. Both are exactly
consistent with those observations and give the observed rater 10% population
weight. In world A the unseen rater gives `(1,0)`; in world B it gives
`(0,1)`. The population mean contrast is `+1` in A and `-0.8` in B.
The sign for new raters is not identified by that observed panel without a
sampling design or additional assumptions. The same logic applies to unseen
items. Repeated ratings and control tasks in WMT25 can inform models of
rater variation; they do not establish random sampling of future raters.

## Exact selection-bias audit

Four equally likely item–rater types have potential scores `(1,0)`,
`(1,0)`, `(0,1)`, `(0,1)`, so the population contrast is zero.
Query the candidate with probability one after reference score 1 and
probability 0.25 after reference score 0. The mean difference among
**selected pairs** is `+0.6`, a false directional impression. The
propensity-corrected signal has expectation zero. The script also
enumerates 4,401 binary null, propensity and prediction settings; the
expected corrected signal never exceeds the null and all tested betting
factors have conditional expectation at most one. The algebra in the README
supplies the general argument; enumeration checks its implementation.

## Paired synthetic comparison

There are two requested reference-star edges, 100 item/rater ledgers per
scenario, a common familywise threshold `2M/0.05=80`, and an 800-round
cap. Costs count **system–item–rater judgments**. Means below are costs
to stopping or cap; they cannot be read as completion costs if a method
has unresolved runs.

| Population | Paired completed | Two-stage completed | Paired mean cost | Two-stage mean cost |
| --- | ---: | ---: | ---: | ---: |
| Aligned | 100/100 | 100/100 | 51.24 | 145.86 |
| Weak | 100/100 | 87/100 | 532.23 | 1,294.42 |
| Reversed | 100/100 | 100/100 | 113.22 | 286.92 |
| Exact ties | 0/100 | 0/100 | 2,400.00 | 1,820.03 |

Neither method made a wrong directional declaration in these 400 seeded
ledgers. This observation does not prove the worst-case error bound; the
bound follows from the stated iid design, bounded signal and e-process
argument. On ties, two-stage uses fewer labels only because it declines
some candidate queries; **neither method reaches a conclusion**. The
paired method is materially cheaper for conclusions in all three
non-tied cases. The conservative `1/epsilon` normalization costs power,
which existing variance-adaptive off-policy methods may address.

## Research decision

This test **rejects** the elementary two-stage rule as the proposed
ICML contribution. It is both substantially more expensive than its
matched paired control here and structurally close to prior
[anytime-valid off-policy inference](https://arxiv.org/abs/2210.10768).
Claims about shared-item ranks,
[graph-wide evidence](https://arxiv.org/abs/2609.32248), or
[hierarchical new-task ranks](https://arxiv.org/abs/2606.08679) also face
direct prior-work comparisons. We have no new theorem or matched efficiency
gain from Stage 27.

A further candidate would need a genuinely joint, variance-adaptive
allocation and evidence result for multiple systems under a **prospectively
randomized item and rater design**, plus a proof and comparisons to those
procedures at matched annotation cost and familywise error. The existing
WMT25 data can motivate and stress-test assumptions, but cannot validate
new-rater population coverage retrospectively. WMT24 remains uninspected.
