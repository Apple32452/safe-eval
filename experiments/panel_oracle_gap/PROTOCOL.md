# Panel allocation oracle headroom probe

Frozen 2026-10-24 before the new synthetic ledgers or optimizer results were
computed. This is an exploratory **lower bound on a surrogate allocation
objective**, not a prospective method or proof of annotation savings. It
tests whether more panel-allocation tuning is warranted after the failed
`shared_panel_gate` screen. No WMT25, WMT24, or human response data enter.

## Fixed data and target

Use the six-system, 96-item, all-six-five-way-panel simulator, base utilities,
panel shifts, and scenario durations in `shared_panel_gate/run_screen.py`.
Generate 100 **new** matrices for each of `no_shift`, `context_shift`, and
`context_and_cost`, using the first eight little-endian SHA256 bytes of
`20261024|panel_oracle_gap|scenario|repeat` as the random seed. Every panel
has 96 rankings. For each of 15 pairs, target the mean signed outcome over
all items and all four eligible panels, as in the previous protocol. Let
`mu[e,p]`, `var[e,p]` be exact item means and population variances of that
panel's signed outcome, and `theta[e]` its four-panel target.

## Oracle proxy

For a full-support panel proposal `q[p]`, define the centered off-policy
second-moment proxy and duration-scaled maximum target difficulty:

```text
v[e,q] = sum(p eligible for e) var[e,p] / (16*q[p])
gap[e] = max(abs(theta[e]), .05)
R(q) = (sum_p q[p]*cost[p]) * max_e v[e,q]/gap[e]^2.
```

The `.05` gap floor keeps exact ties finite and is applied identically to
all proposals. `R` is a **population-informed asymptotic variance proxy**.
It omits finite-time e-process range penalties, with/without-replacement
dependence, pilot and training labels, sequential retirement, and the
completion rule. Therefore a proxy reduction is not a stopping-cost saving.

Compare these three positive panel proposals:

1. `uniform`: exactly `q[p]=1/6`.
2. `all_pair`: the previous proposal with oracle true panel means in place
   of trained estimates: `.2*uniform + .8*remaining_normalized_weight`,
   where `weight[p]=sqrt(sum_{e included in p} max(.1,1-mu[e,p]^2)/cost[p])`.
   Use equal remaining counts across panels for this first-step proxy.
3. `oracle`: numerically minimize `R(q)` over `sum q=1`, each
   `q[p]>=.2/6`, starting from uniform and `all_pair`; retain the lower
   feasible objective. This full-ledger oracle is deliberately infeasible
   as an actual acquisition rule.

The numerical optimizer is SciPy SLSQP, tolerance `1e-10`, 3,000 iterations.
Verify feasibility and that its objective is no higher than either starting
proposal up to `1e-7` relative tolerance. Record objective ratios and all
proposal coordinates for each matrix, scenario, and repeat. An independent
audit recomputes every result from regenerated ledgers.

## Decision

Report mean and median `1-R(oracle)/R(all_pair)` in each scenario, plus paired
bootstrap descriptive 95% intervals for the ratio of mean proxies (10,000
resamples, seed 20261024). If the **mean oracle headroom** is below 10% in
both shifted scenarios, stop tuning this panel-proposal objective. If it is
at least 10% in either shifted scenario, the next step is a **feasible**
predictable method evaluated by complete correct conclusions per paid task
and measured human minute against target-aware pooled controls. The 10% is
only an internal resource-prioritization threshold, not an ICML standard.

Any positive oracle gap is partly explained by already published target-aware
gap-sensitive allocation (Hait 2026), so this experiment **cannot establish
novelty**, even if the screen flags headroom. A method and theorem beyond
that baseline would still be required.
