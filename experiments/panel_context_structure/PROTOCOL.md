# Panel-context compatibility theorem: research protocol

Frozen 2026-10-24 before implementation and enumeration. This is a
mathematical diagnostic, not an ICML novelty or empirical label-saving claim.

## Problem

Fix `K` systems, a collection `P` of allowed panels (subsets of systems),
and a requested pair graph `E`. Only panels containing at least one edge in
`E` are eligible. A fresh input/judge ranking from panel `S` gives a
bounded pair preference `Y_e(S)` for each `e subset S`. Its conditional
mean `mu_e(S)` may vary arbitrarily with the other systems in the panel.
For each edge `e`, define the target as the **uniform average over all
eligible panels containing e**:

```text
theta_e = (1/d_e) * sum_{S in P: e subset S} mu_e(S),
d_e = number of eligible panels containing e.
```

A policy chooses a panel with strictly positive predictable probability
`Q_t(S)` for every eligible panel, possibly depending on previous judgments.
It updates each included pair using its raw, unweighted preference. Ask
when the conditional mean of that raw update is `theta_e` for **every**
possible set of context-specific means `mu_e(S)` and every requested edge.

## Exact characterization to prove and enumerate

The necessary and sufficient condition at each history is
`Q_t(S)/p_e = 1/d_e` for every `S` containing `e`, where
`p_e = sum_{S contains e} Q_t(S)`. Build a graph whose vertices are eligible
panels, with an edge when two panels share a requested system pair.
Conditioning compatibility holds if and only if `Q_t` is constant within
each connected component. The probability mass may be moved between
components, while a connected panel graph forces uniform selection over
all eligible panels.

For all `k`-system subsets of `K>=k` systems, complete requested pair graph,
and `k>=3`, neighboring panels in the Johnson graph share `k-1>=2`
systems, hence a requested pair. The panel graph is connected. Thus the
only policy using *all* included raw pair outcomes and keeping every
edge's uniform-context target under arbitrary context effects chooses
panels uniformly at every history. Adaptive stopping is still permitted.

The theorem concerns raw unweighted reuse, uniform conditional context
targets and arbitrary panel effects. Inverse propensity correction,
focal-edge selection with separate target-context randomization, a different
estimand, or context-invariant preferences can evade its conclusion. A
separate inference proof is needed for any new method based on them.

## Audit

Enumerate all nonempty requested graphs on four systems with three-way
panels, all positive integer panel weights 1..3, and check both directions
of the component characterization against the direct conditional
distribution equality. Check a connected five-way complete-graph example,
a disconnected sparse-graph exception, and an explicit context-effect
witness where nonuniform panel selection changes a raw edge mean. Record
the counts and the limits of the result. Do not use WMT24 or any new
human judgments.
