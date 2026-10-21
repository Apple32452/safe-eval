# Stage 21 frozen protocol: pilot-selected chain certification

## Candidate contribution

Stage 21 tests a different route to preserving fixed-benchmark conclusions.
Instead of directly testing every system pair, use a disjoint pilot prefix to
propose a total system order, certify only the adjacent relations on the
remaining finite pool, and infer nonadjacent relations by transitivity.

The protocol is frozen before implementation or candidate computation. WMT25
is development data. WMT24 outcomes remain untouched.

## Data and common stream

- Use the same 14 WMT25 continuous-score matrices, 50 repeats, common item
  permutations, within-item system orders, and checkpoints as Stage 18.
- A label is one system-item mean human score. Every system is scored on the
  same growing common item set.
- The pilot contains the first `floor(number_of_items / 4)` complete items.
  Its labels count toward the 25%, 50%, and 75% total budgets.

## Pilot-selected chain

At the end of the complete pilot:

1. rank systems by decreasing pilot score sum, breaking exact ties by system
   name;
2. select the `S-1` adjacent ordered pairs in that ranking; and
3. freeze this chain before revealing any score from later items.

Changing any post-pilot score must not change the selected chain.

## Conditional finite-population tests

For a selected ordered edge `(a,b)`, let `s` be its observed pilot difference
sum and let the remaining pool have size `m`. The null that the full-pool
difference is nonpositive implies that the remaining difference total is at
most `-s`. Test this conditional finite-population null on the remaining common
item order. Test the reverse direction symmetrically.

Use the unchanged Stage 17 six betting fractions. At every step, center each
bet at the boundary conditional mean of the still-unseen remainder. Use family
threshold `40 * (S-1)`, which gives a union bound over both directions of the
conditionally selected chain. Use deterministic finite-population bounds and
the exact full-pool sign at the final item.

The primary method is `selected_chain`. An ablation
`selected_chain_allpair_threshold` uses the identical pilot, edges, labels, and
closure but threshold `40 * S(S-1)/2`. It measures the benefit of reducing the
tested family rather than changing acquisition or the proposed order.

## Transitive conclusions

Freeze each adjacent declaration when first made. At every checkpoint, form a
directed graph from declared chain edges and compute its transitive closure. A
reachable ordered pair is a certified conclusion. Compare the closure to the
full fixed-pool score order only for evaluation; full outcomes are unavailable
to the algorithm.

A wrong closure conclusion implies at least one wrong declared chain edge.
Thus conditional family validity for the selected edges also controls every
conclusion produced by closure.

## Baseline, reporting, and gate

Compare to the archived Stage 18 all-pair `common_random_items` result at the
same language/repeat/label-budget keys. Report:

- correct, wrong, and unresolved conclusions over all `S(S-1)/2` pairs;
- directly declared chain edges and closure-added conclusions;
- complete-ranking certification frequency;
- paired gains, MCSE, wins/ties/losses, relative gain, and language means; and
- the all-pair-threshold ablation.

At 75% labels, the development gate passes only if `selected_chain`:

1. has a positive mean gain in correct all-pair conclusions over Stage 18;
2. exceeds two conditional Monte Carlo standard errors;
3. has positive mean gain in more than half of the 14 languages; and
4. has no more observed wrong conclusions than Stage 18.

The gate is evaluated once. No pilot fraction, threshold, ordering rule, or
closure rule will be tuned on WMT25 after the result.

## Integrity and claim boundary

- Commit this protocol before implementation and execution.
- Commit code, tests, proof record, and hashes before the smoke or full run.
- Exhaustively test the conditional e-process on small finite null populations.
- Audit source and matrix hashes, the Stage 18 reference, the selected chain's
  pilot-only dependence, grid and budget accounting, closure accounting, and an
  exact repeat-zero replay.
- Passing would produce a stronger development candidate. WMT24 external
  validation and direct comparison with recent adaptive ranking and sequential
  model-confidence-set methods would still be required for an ICML claim.
