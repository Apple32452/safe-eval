# Prediction-aware graph block development screen

This is the follow-up to `experiments/block_gate`. It asks whether a
**predictable** choice of shared item and partial system subset can certify
all requested fixed-pool comparison signs at fewer purchased scores than
the same prediction-aware certificate using full active-system blocks.
Read [PROTOCOL.md](PROTOCOL.md) for the predeclared methods and gate.

Historical outcomes on 256 separate items and publicly available item side
features produce each system's fixed predictions. The target labels are not
used in that fit. A reversed-history scenario tests prediction mismatch.
For each unresolved edge, the centered inverse-inclusion signal is its
known-score contrast plus the predictions for unknown endpoint cells plus
the inclusion-weighted residuals for the bought cells. For **every fixed
matrix and every predictor**, its conditional mean is the full-pool edge
contrast. Predictable support bounds, two-sided e-processes, and a union
bound give familywise anytime error at most `0.05` across the requested
edges. The small-state test enumerates all possible blocks and binary
outcomes and checks this argument directly. It also checks that changing an
unbought target outcome cannot change its own acquisition probability.

## Result: prespecified 30-repeat synthetic development screen

Each scenario has five systems, 128 items, four reference edges, and 30
fixed matrices. Entries are mean purchased system–item scores to **complete
all four comparisons**, not the fraction decided by a partial budget.

| Scenario | Raw Stage 22 | Prediction full | Prediction partial `.75` | Graph partial |
| --- | ---: | ---: | ---: | ---: |
| Easy independent | 124.63 | 127.13 | 125.67 | 163.33 |
| Weak independent | 462.63 | 465.50 | 466.07 | 453.03 |
| Easy correlated | 121.67 | 125.53 | 119.60 | 171.13 |
| Heterogeneous star | 411.17 | 411.77 | 409.33 | 401.53 |
| Reversed history | 123.17 | 127.57 | 127.90 | 135.23 |

The graph policy saved `2.68%` and `2.49%` against the prediction full
control in the weak and heterogeneous aligned scenarios, but cost `28.47%`
and `36.33%` more in the two easy scenarios. It cost `6.01%` more under
reversed history. The prespecified gate required at least 10% saving in two
aligned scenarios and therefore **failed**. In the easy independent first
replicate, the graph policy assigned some endpoints inclusion chance near
`.2` conditional on the chosen item; the maximum absolute betting support
rose from about 137 for full blocks to 653 for graph partial blocks. This
diagnoses how rare purchased cells weakened the conservative certificate.

The fixed `.75` partial policy had small gains in some settings and a small
loss in another. With 30 repeats, the paired uncertainty intervals for these
small differences include zero. No wrong completed signs appeared in the
150 paths per method. The formal error claim comes from the conditional
e-process construction and the exact one-step audit, not from observing
zero errors in a short pilot.

**Interpretation:** this graph heuristic is not an ICML contribution. Nor
does the negative result rule out other block policies. We did not proceed
to WMT25 because the frozen synthetic gate failed. WMT24 remains reserved.
The predictor was trained on simulated repeated observations of the same
systems; its realism for historical machine-translation systems has not
been established.

Relevant existing methods include
[active testing](https://proceedings.mlr.press/v139/kossen21a.html),
[historical-prediction active fixed-set confidence sequences](https://arxiv.org/abs/2607.17409),
[adaptive importance-weighted anytime inference](https://arxiv.org/abs/2609.37873), and
[shared-item rank confidence sequences](https://arxiv.org/abs/2609.32211).
The next theoretical question is whether a graph-aware allocation can
control its worst-case inclusion-weight penalty while retaining a strong
cost guarantee, beyond these existing constructions. A new valid heuristic
without a matched efficiency gain is insufficient.

From the repository root:

```bash
python -m unittest discover -s experiments/predictive_block_gate -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python \
  experiments/predictive_block_gate/predictive_probe.py \
  --repeats 30 --output experiments/predictive_block_gate/results_reference.json
```
