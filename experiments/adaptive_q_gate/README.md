# Predictable partial-block allocation: negative development screen

**Result:** the prespecified gate failed. This is exploratory synthetic work,
not a claimed ICML contribution. The new code and frozen comparison are in
[PROTOCOL.md](PROTOCOL.md), [results_reference.json](results_reference.json),
and [audit_reference.json](audit_reference.json).

At each history, choose the probability of buying B on an item where both
system scores are unseen from `{.25, .5, .75, 1}`. For every candidate q,
construct the same worst-null-certified conditional factor as Stage 35 and
compute its expected log increment under the **pre-target** positive
predictive alternative, divided by its expected next-step score cost.
Choose the q with the largest ratio, resolving ties toward larger q.
Compute the negative factor after choosing q. The policy reads only cached
past scores and supplied predictions; q and both factors are fixed before
the current purchase. This preserves the two-sided fixed-pool e-process
validity of each chosen factor. An independently reconstructed ledger audit
checks every selected q and worst-null constraint on saved paths.

The fresh 12-repeat, 32-item screen used **new fixed target matrices**
compared with Stage 35. Aligned predictions equal the synthetic generating
base rates, so these conditions are unusually favorable and do not validate
a historical model. Mean distinct purchased system–item scores:

| Scenario | Exact full | Fixed q=.5 | Adaptive q | Stage 22 |
| --- | ---: | ---: | ---: | ---: |
| Aligned strong | 12.00 | 10.25 | 10.25 | 18.67 |
| Aligned moderate | 32.17 | 27.67 | 33.83 | 38.67 |
| Shifted opposite sign | 30.83 | 30.50 | 32.50 | 33.00 |

Strong-case adaptation selected q=.5 on all 83 steps, so it exactly matched
that fixed control. In the moderate cases it selected q=.75 on 108 steps,
q=1 on 106, and q=.5 on four. Its mean cost was **22.29% greater than
fixed q=.5** there. The prespecified requirement of at least 10% savings
against both exact full blocks and fixed q=.5 in both aligned scenarios
failed. No wrong completed signs and no optimizer fallbacks appeared in the
saved runs. The paired bootstrap intervals in the audit are descriptive
with only twelve repeats.

The observed pattern suggests the greedy one-step ratio values information
from buying B now but does not capture how the purchase affects future cache
states and stopping. This is an inference from this screen, not a proof that
all adaptive block policies fail. It gives no evidence for an ICML claim.
Prior work already develops growth-oriented active querying for conditional
e-values; see [Hsu and Shekhar (2026)](https://arxiv.org/abs/2607.17409).
We did not proceed to a shared multi-system graph or WMT25. WMT24 remains
reserved.

Reproduce from the repository root:

```bash
python -m pip install -r experiments/adaptive_q_gate/requirements.txt
python -m unittest discover -s experiments/adaptive_q_gate -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python \
  experiments/adaptive_q_gate/adaptive_probe.py --repeats 12 --items 32 \
  --output experiments/adaptive_q_gate/results_reference.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python \
  experiments/adaptive_q_gate/audit.py \
  --input experiments/adaptive_q_gate/results_reference.json
```
