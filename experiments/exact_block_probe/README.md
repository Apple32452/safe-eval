# Exact partial-block factor: exploratory one-step calculation

**Status:** mathematical and software diagnostic only. This is neither a
sequential experiment nor an ICML novelty claim. It does not establish fewer
judgments than Stage 22.

For a fixed binary pool of `N` items, let `a_i` and `b_i` be the two system
scores. The null for the positive direction is
`sum_i (a_i - b_i) <= 0`. Before seeing the current score, choose an item
uniformly, purchase its `a_i`, and independently purchase `b_i` with
probability `q`. An event records `(item, a_i, b_i)` when both scores are
bought, or `(item, a_i, missing)` otherwise. For any nonnegative event factor
`f`, validity at this first step requires, for **every** fixed binary null
matrix `u`,

```
1/N * sum_i [(1-q) f(i, a_i, missing) + q f(i, a_i, b_i)] <= 1.
```

The script enumerates all such matrices for `N=4` and maximizes expected
`log(f)` under a specified *alternative predictive distribution*, subject to
those exact null constraints. This is the general growth-optimal e-variable
principle applied to this finite observation design, not a new optimality
theorem. It compares with the best stake, for that same predictive
distribution, in the prediction-centered linear inverse-propensity factor
`1 + rho * X / (-min X)`, where `X` is conditionally unbiased for the fixed
pool total. It also computes full-block (`q=1`) cases. Each optimization
result is checked against every enumerated fixed null.

An additional dynamic program finds the most violated fixed-null constraint
for **any proposed one-step factor** in `O(N^2)` time: its state is the
running score difference, and it considers the four possible score pairs at
each item. Tests compare it with exhaustive enumeration for `N <= 4` and
exercise separation for `N=128`. This is a separation oracle, not yet a
solver for the growth-optimal factor at large `N` or after observations.

| Alternative `P(a=1), P(b=1)` | `q` | Exact log evidence / expected score | Linear log evidence / expected score |
| --- | ---: | ---: | ---: |
| `.85, .15` | `.2` | `.1518` | `.0912` |
| `.85, .15` | `.5` | `.2109` | `.1667` |
| `.85, .15` | `1` | `.2077` | `.2077` |
| `.95, .05` | `.2` | `.2855` | `.1328` |
| `.95, .05` | `.5` | `.3530` | `.2393` |
| `.95, .05` | `1` | `.3050` | `.3050` |

These are **first-step, model-averaged** log increments divided by the
first-step expected price `1+q`. They are not a measured stopping-cost ratio.
The `.95, .05` alternative at `q=.5` offers 15.7% more first-step evidence
per score than the full-block exact factor in this tiny model. At `q=.2`,
partial blocks are worse than full blocks on that measure. Under a reversed
`.05, .95` alternative while using the `.95, .05` factor, its expected log
increment at `q=.5` is `-3.3310`: prediction mismatch is a serious problem,
although fixed-null validity remains intact.

The factor is only computed for an **empty history** and one comparison.
It assumes alternative probabilities supplied in advance, and it does not
reuse an acquired score across a graph. Direct constraint enumeration grows
exponentially. For a full method, one would need to use the separation oracle
within a stable optimizer at every history, extend it to cached cells and
shared graph designs, guard against prediction misspecification, establish
simultaneous coverage, and run an actual
paired end-to-end label-cost comparison with Stage 22. WMT25 and WMT24 are
untouched by this diagnostic.

Growth-optimal e-variables are established in
[Safe Testing](https://arxiv.org/abs/1906.07801). Historical predictions,
active fixed-set evaluation, and conditional RIPr factors are treated by
[Hsu and Shekhar (2026)](https://arxiv.org/abs/2607.17409). Shared-item
rank confidence sequences are studied in
[Rank Confidence Sequences (2026)](https://arxiv.org/abs/2609.32211).
The potential research gap is a *computationally practical and empirically
efficient* exact conditional factor for **partial shared blocks** across
requested comparisons. This gap is a hypothesis to test, not an established
novel contribution.

Run from the repository root with SciPy installed:

```bash
python -m pip install -r experiments/exact_block_probe/requirements.txt
python -m unittest discover -s experiments/exact_block_probe -p 'test_*.py' -v
python experiments/exact_block_probe/exact_probe.py
```
