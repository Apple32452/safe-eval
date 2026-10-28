# A joint-feasibility boundary for fixed finite test sets

This is a small falsification check for a candidate joint certificate, not a
new SAFE-EVAL method or an ICML claim. It does not use WMT24/WMT25 outcomes.

## Candidate and result

For each system `s`, let `L_s` be the sum of observed bounded scores and let
`U_s` be `L_s` plus the number of unobserved items (scores are in `[0,1]`).
Given the observed partial matrix, allow *all* bounded completions. The exact
range of the full-pool difference for edge `(a,b)` is

    [L_a - U_b, U_a - L_b] / N.

The endpoints are attainable by assigning missing scores on `a` and `b`
independently. Scores on other systems cannot narrow either endpoint. Thus
enumerating the complete joint feasible set gives exactly the same possible
signs for each individual edge as the elementary pairwise row bounds. A strict
sign is deterministically certified if the entire interval is positive or
negative; an exact tie is certified only if the interval is the singleton
zero. Such declarations have **zero** wrong-sign probability on every fixed
matrix for *any* adaptive order of cell acquisition and at *any* stopping time.

The set of *joint sign vectors* can still be smaller than the Cartesian
product of edgewise sign sets (because rankings are transitive). This logical
restriction alone does not make an individual edge sign certifiable sooner.
It may help a different decision target, such as ruling out complete rankings.

The proof is for unrestricted cell values in `[0,1]`; the audit independently
enumerates **all binary completions** for every partial observation state of
three systems and up to three items. Binary row sums attain every integer in
their row intervals, so the same edge-sign projection equality applies.

## Independent exhaustive audit

From the repository root, run:

```bash
python experiments/joint_feasibility_boundary/audit.py --items 2
python experiments/joint_feasibility_boundary/audit.py --items 3
```

The script compares direct enumeration of every compatible full matrix with
an independent analytic row-bound implementation. It checks every edge
projection and the truth of every declared singleton sign for every
compatible fixed matrix. It also counts states where the joint sign-vector
set is smaller than the product of its edge projections. No Stage 22 scheduler
is imported, and no inference about noisy human raters is made.

Audited results:

| Items | Full matrices | Partial states | Edge projections checked | Compatible state/matrix pairs | States with joint restriction |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 64 | 729 | 2,187 | 4,096 | 557 |
| 3 | 512 | 19,683 | 59,049 | 262,144 | 15,913 |

In both sizes there are joint restrictions even when no individual edge is
certified. All analytic and brute-force edge projections agree.

## Implication

This rules out one tempting shortcut: calling the feasible-completion set a
"joint certificate" cannot improve *individual* sign declarations over exact
pairwise deterministic bounds. It does **not** rule out a statistically
calibrated joint confidence process, adaptive risk allocation, or an
alternative target. Any such method must be compared with the existing
pairwise and per-system finite-population baselines at matched family error
and unique-cell cost. The Stage 23
[next-method gate](../stage23/NEXT_METHOD_GATE.md) remains in force.
