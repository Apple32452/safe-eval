# Cell-level fixed-pool certification: preliminary negative gate

Date: 2026-10-22. This is an **exploratory baseline**, not an established new
method, a locked benchmark protocol, or an ICML contribution. It keeps WMT24
untouched. The frozen Stage 22 source and results are not changed.

## Exact question

There are `S` systems, `N` fixed benchmark items, bounded scores
`y[v,i] in [0,1]`, and a predeclared requested graph `G=(V,E)`. A bought
system-item score is cached and charged once. For edge `e=(a,b)` the target is
the sign of the *complete fixed-pool* contrast

```text
T_e = sum_i (y[a,i] - y[b,i]).
```

We seek simultaneous wrong-direction probability at most `alpha` under any
stopping rule, and fewer **unique purchased cells to complete all requested
conclusions** than Stage 22. Stage 23's max-prefix identity shows that
rescheduling unchanged common-item pair certificates cannot lower the
Stage 22 completion footprint. This diagnostic changes the certificate and
permits individual-cell acquisition.

## A valid but elementary cell certificate

Immediately before a purchase, let `F_t` include previously purchased scores
and query decisions. For every unresolved edge, all unpurchased cells at both
endpoints have positive *known* purchase probability `p_t(c)`. Probabilities
may depend on `F_t` and item metadata, but cannot depend on the unobserved
score of the chosen cell. Write `A_e,t` for the sum of already known scores of
`a` minus those of `b`, and `s_e(c)` for `+1` at `a`, `-1` at `b`, and `0`
elsewhere. Draw an unpurchased cell `C_t` with probability `p_t(C_t)` and set

```text
X_e,t = A_e,t + s_e(C_t) * y[C_t] / p_t(C_t).
E[X_e,t | F_t] = A_e,t + sum_{unknown c} s_e(c)*y[c] = T_e.
```

The equality holds for every fixed score matrix, even when previously
observed outcomes changed the next probability. It also holds when the cell
is useful for several edges, or belongs to no particular active edge.

Predictable bounds are

```text
L_e,t = A_e,t - max_{unknown cells of b} 1/p_t(c)
U_e,t = A_e,t + max_{unknown cells of a} 1/p_t(c)
```

with a maximum of zero over an empty set. For `rho` in the fixed grid
`{.02,.05,.10,.20,.40,.80}`, use stakes
`lambda+ = rho/max(1,-L_e,t)` and
`lambda- = rho/max(1,U_e,t)`. Every factor
`1+lambda+*X_e,t` and `1-lambda-*X_e,t` is at least `1-rho>0`.
Under `T_e <= 0`, the first factor has conditional expectation at most one;
under `T_e >= 0`, the second does too. Their products are one-sided test
supermartingales; a fixed, equally weighted mixture of the six products is
also a test supermartingale. Retire an edge on crossing `2*|E|/alpha` in the
corresponding direction. Ville's inequality and a union bound give
`P(any wrong reported sign) <= alpha`, including outcome-adaptive acquisition
and stopping. The proof does not assume independent scores across systems.

The deterministic full-pool interval
`[A_e,t - n_b_unknown, A_e,t + n_a_unknown]` can also certify a sign without
error; at full exposure the exact sign, including a tie, takes priority.

This construction applies established importance weighting and betting to
individual cells. The per-edge union bound is **not** the sought joint
certificate. The proof concerns the specified fixed finite matrix and
randomized purchase mechanism, not judgments from future human raters.

## Small sanity gate

`cell_probe.py` independently checks the conditional moment, both betting
factors, and one-step supermartingale inequality over **7,680** states:
every binary `3 x 2` matrix, every exposure mask with an unresolved edge,
and both reference-star edges, with nonuniform probabilities determined by
known scores. This is an implementation sanity check, not a proof of the
entire sequential procedure; the conditional argument above is the proof.

The exploratory simulation uses `S=5`, `N=128`, a four-edge star, `alpha=.05`,
and 30 independently generated fixed matrices per scenario. Both methods
receive the same matrix. Stage 22 uses its frozen `make_paths` and
`simulate_graph` code with a common uniform item order; this probe buys
individual cells uniformly among unresolved-edge endpoints. Both retire
edges at `2*|E|/alpha`, count each purchased cell once, and complete every
requested edge. Their acquisition randomizations are independent, so these
are paired **matrices**, not matched query streams.

| Synthetic scenario | Stage 22 mean cells | Cell rule mean cells | Cell rule extra cost |
| --- | ---: | ---: | ---: |
| Easy, independent binary scores | 133.67 | 239.80 | 79.40% |
| Weak, independent binary scores | 473.37 | 529.27 | 11.81% |
| Easy, shared latent uniform score | 115.63 | 239.30 | 106.95% |

No wrong sign was observed in these 90 completed diagnostic runs. That count
does not establish worst-case error. This result rejects **this uniform
individual-cell rule** as an efficiency improvement; it does not rule out
other cell policies or stronger evidence constructions. The scenarios and
policy were explored here, so these numbers are not external confirmation.

Reproduce from the repository root with NumPy:

```bash
python experiments/cell_level_gate/cell_probe.py
```

## Decision for the next method

Before another WMT result, specify a genuinely joint finite-pool evidence
construction or a materially better acquisition policy, then prove validity
under adaptive cell purchase. Compare it to Stage 22 **and this cell
baseline** under the same requested edges, family error, item pool, and
unique-label accounting. Check hard ties, adversarial system correlation,
bad historical predictions, and completed conclusions. Read the theorem and
action spaces of [active testing](https://proceedings.mlr.press/v139/kossen21a.html),
[finite-population active querying](https://arxiv.org/abs/2601.20251),
[AnyRank](https://arxiv.org/abs/2610.14603), and
[rank confidence sequences](https://arxiv.org/abs/2609.32211) before calling
any such combination novel.

If the theorem is a direct composition of prior work, or matched completed
cost does not improve, stop this line. WMT24 remains reserved for a method
that passes the proof and synthetic baseline gates.
