# Fixed-pool, shared-panel comparison: frozen development screen

Frozen 2026-10-24 before implementation and outcome inspection. This is a
synthetic mathematical stress test, not real human evidence or a novelty
claim. It follows the one-pair panel-aware screen but changes the estimand:
six systems, all six five-system panels, and a fixed pool of 96 items. Each
item-panel cell has one deterministic five-system ranking. A purchased cell
reveals all ten within-panel signed comparisons at one panel-task cost.
Exactly 576 unique cells exist; no cell may be purchased twice. For each
of 15 pairs `e`, the fixed target is the average signed outcome over all
96 items and all four panels containing `e`.

## Finite-pool valid score

Immediately before each draw, let `O` denote already purchased cells and
`R` the remainder. Fix predictable estimates `m[e,c] in [-1,1]` and a
strictly positive proposal `q(c)` on `R`. Put `w[e,c]=1/(96*4)` if the panel
in cell `c` contains `e`, and zero otherwise. Define

```text
B[e] = sum(c in O) w[e,c]*Y[e,c] + sum(c in R) w[e,c]*m[e,c]
X[e] = B[e] + w[e,C]*(Y[e,C]-m[e,C])/q(C),  C drawn from q on R.
```

For every fixed ledger of bounded potential rankings, `E[X[e]|past]` is
the exact fixed-pool target `theta[e]`. This includes adaptive `q`,
dependent pair outcomes within a panel, and arbitrary deterministic
companion effects. Predictable bounds for `X[e]` evaluate both signs at
every available panel; absent-pair cells yield `B[e]`. Positive/negative
directional e-factors are `1+rho*X/max(1,-L)` and
`1-rho*X/max(1,U)`, respectively. Average four fixed stakes
`rho=(.10,.25,.50,.80)`. First crossing `2*15/.05=600` yields a direct
sign certificate. A union bound gives familywise ever-wrong probability
at most `.05` under the randomized design. At exhaustion, every outcome
is observed and every nonzero fixed-pool sign is known exactly.

The predictive means in a panel are the previously observed signed sums
for that pair-panel divided by `(count+4)`. The first 48 paid draws are
uniform over remaining cells, for all methods; declarations start only
after all 48. Thereafter compare:

1. `uniform_raw`: uniform remaining-cell draw, predictable `m=0`.
2. `uniform_centered`: same draw, with predictable panel means.
3. `adaptive_all`: centered score with a positive `0.2` uniform-cell
   reserve and `0.8` allocation across panels proportional to
   `n_remaining(panel) * sqrt(sum_{all pairs in panel} max(.1,1-m^2)
   / panel_duration)`.
4. `adaptive_active`: same proposal and centered score, but the sum is
   restricted to pairs that have no direct sign certificate yet. If none
   remain, use the uniform remainder. Every new panel ranking updates all
   of its included pairs, even when that pair was not the allocation's
   reason for choosing the panel.

`adaptive_all` is the essential matched allocation control. The reserve
ensures full support while cells remain; no method uses current outcomes
to choose its own panel. A completed run directly certifies at least
11/15 pairs, or exhausts the entire ledger. Compare correct completion
counts, familywise wrong declarations, mean paid panel tasks and simulated
duration units **conditional on correct completion**; always also report
capped costs, abstentions and any context-free regression. No cheap failed
run counts as a saving.

## Fixed simulator and reproducibility

40 matched repeats, seed SHA256 of UTF-8 `20261024|scenario|repeat` (first
eight bytes little endian), independent panel/item uniforms per round, at
most 576 draws. Generate fixed item-system utilities by adding independent
standard normals to the ordered base values `[0,.28,.72,1.2,1.9,2.7]`.
For panel excluding system `j`, add a context shift to each included
system `k`: `amplitude*cos((j+1)*(k+2))`. Break exact utility ties by
system index. Rank included systems and save ±1 pair results. Scenarios:

| Name | Shift amplitude | Panel duration by omitted system |
| --- | ---: | --- |
| `no_shift` | 0 | 1,1,1,1,1,1 |
| `context_shift` | .75 | 1,1,1,1,1,1 |
| `context_and_cost` | .75 | 1,1,2,2,3,3 |

The per-repeat utilities and the latent panel and item uniforms are shared
across methods. Durations are specified **simulation units, not human
minutes**. No WMT24 or WMT25 outcomes are used. Before interpreting any
efficiency gain, independently replay all paths and inspect completion
and errors. A lower mean correct-completion cost for `adaptive_active`
against both `uniform_centered` and `adaptive_all` in the two shifted
scenarios, with no completion loss, is a development signal only. The
known off-policy and multi-target sequential literature must remain the
primary novelty comparator; a generic positive result does not establish
an ICML contribution.
