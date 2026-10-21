# Stage 21 conditional validity and closure

## Pilot selection

The pilot is a uniform prefix of the fixed finite item pool. Conditional on its
observed scores, the selected chain is fixed and the remaining item order is a
uniform permutation of the remaining fixed items. Selection may depend
arbitrarily on the pilot because no post-pilot evidence was used to choose the
tested edges.

## Shifted remaining-pool null

For one selected orientation, write the full difference total as `s + R`, where
`s` is the known pilot sum and `R` is the remaining total. The full-pool null is
`s + R <= 0`, equivalently `R <= -s`. After observing remaining-prefix sum
`u_t`, the boundary conditional mean for the next difference is

`c_t = (-s - u_t) / (m-t)`.

For bounded differences in `[-1,1]`, each Stage 17 factor

`1 + rho * (X_{t+1} - c_t) / (1 + c_t)`

has conditional expectation at most one at the boundary and is nonnegative for
`0 < rho < 1`. If `c_t < -1`, the null is already deterministically impossible;
if `c_t >= 1`, it imposes no useful positive-direction restriction and the
factor cannot grow. Reverse the differences and pilot sum for the other
orientation. Mixtures preserve validity.

Conditional on every pilot realization, a union bound over two directions for
`S-1` selected edges at threshold `40(S-1)` is at most 0.05. Averaging over the
pilot retains the same unconditional family bound.

## Transitive closure

On the event that every declared base edge has the correct full-pool
orientation, every directed path follows strictly decreasing full score.
Therefore each reachability conclusion is correct. A wrong closure conclusion
requires at least one wrong base edge, so closure adds no family error.

The method can certify all pair relations from only `S-1` base declarations
when every adjacent edge in the proposed order is certified. Pilot inversions
or difficult adjacent gaps break the chain into shorter certified segments;
the experiment measures that tradeoff without using full outcomes in selection.
