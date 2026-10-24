# When can all panel outcomes be reused without changing the target?

## Setup and statement

Fix a finite collection of eligible panels `P` and a requested graph `E`.
Every panel contains at least one requested edge; each requested edge
appears in at least one panel. A fresh ranking of panel `S` supplies a
bounded signed outcome for each `e subset S`, with possibly arbitrary
panel-dependent mean `mu_e(S)`. For edge `e`, let `P_e={S in P:e subset S}`
and predeclare the uniform-companion estimand

```text
theta_e = (1/|P_e|) * sum_{S in P_e} mu_e(S).
```

At a given pre-judgment history choose `S` with predictable probability
`Q(S)>0` for every eligible panel. If an edge appears, an **unweighted**
pairwise update has mean

```text
E[Y_e(S) | e appears, history]
  = sum_{S in P_e} Q(S) mu_e(S) / sum_{T in P_e} Q(T).
```

This equals `theta_e` for **every** array of context-dependent means in
`[-1,1]` if and only if `Q(S)` is equal for all panels `S` containing `e`.
For the entire graph, connect two eligible panels when they both contain
some same edge from `E`. The equality holds for all requested edges if
and only if `Q` is constant on each connected component of this panel
graph. Probabilities can vary across components; within a connected panel
graph the only solution is uniform panel selection.

For the complete `K`-system comparison graph and **all** `k`-system panels
with `K>=k>=3`, the panel graph is connected. Any two panels differing in
one system share `k-1>=2` systems and therefore a requested edge; all
`k`-system panels are linked by such swaps. Thus an outcome-adaptive panel
policy cannot both (i) update **every** included comparison from raw
unweighted outcomes and (ii) preserve **all** uniform-companion targets
for arbitrary context effects unless it remains uniform at every history.

## Proof and limits

Sufficiency for one edge follows by substituting the uniform conditional
panel probabilities `Q(S)/sum_{T in P_e}Q(T)=1/|P_e|`. Necessity follows
by setting its mean to one on just one panel and zero on the others:
the observed and target means then equal the corresponding two weights.
Repeat this basis-vector argument for each eligible panel and pair.
The equality forces the weights of any panels sharing a requested edge to
match, hence equality propagates along connected paths. Conversely, all
panels containing a fixed requested edge form a clique, so constancy on
components makes that edge's conditional distribution uniform. The
complete-graph conclusion follows from connectivity above. All statements
apply conditionally at each history; predictive adaptivity does not bypass
the algebra.

This is an **identifiability and design constraint**, not a new anytime
inference theorem. It is limited to raw updates, the specified uniform
companion targets, positive panel support, and arbitrary context effects.
It does not prohibit adaptive selection of items, stopping, an inference
procedure using logged propensity weights, or a focal-edge policy that
randomizes companions for that edge and discards or corrects byproducts.
If pair preferences truly do not depend on the companion panel, every
`mu_e(S)` is constant in `S` and the raw conditional mean is invariant to
`Q`, so the premise requiring equality for *every* mean array matters.

## Exact counterexample and sparse exception

With six systems and all five-system panels, upweight one panel by a factor
of two and give all other panels weight one. Pair `(0,1)` occurs in four
panels. If its mean is `1` in the upweighted panel and `0` (a tie) in the
other three, its target is `1/4=.25`; the raw conditional mean under the
selected panel is `2/(2+3)=.40`. Its bias is `.15`. These means are
realizable by five-way rankings that tie or order the same pair depending
on the companions. With six systems, three-system panels, and only two
disjoint requested edges `(0,1)` and `(4,5)`, the eligible panel graph has
two four-panel components. We may increase the mass on one component
while remaining uniform within each and preserve both targets.

## Novelty boundary

The proof is elementary probability and graph connectivity. It gives a
precise warning for the Stage 31 five-way policy under the context effects
raised in [Koehn (2012)](https://aclanthology.org/2012.iwslt-papers.5.pdf)
and Stage 32. [Saha and Gopalan (2019)](https://proceedings.mlr.press/v89/saha19a.html)
study adaptive subset-wise feedback under a Plackett--Luce model, whose
preference semantics differ from our arbitrary panel-dependent mean target.
Standard inverse-propensity weighting can correct a changed design, so
this graph-specific characterization alone is **not** an established ICML
novelty. A paper would need a valid and efficient corrective acquisition
rule plus a matched measured-human-cost gain, with a deeper source-level
originality audit.
