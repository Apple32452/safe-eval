# Stage 15 development protocol: frontier utility for shared annotations

## Research question

Can an acquisition rule that scores each *unique system-item annotation* by
its value across all unresolved comparisons certify more system-pair
conclusions than the Stage 14 evidence scheduler at the same human-label
budget?

This is a WMT23 development experiment. It may identify a candidate method;
it cannot establish an ICML contribution or benchmark generalization. The
fixed outcome is the recorded binary error-free indicator used in Stages 7,
13 and 14, not official severity-weighted MQM quality.

## Fixed population, inference and cost

- Use all unordered pairs within en-de, he-en and zh-en: 66 + 66 + 105 = 237.
- Use the Stage 14 construction: each pair receives an independent,
  precommitted uniform item permutation, and consumes only a prefix of it.
- Use master seed 20261022 and 50 repeat blocks. The first 12 blocks therefore
  reproduce the Stage 14 orders.
- A revealed `(system, item)` label costs one unit and remains available to
  every comparison in that language. Historical annotations and computation
  are outside this target-label cost.
- After each paid label, repeatedly advance every unresolved pair whose two
  labels for its next precommitted item are already available.
- Use the standalone Stage 13 categorical PPR plus its deterministic
  finite-pool certificate. Use directional threshold `40 * 237 = 9480`, for
  nominal 95% family control over 237 pair conclusions, separately for each
  policy. The Stage 13 reserve mixture and its cap limitation are not used.
- Checkpoints are floor(25%, 50%, 75%) of all unique system-item labels in
  each language. Report correct, wrong and unresolved conclusions separately.
  Full outcomes are available only to the simulation oracle and after-run
  audit; no full gap or final direction enters a scheduler.

## Locked policies

Retain three controls from the final Stage 14 comparison:

1. `focus_random`: finish unresolved pairs in a precommitted seeded random
   pair order.
2. `focus_first`: finish unresolved pairs in fixed index order. This diagnoses
   data-order effects and is not a primary baseline.
3. `evidence_first`: choose the unresolved pair with the largest current
   maximum directional PPR evidence, then acquire its first missing next-item
   label.

Add two annotation-level policies. At a scheduling step, let `F(l)` be the
set of unresolved pair frontiers whose next item requires the currently
unseen unique label `l=(system,item)`. Let `E_p` be pair `p`'s largest current
directional PPR evidence, zero before its first paired observation. Every
candidate label costs exactly one.

4. `frontier_count`: choose `l` maximizing `|F(l)|`.
5. `frontier_evidence`: choose `l` maximizing

       U(l) = sum_{p in F(l)} (Q + min(E_p, 9480 Q)),  Q=2^20.

The added `Q` gives every unresolved frontier positive weight and the sum
credits a label that serves several current pair frontiers. Ties for both
policies use one precommitted random priority over all unique labels, keyed
only by master seed, language and repeat. The label priority is independent
of target outcomes. No coefficient, bonus, temperature or lookahead is tuned.

## Primary comparison and interpretation

The primary comparison is `frontier_evidence - evidence_first` in the number
of correctly certified pairs at 50% of unique labels, summed across the three
languages within each matched repeat block. Report its mean, conditional
Monte Carlo standard error and all 50 block differences. Secondary comparisons
use 25% and 75%, `frontier_count`, and both concentration controls.

The method advances only pair-specific random prefixes. Hence a wrong
declaration for any adaptively scheduled pair is contained in the event that
the pair's anytime-valid process makes a wrong declaration somewhere along
its complete precommitted random permutation. A union bound across 237 pairs
gives the stated per-policy family guarantee despite shared labels and
dependent stopping decisions. The several policies do not share one joint
95% guarantee.

The Stage 15 candidate passes its *development gate* only if
`frontier_evidence` improves on `evidence_first` at the primary 50% budget
and does not produce an observed wrong-decision excess. Passing does not prove
novelty. Failure ends this exact rule; its weights will not be tuned on WMT23.

## Requirements before an ICML contribution claim

Regardless of this result, a contribution claim requires all of the following:

1. A theorem or formally proved property specific to shared annotation
   allocation, beyond the validity of the existing pairwise PPR processes.
2. Comparison with active evaluation, active ranking and anytime leaderboard
   methods under matched unique-label accounting.
3. A practical equivalence or superiority target based on a defensible MQM
   margin, with Professor Koehn's input on the estimand.
4. A protocol frozen before an independent benchmark is inspected, with
   gains over strong controls and full reporting of wrong and unresolved cases.

No repeated development experiment can replace these requirements.
