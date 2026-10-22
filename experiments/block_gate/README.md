# Development screen: partial system blocks on shared items

**Question.** Can a fixed-test-set, anytime-valid comparison buy only some
active systems on a selected item, reuse those scores for every requested
comparison, and finish with fewer paid system–item scores than Stage 22?

This screen holds the score matrix fixed. At each step, one item with at least
one unknown active endpoint is selected uniformly. The lowest-numbered unknown
active system on that item is included; each other unknown active system is
included independently with probability `q`. The entire block is chosen
before any new score is read. Scores are paid for once and cached. An edge is
retired after a valid directional decision, a logical bound, or exact full
exposure. The requested edge family and `alpha=0.05` are fixed in advance.

For an unresolved edge `a-b`, let `A` be the contrast of its already known
scores, and let `pi(c)>0` be the conditional probability that an unknown
endpoint cell `c` enters the next block. The signal is

```
X = A + sum_{c in block} sign_edge(c) * score(c) / pi(c).
```

Conditional on the history, `E[X]` is the exact full-pool contrast for **any**
fixed score matrix. With scores in `[0,1]`, a predictable lower bound is `A`
minus the largest possible inverse inclusion weight for an unknown `b` cell;
an upper bound is `A` plus the corresponding largest weight for `a`.
The implementation uses `1+rho*X/max(1,-lower)` and
`1-rho*X/max(1,upper)` for `rho=(.02,.05,.1,.2,.4,.8)`, averaging each
direction's wealth. Each is a nonnegative e-process under its directional
null. Threshold `2*number_of_edges/alpha`, plus a union bound, controls the
chance of **any false directional declaration at any time** by `alpha`.
Logical bounds and full exposure have no sampling error. Correlations among
systems on the same item are allowed. The positive inclusion floor matters;
setting `q=0` invalidates the signal for skipped systems.

The exhaustive small binary-state audit enumerates every possible next block,
checks its inclusion probability, conditional signal mean, signal bounds, and
one-step e-factor. The `q=1` path audit compares with Stage 22 on the **same
item order**. On all 120 binary pilot matrices, the matched Stage 22 and
`q=1` completion costs were identical. This parity is a diagnostic of this
binary pilot, not a claim of identical processes for arbitrary real-valued
scores or different query histories.

## Fixed 30-repeat synthetic development screen

Numbers below are mean **system–item scores purchased to complete every star
edge**, not partially completed rankings. Each of the four scenarios has 5
systems, 128 binary items, 4 reference edges, and 30 score matrices. Stage 22
shares the `q=1` trial's exact item order. The `q<1` trials use the same score
matrices and fixed random seeds, but their query paths change when an item
is revisited. A cheaper single replicate is not evidence of average saving.

| Scenario | Stage 22 / `q=1` | `q=.75` | `q=.5` |
| --- | ---: | ---: | ---: |
| Easy, independent systems | 129.93 | 147.87 (+13.80%) | 164.37 (+26.50%) |
| Weak, independent systems | 448.13 | 475.43 (+6.09%) | 484.53 (+8.12%) |
| Easy, correlated systems | 114.27 | 132.10 (+15.61%) | 155.10 (+35.74%) |
| Heterogeneous star | 398.27 | 407.93 (+2.43%) | 402.63 (+1.10%) |

No wrong completed signs were observed in the 120 paths per block policy;
the error statement above follows from the e-process argument and does not
follow from this finite pilot. The simple partial-block policy **fails** the
efficiency test. We do not claim an ICML contribution or general impossibility
from four synthetic settings. It has not been evaluated on WMT or new human
judgments. WMT24 remains reserved.

Existing work already covers important parts of this approach:
[active testing](https://proceedings.mlr.press/v139/kossen21a.html),
[active historical-data-guided fixed-set confidence sequences](https://arxiv.org/abs/2607.17409),
[adaptive off-policy confidence sequences for target comparison](https://arxiv.org/abs/2609.37873),
and [shared-item rank confidence sequences](https://arxiv.org/abs/2609.32211).
The last paper expressly leaves adaptive item selection outside its method and
points to inverse probability weighting as a possible repair. Combining known
ingredients is not, on its own, a novel statistical guarantee.

**Next discriminating question:** whether a *predictable, graph-aware block
policy* can choose both an item and its subset of systems using prior scores
or observed history to maximize expected certificate growth **per purchased
score**, while retaining the fixed-pool guarantee and materially beating the
matched full-block control on held-out matrices. An efficiency claim needs a
prespecified gain threshold, an uncertainty interval, WMT development results,
and comparison with existing active testing and adaptive-CS baselines. A
theoretical claim needs a rate or lower bound that those methods do not imply.

Reproduce from the repository root:

```bash
python -m unittest discover -s experiments/block_gate -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/block_gate/block_probe.py \
  --repeats 30 --output experiments/block_gate/results_reference.json
```
