# Stage 14 exploratory pilot: shared annotation scheduling

This is a *development* experiment on the same WMT23 fixed binary outcomes as
Stage 13. It tests whether scheduling paired comparisons to reuse labels changes
the number of certified conclusions under a fixed total annotation budget. It
does not establish novelty, official MQM rankings, or performance on new data.

## Locked pilot design

- Include all 237 within-language system pairs (66 en-de, 66 he-en, 105 zh-en).
- Each pair has its own independently precommitted uniform random item
  permutation. Each policy sees identical permutations for each repeat. A
  pair's PPR process consumes only prefixes of its own permutation, even if
  labels on later items have been revealed for other pairs.
- A single unique (system, item) binary annotation costs one label. It can be
  reused by all comparisons within that language. Histories and automatic
  predictions are not used in this pilot.
- First examine one language with master seed 20261022, 12 repeats; expand
  to all languages with the same 12 repeats, without changing policies.
- Family directional PPR threshold is 40 * 237, i.e. alpha=0.05 over 237
  pairs (two directions each), separately for each scheduling policy. Use
  Stage 13's standalone categorical PPR and deterministic exact-pool sign
  certificate. The Stage 13 reserve cap issue does not affect standalone PPR.
- Repeat-block seeds and all schedule tie breaks depend only on language,
  pair names/indices, repeat index, master seed, and previously revealed labels.
- At fixed unique-label budgets floor(25%,50%,75%) of M*N, count certified
  correct, wrong, unresolved; exact ties only after exhausting a pair's pool.
  Full-reference signs are used only for auditing and after-run reporting.
- The primary comparison is the number of certified correct pairs at 50% of
  unique labels, comparing all policies on the same permutations. Secondary
  budgets are 25% and 75%; no policy is selected or tuned using the outcomes.

## Policies (same closure rule)

After every acquired label, repeatedly advance any unresolved pair for which
both labels of its *next* precommitted item are already in the ledger. Update
its own PPR prefix and decision; free advances cost no labels. Continue until
none exists. A scheduler then chooses one unresolved pair and acquires the
first missing system label for its next item. All policies run identical
closure, including at budget checkpoints and at full annotation.

- `round_robin`: cycle over pair indices and choose the next unresolved pair.
- `reuse_first`: choose a pair whose next item requires just one new label, if
  any; resolve ties by rotating pair index. If none, choose a two-label pair.
- `evidence_first`: choose the pair with the largest current directional PPR
  evidence (capped at the family threshold); tie by rotating pair index.

This is intentionally a small scheduling ablation. It does not claim a new
optimal acquisition method. An improved follow-up would combine cost and
evidence, prove an efficiency statement, and test MQM with a practical margin.

## Validity and limitations

For each pair, its full precommitted permutation is uniform. A scheduling
policy reveals some *prefix* of that sequence, possibly using other labels.
Any pair's wrong declaration implies its own PPR or deterministic rule would
make a wrong declaration at some point on that full independent permutation.
The anytime bound over all prefixes and a union bound over 237 pairs therefore
cover this adaptive scheduling, even though labels and stopping decisions are
correlated across pairs. The policies have separate guarantees; no joint
guarantee across selected policies. Finite benchmark scores are fixed.

This design can be inefficient: using distinct random permutations for each
pair limits the opportunities for reuse. The full-label reference and
post-hoc pair gaps never guide querying. Repeats measure randomization over
orders, not generalization to new benchmarks or annotators.

## Post-pilot amendment (after seeing the three-policy output)

The initial three-policy results showed that `evidence_first` greatly exceeds
the two diffuse schedulers at fixed budgets. This can result simply from
focusing annotation on a few pairs. Add `focus_first`: finish the lowest-index
unresolved pair before moving on, with the same free closure, random pair
streams, threshold, and budgets. This is a stronger concentration control.
It was added after seeing the first results, so it cannot be called a
preregistered comparison or used to claim a discovered optimum.

Because the fixed alphabetical pair order may overrepresent hard or easy
pairs, also add `focus_random`: finish pairs in a precommitted random order
using a separate seed keyed only by language and repeat. This is an additional
post-pilot comparator; do not select the more favorable control afterward.
