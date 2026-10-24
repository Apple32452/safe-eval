# Frozen feasible gap-aware panel acquisition screen

Frozen 2026-10-24 **before** generating these ledgers or seeing stopping
outcomes. The previous `panel_oracle_gap` study used all future outcomes and
only a variance proxy. This study evaluates a feasible, predictable proposal
using the original finite-pool familywise inference and actual simulated
stopping duration. It is a test of a known gap-aware allocation idea, not a
claim of an original ICML method. No human judgments, WMT25, or WMT24 data.

## Matched targets and controls

Reuse `shared_panel_gate/run_screen.py`: six systems, six possible five-way
panels, 96 fixed items per panel, all 15 pairwise four-panel means, the three
specified context and duration scenarios, the finite-pool corrected score,
betting factors, 48-task uniform pilot, α=.05 familywise directional error,
and stop after 11 certified pair directions. Purchase each panel-item cell at
most once. All methods on a matrix receive the same potential-outcome ledger
and the same two latent uniform streams for panel and item sampling.

Run 100 fresh matrices in each scenario, where the random seed is the first
eight little-endian bytes of SHA256 of
`20261024|panel_gap_feasible|scenario|repeat`, with `repeat` 0..99. These
matrices are distinct from both preceding panel experiments. Compare four
methods: the unchanged `uniform_raw`, `uniform_centered`, and `adaptive_all`
from `shared_panel_gate`, plus `gap_pilot`. All use the same exact stopping,
recovery at full exhaustion, error budget, and task duration charges.

## Feasible candidate

For each completed panel purchase, use only its revealed pair outcomes to
update counts and sums. Let `m[e,p]=sum[e,p]/(count[e,p]+4)` for eligible
pair-panel cells; no current outcome may change its own proposal. At the
beginning of draw 48 and every 24 draws afterward, compute

```text
theta_hat[e] = sum(p eligible for e) m[e,p]/4
var_hat[e,p] = max(.1, 1-m[e,p]^2) for eligible cells; zero otherwise
C[e,p] = var_hat[e,p] / (16*max(abs(theta_hat[e]),.20)^2)
R_hat(q) = (sum_p q[p]*cost[p]) * max_e sum_p C[e,p]/q[p].
```

Minimize `R_hat(q)` numerically among `sum q=1`, `q[p]>=.2/6`, from uniform
and the original `adaptive_all` first-step weight computed with this `m`
and the scenario's costs. Use the same normalized SLSQP convex epigraph,
feasibility tolerance, and best-feasible-start fallback documented in
`panel_oracle_gap/AMENDMENT.md`; count infeasible solver updates. Freeze the
result `q_star` until the next update. At any subsequent draw, choose among
remaining cells with `q_t[p]` proportional to
`remaining[p] * q_star[p]`; exhausted panels have probability zero. This
quantity is positive for every unexhausted panel. During the first 48 draws
use the original uniform-remaining proposal. Continue to update the centered
prediction `m` every draw for the original finite-pool e-process, regardless
of whether `q_star` updates.

The gap floor `.20`, block length 24, and reserve `.2/6` were fixed before
new stopping outcomes; the previous `.05` oracle floor is purposefully more
optimistic. Do not tune them after this result. The allocation is a standard
target-aware heuristic; any gain against these controls cannot alone establish
novelty beyond published target-aware multi-target allocation.

## Audits and decision

Check candidate proposal predictability under a changed current unobserved
cell; panel probabilities and conditional score bounds under depletion; unique
cells and exact full exhaustion; reproduction of the three original methods;
then independently replay all saved trajectories and summaries. Report all
correct completions, wrong signs, mean capped tasks and duration, and paired
10,000-resample bootstrap descriptive intervals for the ratio of mean
durations (seed 20261025). Never condition duration only on completed paths
when completion rates differ.

For this screen to warrant further research, require the candidate to finish
all 100 paths with no wrong signs in each shifted scenario, to complete no
fewer paths than each control, and to cut mean capped duration by **at least
10% against the least-expensive of all three controls** in *both* shifted
scenarios, with the paired bootstrap lower endpoint above zero against that
strongest control. This 10% is only an internal follow-up criterion, not an
ICML novelty standard. If it fails, report the failure and stop tuning this
specific proposal. Even if it passes, obtain prospective human context and
time evidence and a distinct guarantee or clear prior-art comparison before
considering an ICML contribution.
