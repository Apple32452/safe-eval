# Stage 20 pathwise label-cost dominance

Fix an item order, a within-item system order, pairwise decision paths, and
irreversible declarations. The common control scores all `S` systems on every
item. The pruning policy scores exactly the systems incident to an unresolved
pair at the start of an item.

## Validity

Every unresolved pair has both endpoints in the committed active set, so it
observes the next item in the same common order. Its observed differences are
therefore a prefix of its precommitted uniform without-replacement path. The
Stage 17 per-pair anytime bound and union bound continue to control the family
event. The active-set decision uses only previous items, and the full active set
is committed before any current-item score is observed.

## Dominance theorem

At the start of item `j`, every pair unresolved under pruning has received the
same first `j-1` pair differences as under the common control. Its endpoints
are both active and receive item `j`. A pair that has resolved under pruning
needs no later label. Thus pruning reproduces every label relevant to an
unresolved decision and omits only labels whose incident pairs are all frozen.

For each completed item, pruning spends at most the `S` labels spent by the
control. Within an item, its system order is the control order restricted to
the active set, so every relevant endpoint appears no later in cumulative label
cost. Induction over item blocks gives:

> For every fixed path and every label budget, each pair prefix reached by the
> common control has either already resolved under pruning or is reached no
> later under pruning.

Consequently, the pruning policy's resolved-pair set contains the control's at
every label budget. The statement is pathwise and makes no distributional or
effect-size assumption. It does not say that extra earlier declarations are
correct; correctness is supplied by the common family-valid certificate.

The gain can be zero when every system remains incident to an unresolved edge.
The experiment measures whether the theorem produces material savings on real
multi-system evaluation graphs.
