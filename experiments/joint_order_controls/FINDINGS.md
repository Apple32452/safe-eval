# Matched rebalancing removes the joint-ordering efficiency signal

Date: 2026-10-25. **Status: the present candidate does not establish an ICML
contribution.** This diagnostic follows the failed original expansion gate;
it does not change that gate or provide independent confirmation.

The [protocol](PROTOCOL.md) was published before these control outcomes
(commit `363ddf96`), and the code, tests and mechanism note were published
before the full control run. We reused all 100 original fixed matrices:
three systems, 16 binary items, 20 matrices in each of five scenarios.
The original joint candidate, priors, item orders and cell paths were fixed.

## Main finding

The original exact-pair control maintained separate accumulated wealths and
combined them. The new `rebalanced_pair_order` control instead selects a
predictable convex combination of the same exact pair factors at every step,
then multiplies those combined factors over time. It uses the same purchases,
predictions, familywise error guarantee and individual-sign decision rule.
It does not directly optimize over the full joint null polytope.

The candidate and this control have **identical paid completion costs in
197 of 200 matrix-graph tasks**. The candidate wins one task by one label and
loses two tasks by four labels and one label. All methods finish correctly
in this sample. The same-cost comparisons below therefore also hold for
the error-penalized costs.

In the independent strong-gap setting, the earlier candidate savings of
8.20% for stars and 6.16% for triangles relative to the requested-edge
accumulated-wealth control both become **0.00%** against rebalanced pair
factors, with paired bootstrap intervals [0%, 0%] on these saved cases.
This supports attributing the observed advantage to the evidence aggregation
rule. It does not prove the two algorithms equivalent on all matrices or
at all histories.

## All fixed scenarios

Mean unique purchased judgments out of 48; lower is better. A star requests
two comparisons against reference system 0; a triangle requests all pairs.
Both common-item controls use exact finite-pool difference histograms,
predict their next paired difference from past counts and the original
priors, and retire systems with no unresolved requested comparisons.

| Scenario | Graph | Joint candidate | Rebalanced pairs | Paired exact closure | Paired exact Bonferroni | Stage 22 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Independent strong | Star | 29.65 | 29.65 | 29.55 | 30.30 | 33.50 |
| Independent strong | Triangle | 35.05 | 35.05 | 36.45 | 37.15 | 38.65 |
| Independent moderate | Star | 39.30 | 39.10 | 40.00 | 40.05 | 41.10 |
| Independent moderate | Triangle | 41.60 | 41.65 | 43.40 | 43.40 | 43.55 |
| Correlated strong | Star | 28.40 | 28.40 | 29.40 | 30.00 | 34.25 |
| Correlated strong | Triangle | 34.90 | 34.90 | 34.90 | 35.90 | 38.70 |
| Reversed predictions | Star | 37.90 | 37.85 | 35.55 | 35.75 | 34.65 |
| Reversed predictions | Triangle | 41.40 | 41.40 | 39.45 | 39.75 | 39.70 |
| Near ties | Star | 44.90 | 44.90 | 43.70 | 43.70 | 44.00 |
| Near ties | Triangle | 45.80 | 45.80 | 45.50 | 45.55 | 45.75 |

The prediction-aware common-item closure is competitive. Against it, the
candidate's independent strong-gap saving is **-0.34%** for stars
(descriptive paired 95% interval -14.19% to 12.07%) and **3.84%** for
triangles (-3.16% to 11.39%). Neither interval establishes a positive gain.
The moderate-gap triangle has a 4.15% saving (0.80% to 7.92%), but its
rebalanced cell control achieves essentially the same cost as the candidate.
Under reversed predictions the candidate instead costs **6.61% more** for
stars and **4.94% more** for triangles than common-item closure.

All intervals are descriptive, computed after the original experiment on
reused matrices. They are not independent validation or simultaneous
multiple-comparison claims. No additional repeats were added after looking
at these outcomes.

## Mathematical boundary

The [mechanism note](MECHANISM.md) expresses the best predicted one-step log
factor as a KL projection onto the convex conditional null family. Joint
constraints help strictly only when they exclude the pair-null projection.
For a neighboring swap in an initially ordered three-system prediction,
the pair projection already satisfies the entire wrong order: the optimal
joint and pair log growth are equal. Two analytic examples verify this
equality numerically.

A different reversed-order example has a genuine joint information gain:
predicted log evidence per cell is 0.28949 for joint calibration, 0.26333
for rebalanced pair factors and 0.24538 for the strongest single pair.
That calculation does not establish cheaper complete certification.
Improving an ordering that is easy to reject may leave the difficult
neighboring alternatives unchanged, and the predictive law may be wrong.

These are applications of established growth-optimal e-value principles.
No new stopping-cost, lower-bound or sample-complexity theorem is claimed.
The [validity note](VALIDITY.md) gives the conditional argument for both
new controls, including freezing resolved pairs and charging retired systems.

## Verification

- All five original joint-order tests and five additional control tests pass.
- Exhaustive enumeration covers all 64 three-system/two-item binary matrices,
  both item permutations, both graphs and both common-item methods: **512
  complete paths**. Maximum enumerated fixed-matrix familywise error is zero.
- The independent full audit reconstructs **600 new graph-method results**
  and their purchase ledgers, first decisions, completion costs and summaries.
- It checks **17,622,080** rebalanced-factor conditional expectations and
  **958,105** paired-factor expectations against compatible integer null
  completions. The maximum is 1.0000000000000004, within floating-point
  rounding. The conditional proofs, rather than zero empirical errors,
  supply the stated error guarantee.
- No solver reports failure. Rebalancing uses no numerical fallback. The
  paired solver invokes its valid unit-factor safeguard 11,698 times across
  the four graph-method runs per matrix, including null-compatible predictive
  states where the unit factor is optimal. All such factors are audited.
- Rebalanced controls need no extension beyond the archived cell prefixes.
  The original source archive is identified by SHA256 in the metadata.
- No human judgments, measured annotation times, WMT25 outcomes, or WMT24
  holdout were used. The source is still a small synthetic diagnostic.

## Decision and next research requirement

The current joint-calibration variant is **not supported as a distinct
efficiency contribution**. Preserve its original measurements, with this
stronger-control qualification. Do not promote the earlier 8.2% or 6.2%
numbers as evidence of novelty, and do not tune this variant on the same
100 matrices to restore those percentages.

Retain both rebalanced pair evidence and prediction-aware common-item
retirement as required controls in future work. Before another large
performance study, the useful theoretical target is a family of fixed-pool
comparison problems for which a new method has a demonstrably better
attainable judgment cost than these controls. That requires identifying the
limiting alternative orderings and the paid observations needed to reject
them. A one-step log-growth advantage on an easy null is insufficient.

This is progress in narrowing the research question, not an ICML-ready
method or a promise that the remaining question has a positive answer.

## Reproduce

From the repository root, with a new output directory:

```bash
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest discover -s experiments/joint_order_controls -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/joint_order_controls/mechanism_check.py --output results/joint_order_mechanism.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/joint_order_controls/run_controls.py --source experiments/joint_order_gate/results_reference/cases.json --output results/joint_order_controls_local
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/joint_order_controls/audit_controls.py --source experiments/joint_order_gate/results_reference/cases.json --input results/joint_order_controls_local --output results/joint_order_controls_local/audit.json
```

The committed `results_reference` directory contains all new ledgers,
summaries, metadata, the full audit and the analytic mechanism checks.
The original fixed matrices remain in `joint_order_gate/results_reference`.
