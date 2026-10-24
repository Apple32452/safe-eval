# Fixed-pool shared-panel screen: result and novelty decision

The protocol and implementation were committed to `main` before the
40-repeat run. Four invariants passed, including exact enumeration of the
finite-pool score's conditional mean after prior purchases under wrong
predictions and nonuniform allocation. The audit reproduced all 480
saved paths, checked the 15-pair summaries, and matched the protocol hash.

Each table cell gives **mean simulated duration units to a correct
completed 11-pair conclusion**, with completions out of 40 in parentheses.
Every method completed every repeat, and no wrong direct sign was observed.
All counts are descriptive; the familywise `.05` guarantee follows from
the stated predictable score and betting argument, not from zero errors.

| Scenario | Uniform uncentered | Uniform centered | Adaptive all pairs | Adaptive active pairs |
| --- | ---: | ---: | ---: | ---: |
| No shift | **106.58 (40)** | 110.48 (40) | 111.33 (40) | 108.85 (40) |
| Context shift | 116.15 (40) | 115.63 (40) | **113.88 (40)** | 120.18 (40) |
| Context and cost | 224.35 (40) | 230.23 (40) | **220.60 (40)** | 224.15 (40) |

The candidate **failed** its prespecified screen. Relative to the matched
`adaptive_all` control, active-pair allocation required 5.53% *more*
duration in context shift and 1.61% more in context and cost. Paired
repeat-level bootstrap 95% descriptive ranges for its *relative saving*
versus `adaptive_all` were -11.94% to -0.25% and -6.95% to 3.27%,
respectively. Its small 2.64% saving against uniform centered in context
and cost did not survive the stronger allocation comparison. Zero shift
favored uniform uncentered on mean cost.

The simulator generated genuine context dependence: on the same fixed
item and system pair, the sign varied among the four companion panels
in **31.58%** of pair-item cases under context shift and **32.01%** under
context and cost, versus zero with no shift. A purchased panel revealed
ten dependent pair outcomes while costing exactly one panel task, and
no item-panel cell was purchased twice. No method was evaluated on human
judgments, actual annotation time, or untouched WMT24.

## What is established and what is open

The finite-pool score is exactly unbiased conditionally on past purchases:
the sum over unpurchased cells of its predictable residual cancels the
known/predicted baseline. A union bound over the two directions of the
15 pairwise e-processes gives the declared familywise anytime error
control for this randomized fixed ledger. Correlations among the ten
within-panel comparisons do not affect this marginal argument.
At full exhaustion, the score resolves to the exact fixed-pool target.
These are direct applications of established survey and sequential
inference ideas; the exact-enumeration test checks this implementation.

The simple `adaptive_active` proposal should now be closed as a claimed
efficiency contribution. The earlier one-pair augmented screen passed its
internal synthetic gate, but its positive result did **not** transfer to
this more relevant many-pair, shared-judgment setting. The result does not
prove that adaptive panels cannot help: it refutes this specific frozen
selection rule in these scenarios. Avoid post hoc tuning of its constants
or simulator to reverse this finding.

A methodological paper would need a genuinely distinct panel-constrained
allocation or inference result over the prior target-aware and shared
multi-target literature, then a matched gain under measured human costs.
For comparison, Hait (2026) already develops shared pooled target-set
proposals, centered off-policy scores and simultaneous best-system
identification (https://arxiv.org/abs/2609.37873), and Waudby-Smith et
al. (2022/2024) already derive anytime-valid off-policy inference
(https://arxiv.org/abs/2210.10768). Saha and Gopalan (2019) develop
active subset ranking under a different Plackett--Luce model
(https://proceedings.mlr.press/v89/saha19a.html).

The highest-value next evidence is the prospectively randomized human
companion-panel study in `experiments/stage33` and
`experiments/stage34_panel_randomization`, collecting the specified 160
blinded bilingual ratings with recorded time. Its 40-document design is a
feasibility pilot, not adequate to rule out small effects. Until real
panel judgments exist, simulation cannot establish that this context
effect matters for MT evaluation or that panel correction improves valid
conclusions per human minute.

Reproduce from the repository root:

```bash
python -m unittest -v experiments/shared_panel_gate/test_screen.py
python experiments/shared_panel_gate/run_screen.py
python experiments/shared_panel_gate/audit_screen.py
```
