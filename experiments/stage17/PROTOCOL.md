# Stage 17 development protocol: anytime shared-label allocation

## Contribution question

Can one human score for a single system-item output be allocated and reused
across many simultaneous pairwise system comparisons while retaining an
anytime-valid family guarantee and certifying more complete-benchmark
conclusions than matched active controls at the same unique-score budget?

Stage 17 is a development study on the WMT25 file already used in Stage 16.
It cannot be external confirmation. It changes the outcome from the strict
binary proxy to the mean recorded 0--100 human score, and it freezes all rules
before that continuous-score comparison is summarized. WMT24 human outcomes
must not be downloaded or inspected while developing this method.

## Fixed population and conclusions

Use the exact Stage 16 source hash, reference filter, maximum-coverage system
rule, common-item intersection, and 14 included language directions. For each
retained system-item, take the arithmetic mean of its nonempty annotation
scores and divide by 100. Every score must be finite in [0,100].

For every unordered system pair, the complete-benchmark conclusion is the sign
of the mean paired score difference. Exact ties are a third conclusion. Use
all pairs, including close pairs. No full mean, gap, or final sign may enter an
acquisition policy.

For each pair and repeat, precommit an independent uniform permutation of its
common item pool using NumPy PCG64 and SHA256-derived seeds. Use 50 matched
repeat blocks and master seed 20261024. A queried `(system,item)` score costs
one label and is reusable across every pair in that language. Free pair
prefixes close immediately after every paid label.

## Continuous anytime-valid evidence

For a pair difference `d` in [-1,1], test each directional null mean at zero
with a finite-population betting mixture. Before the next uniform draw, with
`r` items remaining and observed directional sum `s`, the boundary-null
conditional center is `c=-s/r`. For fixed fractions

    rho in {0.02, 0.05, 0.10, 0.20, 0.40, 0.80},

use the predictable factor

    1 + rho * (d-c)/(1+c)

when `c>-1`; use factor one when `c<=-1`, where the deterministic finite-pool
bound handles boundary-null impossibility. Apply the same construction to
`-d` for the reverse direction. Average the six component wealths. This is a
fixed mixture, not a tuned grid. Stop a direction when its mixture reaches
`40*K`, where K is the number of pairs in that language. Also stop when the
remaining [-1,1] range makes the full-mean sign deterministic. At full budget,
return the exact sign.

The threshold allocates 0.05/(2K) to each directional process, giving nominal
95% family control separately within each language and policy. Every saved
wrong declaration remains reported.

## Frozen policies

Use checkpoints floor(25%,50%,75%) of all unique system-item scores and the
following six policies:

1. `uniform_labels`: take the next unseen unique label in a precommitted
   uniform random order and close all newly available pair prefixes.
2. `round_robin`: cycle over unresolved pairs, acquiring their first missing
   frontier label.
3. `focus_random`: finish pairs in a precommitted outcome-independent random
   order.
4. `evidence_first`: choose the pair with greatest current capped directional
   mixture evidence, then its first missing frontier label.
5. `frontier_count`: choose the unseen label occurring in the greatest number
   of current unresolved pair frontiers.
6. `frontier_evidence`: choose label `l` maximizing

       U(l) = sum_{p: l in M_p} [1 + min(E_p, 40*K)],

   where `M_p` is the set of missing labels at pair p's current frontier and
   `E_p` is its greatest current directional mixture evidence.

All ties use precommitted outcome-independent priorities. No automatic metric,
embedding, historical outcome, coefficient, temperature, lookahead, pair
filter, or post-result policy change is allowed in Stage 17.

## Development gate

The primary checkpoint is 75% unique labels. Sum correct conclusions across
the 14 languages within each repeat. `frontier_evidence` must have a positive
mean difference against both `evidence_first` and `uniform_labels`, positive
per-language means over `evidence_first` in a strict majority of languages,
and no observed wrong-declaration excess over either comparator. Report all
50 paired differences, conditional Monte Carlo standard errors, and every
25% and 50% result.

Passing supports the combined problem/method claim but does not complete the
paper. Before an ICML claim, implement faithful comparisons to direct-pair
Active Evaluation/DiffUse-style methods under an explicit cost conversion,
and freeze an outcome-untouched WMT24 confirmation. Failure ends the exact
frontier-evidence rule on this continuous target; do not retune it on WMT25.
