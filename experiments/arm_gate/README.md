# Separate-arm finite-pool intervals: exploratory negative gate

Date: 2026-10-22. This is a small diagnostic following the negative
[cell-level pilot](../cell_level_gate/README.md). It is not an ICML novelty
claim or a new evaluation method. It uses synthetic binary score matrices;
WMT24 is untouched.

## Question and guarantee

Stage 22 buys paired system scores on a common uniform item order. PR #30's
uniform individual-cell design lost to it. Could a more targeted policy buy
one score at a time, keep a separate uniform without-replacement permutation
for each system, and use an anytime interval for each complete fixed-pool
system mean? The policy samples the unresolved endpoint with the widest
current interval. Its comparisons are declared only when two intervals do
not overlap, or both endpoints have been evaluated completely.

For system `v`, let `N` be the fixed item count, `S` the sum of its first `t`
randomly ordered observed scores, and `m` a candidate full-pool mean. Under
the null `mu_v <= m`, the conditional expected next score is at most
`c=(N*m-S)/(N-t)`. For `0<c<1` the factor
`1+rho*(Y_next-c)/c` is nonnegative, has conditional expectation at most
one, and is fixed before reading the next score. A symmetric factor
`1+rho*(c-Y_next)/(1-c)` tests `mu_v >= m`. Impossible nulls are rejected
by logical bounds. The implementation mixes fixed `rho` values
`{.02,.05,.10,.20,.40,.80}` and tests candidate means on the fixed grid
`{0,.01,...,1}`. A crossed lower (upper) null gives a lower (upper) mean
bound. The sharp logical interval from observed scores is intersected with
the betting interval. At full exposure the mean is exact.

Each of the two directional processes for each of `S` systems is given
threshold `2*S/alpha`. With a fixed score matrix and independent random item
permutation for every system, conditioning on the past leaves that system's
next item uniform among its remaining items. The arm schedule is based on
observed history. Ville's inequality and a union bound therefore imply
that **all system means remain covered at all times** with probability at
least `1-alpha`; every comparison made by nonoverlapping intervals is then
correct. A tie is returned only at exact full exposure. The exact small-pool
test enumerates all binary four-item populations and partial observation
orders and checks the implemented one-step factors. These facts do not
establish novel inference; per-arm confidence sequences and adaptive
allocation are established ideas. The finite grid makes the interval
conservative between grid values, not anti-conservative.

## Matched-matrix pilot

Four synthetic five-system, 128-item reference stars, with 30 fixed binary
matrices each. The two procedures receive the same matrix but draw separate
random acquisition paths; they are **paired by matrix, not by query stream**.
Both use `alpha=.05`, complete all four requested edges, and count each
system-item score once. Stage 22 is called through its frozen
`make_paths`/`simulate_graph` implementation. The baseline risk threshold
is `2*|E|/alpha`; the interval method uses `2*S/alpha` for its `2*S`
directional processes. No previous WMT25 or WMT24 outcome is used.

| Scenario | Stage 22 labels | Separate-arm labels | Extra cost |
| --- | ---: | ---: | ---: |
| Easy, independent | 133.67 | 226.53 | 69.48% |
| Weak, independent | 473.37 | 547.03 | 15.56% |
| Easy, correlated | 115.63 | 221.57 | 91.61% |
| Heterogeneous star | 412.17 | 455.37 | 10.48% |

The separate-arm policy lost on all 30 paired matrices in three scenarios
and on 28 of 30 in the weak scenario. All 120 runs completed and none
reported a wrong sign. That observed count is **not** a coverage proof; the
specified randomized design and e-process argument supply the guarantee.
The small scenarios, policy and threshold grid are exploratory. The
[raw replicates](results_reference.json) preserve both costs for each seed.

Reproduce from the repository root with NumPy:

```bash
python -m unittest discover -s experiments/arm_gate -p 'test_*.py' -v
python experiments/arm_gate/arm_probe.py --repeats 30 \
  --output results/arm_gate_local.json
```

## Decision

Reject this particular independent-arm strategy as a Stage 22 efficiency
improvement. Separate-arm intervals discard within-item pairing. For
correlated item scores, `Var(A-B)=Var(A)+Var(B)-2 Cov(A,B)`: positive
same-item covariance can substantially reduce the variance of a paired
contrast. This is a standard variance identity, not a new theorem. It
helps explain why the shared-latent scenario is much harder for separate
intervals than paired differences. The observation is not a universal
lower bound; more small-grid tuning here is unlikely to provide a credible
ICML claim.

A future candidate should specify a *distinct* graph-wide inference or
allocation theorem before another benchmark run, preserve pairing or prove
when breaking it pays, and compare against strong rank-confidence and
finite-population active-query methods. In an MT human-judgment study, the
estimand must say whether it concerns the recorded finite panel or future
raters; the latter needs a prospective assignment design. Relevant primary
work: [Rank Confidence Sequences](https://arxiv.org/abs/2609.32211),
[Active Testing](https://proceedings.mlr.press/v139/kossen21a.html),
[finite-population active querying](https://arxiv.org/abs/2601.20251),
and [AnyRank](https://arxiv.org/abs/2610.14603).
