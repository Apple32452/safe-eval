# Stage 18 frozen protocol: common random test-set baseline

## Question

Does annotation-level frontier scheduling certify more correct fixed-benchmark
system comparisons than evaluating every system on the same smaller random test
set, at the same unique system-item label budget?

This comparison repairs the blocking Stage 17 baseline. It is frozen before
computing the common-test-set result. WMT25 remains development data. WMT24
outcomes remain untouched and are reserved for later confirmation only if this
stage passes.

## Data and estimand

- Use the 14 WMT25 continuous-score matrices frozen in Stage 17, with identical
  systems, common items, source hash, and matrix hashes.
- A label is one recorded mean human score for one system-item cell.
- For each system pair, estimate the sign of its fixed-pool mean score
  difference. Ties have truth sign zero and cannot be declared by a one-sided
  certificate before exact full evaluation.
- Use the unchanged Stage 17 continuous finite-population e-process, six-way
  betting mixture, family threshold `40 * number_of_pairs`, and exact full-pool
  decision.

## Frozen candidate

Use the archived Stage 17 `frontier_evidence` rows without rerunning or changing
the method. Its independent uniform item path for every pair, evidence cap,
tie-breaking priorities, master seed 20261024, 50 repeats, and 25%, 50%, and
75% checkpoints remain exactly as recorded in the Stage 17 reference package.

## Common random test-set control

For each language and repeat:

1. Draw one uniform permutation of common items with the frozen Stage 18 master
   seed 20261025 and the namespace `common_item_order`.
2. For every item in that order, draw a uniform system order with namespace
   `common_system_order`. Acquire all system labels in that order before moving
   to the next item. This defines partial-item behavior at an exact label
   budget without favoring a fixed system.
3. Feed each system pair's completed differences to the unchanged Stage 17
   e-process in the common item order. A pair may resolve as soon as either
   direction crosses its family threshold.
4. Save results after `floor(fraction * systems * items)` unique labels for
   fractions 0.25, 0.50, and 0.75. Do not replace early declarations.

The control's shared item order is uniform without replacement for every pair.
Dependence between pairs is permitted by the scheduler-independent family
validity argument. Unique system-item labels are charged once.

## Repeats and reporting

- Run 50 repeats for every included language.
- Report the total number of correct, wrong, and unresolved pair conclusions
  at every checkpoint.
- Compare the archived candidate and new control by repeat index. The two
  randomized designs use distinct frozen random streams; the conditional
  Monte Carlo standard error is computed from the 50 differences.
- Report wins, ties, losses, relative gain over the control, and mean
  differences for every language.

## Primary gate

At the 75% unique-label budget, Stage 18 passes only if all conditions hold:

1. the candidate has a positive mean gain over the common-test-set control;
2. the gain is greater than two conditional Monte Carlo standard errors;
3. more than half of the 14 language-level mean gains are positive; and
4. the candidate has no more observed wrong declarations than the control.

The gate is evaluated once. A failed gate will be reported as a failed
candidate rather than followed by scheduler or threshold tuning on WMT25.

## Integrity and claim boundary

- The protocol, implementation, tests, and hashes must be committed before the
  50-repeat baseline is computed.
- A one-repeat software check may be run first and cannot alter the protocol.
- The final audit must verify the implementation lock, Stage 17 reference
  hashes, complete grid, budget accounting, monotonicity, unique labels, and an
  exact repeat-zero replay.
- Passing this development gate would justify a frozen WMT24 confirmation and
  comparison to direct pair-feedback methods. It would not alone establish an
  ICML contribution.
