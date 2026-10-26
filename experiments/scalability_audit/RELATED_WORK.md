# Focused primary-source audit (2026-10-26)

This is a targeted check of the suspected bottlenecks, not an exhaustive novelty
claim. Papers are read without downloading evaluation datasets or WMT24.

| Primary work | Relevant result / scope | Does it solve this audit's bottleneck? |
|---|---|---|
| [Waudby-Smith & Ramdas, bounded means by betting](https://arxiv.org/html/2010.09686v6) | Predictable plug-in and betting constructions, including finite-pool sampling; Appendix C discusses computational cost differences between betting schemes. | Efficient scalar inference is established. It does not eliminate graph-wide repeated scans in this particular replay. Changing bets is not certified to retain its stopping labels. |
| [Howard et al., time-uniform nonparametric CSs](https://arxiv.org/abs/1810.08240) | Mixture/stitching methods and empirical-Bernstein time-uniform boundaries. | Existing sufficient-statistic/boundary methods are strong computational alternatives. A different boundary is not an identical-power replacement without a comparison proof. |
| [Waudby-Smith & Ramdas, WoR CSs](https://arxiv.org/abs/2006.04347) | Time-uniform confidence sets for a finite population under random sampling without replacement. | Finite-pool validity itself is established; standard streaming state avoids keeping every historical confidence set. |
| [Rank Confidence Sequences, v1](https://arxiv.org/html/2609.32211v1) | Pair wealths plus ordering closure. Exact enumeration, polynomial shortcut, integer programming; Appendix C.4 gives a coNP-hardness result for general exact certification. | Large-scale shortcuts exist, but may certify fewer comparisons than exact closure. They do not establish unchanged annotation cost for a new SAFE-EVAL replacement. The difficult exact-closure question is already identified in prior work. |
| [AnyRank, v1](https://arxiv.org/html/2610.14603v1) | Sequential graphical testing, adaptive trial allocation and prior-informed ranking under its sampling assumptions; scalability experiments emphasize sample complexity. | Related ranking/retirement mechanisms already exist. Those experiments do not establish CPU/memory performance on this 400-system fixed-pool workload. Its i.i.d. rollout setting is not our common-prefix finite pool. |

## Interpretation

The cheap scalar primitives are not an unsolved computational invention.
Streaming a fixed mixture, recording first decisions, counters for absorbing
states and dependency indexing are standard computational ideas. COMPLEXITY.md
shows why these can preserve the exact Stage22 ledger; this is not a new CS
construction or a claim that these ideas have never appeared in an evaluator.

Conversely, no cited work proves that every simultaneous pairwise inference
task can be computed in subquadratic time with the same annotation efficiency.
Full pair output can itself be quadratic; full trajectory output is pair-item
sized. General exact order closure has a distinct computational barrier. Neither
fact transfers automatically to the independent-edge Stage22 rule benchmarked
here. Approximate/conservative closure may be valid but decide later.

Per-system simultaneous confidence intervals can induce pair signs with only
S evolving marginal states. That changes the evidence: their differences can
ignore shared-item covariance. Fixed-null mixtures do not require inversion
over a large mean grid. All-time validity therefore does not inherently require
SAFE-EVAL's offline PN history arrays, but existing alternative CS guarantees
alone do not prove unchanged stopping times.

The prior [method screen](../method_screening/REPORT.md) also matters: an expensive
joint candidate tied a strong rebalanced control in 197/200 small tasks, and
full-block DP tied matched-law paired factors in 30/30 cases. Those are different
small workloads and are not scaled-performance measurements. They caution
against selecting a research target solely because its implementation is slow.

Research GO would require a genuine computational theorem for a statistically
competitive target beyond these known tools, with matched annotation cost or
a proved tradeoff. A faster generic implementation, weaker output objective,
changed alpha allocation, or delayed look schedule does not meet that standard.
