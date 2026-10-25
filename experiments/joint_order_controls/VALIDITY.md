# Conditional validity of the additional controls

The estimand is the sign of each requested pair's mean difference on the
same fixed 3-by-N binary matrix. There is no population-of-new-items or
new-raters guarantee. Alpha=.05 bounds the probability of any incorrect
requested sign over all looks within one fixed graph task. It does not
bound the probability of any error over every simulated matrix in the study.

## Rebalanced pair factors

Fix the actual weak ordering W*. Every directional null implied by W* is
true. Each original exact pair factor has conditional expectation at most
one under its pair null in the full adaptive-cell filtration. A convex
combination, whose nonnegative weights sum to one and are fixed before the
next outcome, also has conditional expectation at most one under W*.
Including the unit factor preserves this property. Its time product is a
nonnegative supermartingale starting at one, regardless of optimizer success.

Ville's inequality bounds rejection of W* at 1/alpha by alpha. If W* is
still among surviving orders, agreement of every survivor on a strict sign
cannot be wrong. Logical remaining-total bounds have zero error. An empty
survivor set licenses no statistical decision. Exact ties need both
endpoint totals. This proves simultaneous anytime correctness of the new
cell control under the original uniform-within-row purchase rule.

## Common-item exact paired differences

The item permutation is uniformly randomized in advance and is not selected
using unseen outcomes. Factors and retirement decisions use only earlier
purchased scores, not the future part of that permutation. At a round when
pair (a,b) remains unresolved, both endpoints have been purchased on every
previous common item. Conditional on this past, the next item is uniform
among the m remaining items. Its difference has probabilities
`(c-,c0,c+)/m` for the actual remaining difference histogram. These statements
hold for an arbitrary fixed matrix and arbitrary cross-system dependence.

Under the directional null, the actual histogram satisfies
`d+c+-c- <= 0`. The optimized factor is checked against every integer
histogram satisfying that inequality. It therefore has conditional
expectation at most one under that null. Its predictive categorical model
need not be correct. Feasibility, not an accurate optimizer or prior, is
what supplies validity. When an edge resolves, freezing each directional
wealth is optional stopping and preserves the supermartingale property.

For the closure control, the fixed average of current wealths whose nulls
are implied by W* is a supermartingale under W*. The preceding W* retention
argument applies. For Bonferroni, each of the 2|E| directional tests has
threshold 2|E|/alpha; a union bound gives the same taskwise error bound.
Opposing simultaneous crossings abstain, and exact logical rules remain safe.

Within a round, all active cells are bought before any factors are updated.
Once a system has no incident unresolved requested comparison, it is retired
permanently. The actual ledger charges every active system-item cell once.
No post-hoc reduction in paid cost uses a score that was never purchased.

These are applications of established conditional e-process, optional
stopping, and order-closure principles. They do not supply a new label-cost
bound or an originality result.
