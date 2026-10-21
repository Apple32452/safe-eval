# Stage 19 frozen protocol: common-core adaptive tail

## Candidate contribution

Stage 18 rejected separate pair-path frontier scheduling because it discarded
the powerful reuse of a common test set. Stage 19 tests one principled repair:
evaluate every system on a shared random core, then allocate only the remaining
labels to unresolved comparison frontiers.

The candidate is fixed before implementation or outcome computation. WMT25 is
development data. WMT24 outcomes remain untouched and are reserved for a later
external confirmation only if the development gate passes.

## Data, estimand, and inference

- Use the exact 14 WMT25 continuous-score matrices frozen in Stages 17 and 18.
- A label is one recorded mean score for one system-item cell.
- Infer the sign of every fixed-pool pairwise mean difference.
- Use the unchanged Stage 17 continuous finite-population e-process, six-way
  betting mixture, family threshold `40 * number_of_pairs`, and exact full-pool
  decision.
- Charge each unique system-item label once and save results at 25%, 50%, and
  75% of all available labels.

## Paired common core

For each language and repeat, use the exact Stage 18 common item order and
within-item system orders: master seed 20261025 with namespaces
`common_item_order` and `common_system_order`.

The complete common core is the first `floor(number_of_items / 2)` items. The
candidate first acquires every system label for these items in the Stage 18
order. Thus the 25% checkpoint is pathwise identical to the Stage 18 common
control, and the 50% checkpoint is identical whenever the number of items is
even. For an odd item count, the small budget remainder after the complete core
begins the adaptive tail.

## Precommitted pair paths

For each pair, append an independent uniform permutation of the items outside
the common core. Use master seed 20261026 with the language, ordered system
names, repeat, and namespace `pair_suffix`. The common prefix followed by this
conditional suffix is a marginal uniform permutation of the complete item pool
for every pair.

Compute the complete pair e-process paths offline. The acquisition policy may
read only each pair's currently revealed prefix and its current capped evidence.

## Adaptive tail

After the common core, repeatedly:

1. identify each unresolved pair's next required suffix item;
2. give that frontier weight `1 + min(current_evidence, family_threshold)`,
   using zero evidence before any observation;
3. assign every unseen system-item label the sum of weights for unresolved
   frontiers it advances;
4. acquire a maximum-utility label, breaking ties by one deterministic uniform
   priority over labels generated from master seed 20261026; and
5. close every pair frontier made complete by that label before scheduling the
   next label.

This is the unchanged Stage 17 `frontier_evidence` utility applied only after
the common core. No core fraction, evidence cap, mixture, threshold, or
tie-break rule will be tuned after the result.

## Frozen comparison and gate

Run 50 repeats. Compare the candidate to the archived Stage 18
`common_random_items` control by the paired language/repeat/checkpoint key.

At 75% labels, the development gate passes only if:

1. the candidate's mean gain in correct conclusions is positive;
2. the gain exceeds two conditional Monte Carlo standard errors;
3. more than half of the 14 language-level mean gains are positive; and
4. the candidate has no more observed wrong declarations than the control.

Report all checkpoint means, relative gain, wins/ties/losses, language means,
and wrong conclusions. A failed gate rejects this common-core candidate. There
will be no further WMT25 core-fraction or utility search.

## Integrity and claim boundary

- Commit this protocol before implementing or running the candidate.
- Commit the implementation, invariant tests, and hash lock before a one-repeat
  smoke run or the full experiment.
- Audit the exact Stage 18 reference, source and matrix hashes, complete result
  grid, budgets, monotonicity, unique-label invariants, and repeat-zero replay.
- Passing would establish a development candidate, not a completed ICML claim.
  It would trigger a frozen WMT24 external validation and direct comparison to
  the closest active-evaluation acquisition baselines.
