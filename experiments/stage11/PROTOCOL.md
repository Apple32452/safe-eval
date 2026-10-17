# Stage 11: published sequential boosting on the same PPR process

Development study, fixed before new benchmark comparisons. Parent main commit
faa189d8888a7ad46afd8a007ab3cbc525a47026 has tree
3142145cf4dac63037e5c76d86b903c83f924270. Preserve all Stage 7–10 files.

## Baseline and numerical specification

Apply Fischer and Ramdas, arXiv:2410.16076v4, Algorithm 1 and Section 4.1,
to the existing Beta(1,1) finite-population PPR factors. Section 4.2 supplies
related binary sampling-without-replacement applications; we do not claim to
reproduce their particular RiLACS simulation. This is a published algorithm
applied to our chosen process, not a proposed new method.

For each candidate total K, use the exact conditional null success probability
(K-s)/(N-t+1) and prior predictive probability (s+1)/(t+1), with s the number
of successes before query t. Invert all K=0,...,N; do not assume monotonicity
or discard holes. Return the hull of surviving candidates.

Use fixed wealth grid Q=2^39 and rejection wealth B=20Q, alpha=.05. Every
update uses integer division rounded downward; no floating logarithms or root
solver determine rejection. Restrict N to 2,...,820 and prove the int64
intermediate bound before execution. The exact two-outcome water-filling
formula and degenerate-null cases are in THEORY.md. If a candidate reaches B
or its observed outcome is impossible under that null, reject it permanently.
Wealth zero remains zero on null-possible outcomes. No later outcome may
affect the current pair of possible updates.

Add two controls: grid_ppr95, the matching downward-rounded unboosted PPR,
and boosted_ppr95. If the grid confidence set becomes empty, return the
unchanged raw95 interval; if the boosted set becomes empty, return the grid
control's output. Both replacements expand an empty set. At N return the
exact recorded mean, retaining every earlier coverage failure. Empty outputs
are never precision stops. Use the existing epsilon=.05 and integer width
criterion 10*(upper-lower)<=N.

Prove conservative conditional validity and boosted rejection-set containment
relative to grid_ppr95. This supplies a never-later precision stop relative
to that implemented matched control. Differences from the existing floating
raw95 are measured, not assumed absent; the exact-arithmetic published result
does not automatically imply numerical dominance over that old implementation.

## Fixed paired comparison and reuse

Reuse the complete audited Stage 10 and Stage 9 traces for all 117 cases,
100 repeats, identical labels and query ledgers. Reconstruct all 70,200 source
decisions and 3,510 metric values; verify prior audits and separately freeze
their full file fingerprints before inspecting any new benchmark comparison.
Local reproduction may preserve an audited local source's runtime-dependent
prediction results; canonical reproduction requires the archived fingerprints.
No source prediction, trust, stake, alpha, seed, precision or model is changed.

There are eight methods: the six preserved Stage 10 methods and these two
controls, totaling 93,600 compared trajectories, of which 70,200 are reused.
Identical model-free histories may reuse computation only after checking the
full outcomes and query ledger; verify every saved case against that result.

Primary contrast: unchanged budget_prediction95 minus boosted_ppr95 under
aligned history, weighting languages equally then systems equally. Also report
each language and both adverse histories, matched zero, fine/repair/raw/grid
comparisons, conditional query-randomization MCSE, all target means, wins and
losses, worst extra labels, simultaneous coverage, stopped error, empty sets,
fallbacks, holes and every numerical difference from floating raw95. Do not
choose favorable targets or tune the grid after observing these comparisons.

## Verification and decision

Before locking, test exact conditional expectations against rational arithmetic,
all binary strings for N=2,...,9, independently coded observed-branch updates,
degenerate nulls, int64 bounds at the actual pool sizes, unique queries, exact
final means, prefix predictability, hull holes and pathwise matched containment.
Use only small synthetic data before the lock. Then independently replay all
new controls with a separate observed-branch implementation and compare every
candidate's first rejection, output interval, fallback and hole count. Rebuild
every decision and summary. Reuse the already-completed source capital and
calibration audits explicitly; do not claim to repeat those computations.

Freeze code, this protocol, theory, instructions and source manifest before
the full comparison. Report all results, including an eliminated advantage.
WMT23 remains development data. This baseline check cannot establish novelty,
future-population quality, new-rater validity or end-to-end human time savings.
No new dataset, annotation collection, algorithm tuning or proposal submission
is authorized by this stage.
