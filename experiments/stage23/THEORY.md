# Synchronous shared-label minimality

Fix a finite score matrix, a requested comparison graph, one common uniform
without-replacement item order, and a precommitted within-item system order.
An edge is unresolved until its irreversible sequential certificate fires.

## Policy class

A synchronous prefix-preserving policy advances every unresolved edge by the
next observation on the same common item. It commits its queried systems before
revealing any score on that item. Labels are system-item scores and are charged
once. The policy may stop inside its last full-system block after every
requested edge resolves.

This class contains the common-prefix control and Stage 22 pruning. It excludes
asynchronous edge racing, outcome-dependent item selection, parametric ranking,
and i.i.d. policy-allocation methods.

## Itemwise lower bound

Let `U_j` be the unresolved requested edges before common item `j`, and let
`V(U_j)` be their incident vertices. To give every edge in `U_j` its next
paired observation, a policy must reveal the current-item score at both of the
edge's endpoints. Taking the union over edges, every vertex in `V(U_j)` is
necessary. Querying exactly `V(U_j)` is sufficient.

Therefore `|V(U_j)|` is the unique minimum number of system labels that can
advance every unresolved edge on that item. Stage 22 attains this lower bound.

## Pathwise dominance

The pruned within-item order is the common order restricted to `V(U_j)`. For
any edge still unresolved at the start of item `j`, both endpoints appear in
both orders and its paired score difference is identical. Before either
endpoint, pruning has only removed labels not in `V(U_j)`. Thus the cumulative
label position at which the edge receives its `j`-th difference is no later
under pruning.

Induction over common items gives, for every fixed outcome path and requested
edge `e`,

\[
  C_e^{\mathrm{pruned}} \leq C_e^{\mathrm{common}},
\]

where `C_e` is cumulative unique-label cost at first declaration. The same
argument handles the final partial common block: pruning removes nonincident
systems while retaining the relative endpoint order, so the last required
endpoint is no later. Total requested-graph completion cost is consequently no
larger.

## Statistical validity

Each edge sees exactly the same uniform without-replacement prefix that it
would see under the common control. The Stage 17 finite-population e-process is
therefore unchanged edge by edge. A union bound over the predeclared requested
edges gives the same taskwise family guarantee. The pruning decision depends
only on completed earlier items, so current-item outcomes cannot change their
own acquisition set.

## What is and is not optimal

The rule is label-minimal only inside the synchronous prefix-preserving class.
It need not minimize expected labels among all valid procedures. Another
method may target an i.i.d. population mean, advance selected edges on separate
item paths, assume a parametric model, use an indifference zone, recycle error
budgets, or infer relations by transitivity. Those methods change the estimand,
policy class, guarantee, or all three.

The independent `audit_stage23.py` enumerates every nonempty graph on up to
four vertices, every within-item system order, every assignment of edge
resolution times in the first three rounds, and every queried vertex subset
for the itemwise lower bound. It does not import the Stage 22 scheduler.

