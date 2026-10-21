# Stage 22 frozen protocol: graph-aware pruning for reference comparisons

## Research question

Stage 20 proved pathwise dominance for active-system pruning, but the complete
comparison graph kept almost every system active and produced only a 0.665%
gain. Stage 22 asks whether the same exact finite-pool method is materially
useful for a practical sparse objective:

> compare every candidate system with one designated incumbent/reference
> system, with simultaneous family-valid conclusions.

This is a development experiment, not an ICML claim. The protocol, primary
metric, graph suite, seeds, and gate are frozen before Stage 22 implementation
or outcome computation. WMT24 remains untouched.

## Data and common paths

- Reuse the exact 14 WMT25 continuous-score matrices prepared in Stage 17.
- Reuse the 50 Stage 18 common item and within-item system orders with master
  seed 20261025 and namespaces `common_item_order` and
  `common_system_order`.
- Reuse the unchanged Stage 17 continuous finite-population e-process and exact
  full-pool rule.
- Scores are fixed recorded human-evaluation item means. No new labels are
  collected.
- Charge each acquired system-item score once.

## Primary reference-star suite

For a language with `S` systems, create all `S` reference tasks. Reference
task `r` requests exactly the `S-1` edges `{(r,s): s != r}`. Every system
serves as the reference once. Results must average over all references; no
reference may be selected using WMT25 outcomes.

Within each reference task, use family threshold `40 * (S-1)`. The guarantee
is taskwise 95% simultaneous directional error control by the Stage 17 anytime
bound and union bound. Stage 22 does not claim one joint 95% event across the
collection of reference tasks.

## Methods

Both methods use the identical requested edges, item order, within-item system
order, pairwise certificate, and irreversible declarations.

### `star_common`

At every common item, score every system in the precommitted system order.
Update requested edges when both endpoints are available. Stop when every
requested edge is certified; the exact full-pool rule guarantees termination.

### `star_pruned`

At the start of every common item, form the unresolved requested-edge graph and
commit to scoring exactly its incident systems, in the common system order
restricted to that set. Complete the committed item block even if an edge
resolves within it. Resolved vertices never reactivate. Stop when every
requested edge is certified.

The active set is committed before any score on the current item is observed.

## Primary endpoint

For each language, repeat, and reference, record the number of unique
system-item labels needed to certify all requested edges. The paired relative
saving is

[
(mathrm{cost}_{common}-mathrm{cost}_{pruned}) /
 mathrm{cost}_{common}.
]

First average references within each language/repeat, then average languages
equally within each repeat. The reported conditional Monte Carlo standard
error is over the 50 precommitted repeat blocks.

Also report absolute saving, all per-language means, every reference-task
saving, and the distribution of unresolved-degree trajectories.

## Pathwise and correctness audits

For every language/repeat/reference:

1. both methods must return the same final decision for every requested edge;
2. every final decision must equal the exact full-pool sign;
3. every pruned edge must resolve at no greater label cost than its matched
   common-control edge;
4. unique-label and common-order accounting must be exact;
5. active sets must be determined from prior completed items only; and
6. results must be invariant to outcomes not yet revealed to the policy.

Save 25%, 50%, and 75% full-system-label-budget checkpoints as secondary
resolved/correct/wrong summaries. The pruned resolved set must contain the
control resolved set at every saved checkpoint.

## Secondary graph-density diagnostic

Without changing the primary gate, repeat the comparison for outcome-independent
name-sorted circulant graphs with offsets one and offsets one-plus-two, plus the
complete graph. These graphs diagnose how savings scale with requested-edge
density. They are descriptive and cannot replace a failed reference-star gate.

## Frozen development gate

Stage 22 passes only if all of the following hold:

1. mean primary relative label saving is at least 10%;
2. the mean saving exceeds two conditional Monte Carlo standard errors;
3. more than half of the 14 language-level mean savings are positive;
4. all final decisions match the common control and exact full-pool signs;
5. no pruned path violates per-edge resolution-cost dominance; and
6. all implementation, data-hash, stream, and exact replay audits pass.

Failure ends graph-pruning experimentation on WMT25. A pass would establish
material development relevance, not ICML readiness. It would still require a
direct definition-level comparison with recent active-testing and sequential
model-confidence-set methods, a frozen paper-level method, and one untouched
WMT24 confirmation run.

## Integrity

- Commit this protocol and the related-work boundary before implementation.
- Commit implementation, tests, audit, and hashes before a smoke or full run.
- A smoke run may test software only; any amendment after output must be
  recorded and must not weaken the gate.
- Preserve all failed tasks and language-level results.
