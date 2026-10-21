# Stage 22 requested-graph dominance

Fix a finite item pool, a common item order, a within-item system order, a
requested comparison graph \(G=(V,E)\), and irreversible edge declarations.
The common control scores every system on every item until all requested edges
resolve. The graph-pruned method scores only vertices incident to an unresolved
requested edge at the start of an item.

## Taskwise validity

Every unresolved edge receives both endpoint scores on the next common item.
Its observed differences are therefore a prefix of its precommitted uniform
without-replacement path. The Stage 17 anytime bound applies to every prefix,
and a union bound over the requested edge set gives taskwise family control.
The active vertex set is measurable with respect to completed earlier items
and is committed before any current-item outcome is revealed.

## Per-edge pathwise dominance

Consider an unresolved edge at the start of item \(j\). Both endpoints belong
to the graph-pruned active set, so the edge receives the same \(j\)-th paired
difference as the common control. Before those endpoints, graph pruning has
acquired a subsequence of the common control's labels: it removes inactive
vertices while retaining the common within-item order. Thus an unresolved edge
reaches every certificate prefix at no greater cumulative label cost. Once an
edge resolves, later labels cannot alter its frozen declaration.

Induction over common items yields, for every fixed outcome path and every
requested edge,

\[
  C^{\mathrm{pruned}}_e \le C^{\mathrm{common}}_e,
\]

where \(C_e\) is the cumulative system-item label cost at first declaration.
Consequently, total cost to resolve the requested graph is no larger under
pruning, and the pruned resolved-edge set contains the control set at every
label budget.

## Exact savings identity

If \(U_j\) is the unresolved edge set when item \(j\) is committed, the pruned
item cost is the number of incident vertices \(|V(U_j)|\), compared with
\(|V|\) for a complete common block. Before the final possibly partial block,
the skipped cost is therefore

\[
  \sum_j \bigl(|V|-|V(U_j)|\bigr).
\]

This identity explains the Stage 20 complete-graph result and the Stage 22
hypothesis. A complete graph usually retains nearly every vertex while any
edge remains unresolved. In a reference star, each nonreference vertex has one
requested edge and can leave immediately after that edge resolves.

The theorem supplies safety and dominance, not empirical materiality or
novelty relative to all model-racing literature. Those are separate Stage 22
and related-work questions.
