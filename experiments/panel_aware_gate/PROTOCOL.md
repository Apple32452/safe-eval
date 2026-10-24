# A panel-aware adaptive correction: frozen synthetic feasibility screen

Date: 2026-10-24. This asks whether a paid-pilot, target-corrected
context allocation can improve *simulated* five-way task cost for one
prespecified A/B comparison. It is development work, not a human study or
an ICML novelty claim. WMT24 and WMT25 outcomes are not used.

## Target, simulator, and matched controls

Two five-system companion contexts P0 and P1 have a fixed target mixture
`pi=(.5,.5)`. On each independent fresh task, the signed A-over-B preference
is `+1` with context-specific probability `p_s` and `-1` otherwise.
The target `theta=sum_s pi_s*(2*p_s-1)` is fixed before sampling.
Only one of the two panels is judged per task. Context-dependent positive
task-duration units `c_s` are specified for the simulator; **these units
are not measured human minutes**.

Use 100 matched random-number ledgers per scenario, 2,000 tasks maximum,
alpha=.05 for two directional nulls, four fixed bets
`rho=(.10,.25,.50,.80)`, first crossing threshold `2/alpha=40`.
Every method spends the first 20 tasks on target-randomized panels. Thereafter:

1. `target_random`: continue to sample P0/P1 with probabilities `pi` and
   use raw signed preferences.
2. `adaptive_ipw`: estimate context means from previously purchased tasks;
   choose `q` below and correct `X=pi_s*Y/q_s`.
3. `adaptive_augmented`: choose the same `q`, make the predictable estimates
   `m_s=sum(Y in s)/(count_s+4)`, put `b=sum_s pi_s*m_s`, and use
   `X=b+pi_s*(Y-m_s)/q_s`. The proposal is the 0.3 target reserve plus
   0.7 times the normalized weights
   `pi_s*sqrt(max(.05,1-m_s^2))/sqrt(c_s)`.

For the adaptive signals, bet conservatively using a predictable lower
bound `L` and upper bound `U` obtained by evaluating both potential signs
at each available context. The positive-null factor is
`1+rho*X/max(1,-L)` and the negative-null factor is
`1-rho*X/max(1,U)`. Conditional on the full past, both corrected signals
have expectation `theta` for **any** predictable estimates and positive
proposal, so these factors and their fixed stake mixtures control
directional error under the corresponding null. Target random uses the
same factors with `L=-1,U=1`. Simultaneous false-direction risk is <=.05
at arbitrary stopping times via Ville and a union bound. Wrong-target
declarations, abstentions, complete costs and duration units are all saved.

## Predeclared cases and gate

| Scenario | `p0,p1` | Duration `c0,c1` | Purpose |
| --- | --- | --- | --- |
| `unequal_variance` | .50,.95 | 1,1 | Hard versus easy context |
| `unequal_duration` | .80,.80 | 1,3 | Equal signs, unequal task time |
| `mixed_variance` | .98,.55 | 1,1 | Very different conditional variances |
| `homogeneous` | .80,.80 | 1,1 | Neutral allocation check |
| `opposed_tie` | .90,.10 | 1,1 | Exact target tie; unresolved is valid |

Seed is SHA256 of `(20261024,scenario,repeat)` and the two methods share
each task's latent panel-choice and judgment uniforms. Report mean actual
duration units to **correct completed conclusions** for the three
heterogeneous non-tie cases; no credit for cheap abstentions. The
internal gate requires the augmented candidate to complete at least
as often as both valid controls, have no wrong declarations observed,
and save at least 10% mean duration versus **both** controls in at least
two of the three heterogeneous cases. Report the homogeneous and tied
cases regardless of outcome; they cannot substitute into the gate.

This simple doubly robust signal, propensity correction, and variance-guided
allocation are established ideas (Waudby-Smith et al. 2022; Hait 2026).
Passing would only justify trying a stronger published comparator and an
independently randomized human study, never an ICML novelty claim. A
failure closes this candidate without adjusting its scenarios or gate.
