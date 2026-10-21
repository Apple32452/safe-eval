# Stage 20 frozen protocol: active-system pruning on a common test stream

## Narrow candidate contribution

Sequential model evaluation, pairwise stopping, ranking, and active test-point
selection already exist. Stage 20 therefore tests a narrower structural claim:
for simultaneous fixed-benchmark pair certification, stop scoring a system on
future common items once every requested comparison incident to that system is
already certified. This preserves the common-test-set reuse exposed by Stage 18
and skips only labels that cannot change any unresolved conclusion.

The method and gate are frozen before implementation and outcome computation.
WMT25 remains development data. WMT24 remains untouched.

## Data and certificate

- Use the exact 14 WMT25 continuous-score matrices and 50 Stage 18 repeat
  streams.
- Use the same item permutation and within-item system order as Stage 18:
  master 20261025 and namespaces `common_item_order` and
  `common_system_order`.
- Use the unchanged Stage 17 continuous finite-population e-process, six-way
  mixture, family threshold `40 * number_of_pairs`, and exact full-pool rule.
- Freeze every declaration when first made. Charge every acquired system-item
  score once.

## Candidate policy

At the start of each new item in the Stage 18 common order:

1. form the unresolved comparison graph;
2. mark a system active if it is an endpoint of at least one unresolved edge;
3. commit to scoring every active system on this item, in the Stage 18 system
   order restricted to the active set;
4. complete that committed item block even if declarations occur within it;
5. update every completed pair prefix and its certificate; and
6. repeat on the next common item until the next label-budget checkpoint or
   until no unresolved edges remain.

The active set is chosen before any score on the current item is revealed.
Resolved systems can never reactivate because declarations are irreversible.
Save snapshots after 25%, 50%, and 75% of the full system-item label budget.

## Frozen control and pathwise audit

Compare to the archived Stage 18 `common_random_items` rows using the identical
language, repeat, pair paths, item orders, system orders, certificate, and label
budgets. For every saved language/repeat/checkpoint, require the candidate to
have at least as many resolved pair conclusions as the control. Any violation
is an implementation or theorem failure.

## Development gate

At 75% labels, the gate passes only if:

1. the mean gain in correct conclusions is positive;
2. the gain exceeds two conditional Monte Carlo standard errors;
3. more than half of the 14 language-level mean gains are positive;
4. the candidate has no more observed wrong declarations than the control; and
5. pathwise resolved-pair dominance holds at every saved checkpoint.

Report correct, wrong, and unresolved pairs; labels actually acquired; paired
wins/ties/losses; relative gain; and language means. A failed gate ends this
acquisition line on WMT25.

## Integrity and claim boundary

- Commit this protocol before implementation or execution.
- Commit implementation, tests, the proof record, and hashes before a smoke
  run or the 50-repeat run.
- The audit must verify the Stage 18 reference, data hashes, paired stream,
  budgets, monotonicity, pathwise dominance, and an exact repeat-zero replay.
- Passing would support the narrow pruning theorem and algorithm as a
  development candidate. WMT24 validation and direct comparison with recent
  adaptive-evaluation and sequential-model-confidence-set methods would still
  be required before an ICML claim.
