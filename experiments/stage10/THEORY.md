# What Stage 10 certifies

## Finer unrepaired calibration

At any threshold h, the pointwise PPR gate accepts total K exactly when its
implemented log ratio is smaller than log(h). Increasing h enlarges the
accepted sets and the event of retaining the truth at every time. The
unrepaired worst-case error over K is consequently nonincreasing in h.
Twelve dyadic bisections retain a valid upper endpoint and an invalid lower
endpoint, with difference 1/4096. Exact forward integer counts determine
every comparison; an independently implemented backward recurrence checks
all counts at both final endpoints. This establishes a valid finer threshold
for the specified gate family, without numerical probability approximation.

The finer gate is nested inside raw95 because h <= 20. The calibrated running
intersection therefore lies inside the running raw95 interval whenever it
is nonempty. Otherwise the output equals raw95. Thus the output remains
contained in raw95, and a first valid precision stop cannot be later than
raw95 on a common query path. This includes failure paths. A valid unrepaired
coverage certificate also bounds the repaired output's failure event.

Pointwise nesting does NOT by itself prove dominance over the repaired
integer-grid control. A smaller running set can become empty and return to
raw95 while a larger running set remains nonempty. The code tests a general
nested-gate example in which this changes coverage. This example is not a
claim that the particular PPR family's worst-case repaired error is
nonmonotone. It explains why no such monotonicity is assumed or used.

## Exact repaired coverage recurrence

For a binary prefix, let G be the set of totals that have belonged to every
RETURNED interval so far. Before fallback, G is the nonempty calibrated
running intersection. If its next intersection becomes empty, the returned
interval is raw95. Since the previous G was contained in every preceding raw
pointwise set, the new G is simply old G intersected with the current raw
pointwise set. The calibrated running set then remains empty, so later
updates intersect G with each new raw pointwise set.

Every G is an integer interval. Prefixes can therefore be aggregated by
(success count, lower G, upper G, fallback phase), adding their integer
multiplicities. Empty G states have no full-path coverage survivors and may
be dropped. At time N, a surviving state has G={K} with K equal to the final
success count. The multiplicity gives the number of covering strings among
the comb(N,K) equiprobable full binary strings. The maximum exact failure
fraction over every K is the repaired error certificate.

The independent implementation carries actual raw and calibrated running
endpoints and an explicit bitmask of all-time survivors. It intersects the
mask with each actual returned interval. It does not use the compressed
phase-state recurrence. Exhaustive enumeration on all small binary strings
cross-checks both implementations. A capped state calculation returns no
failure probability or usable certificate.

The repaired-control search is deliberately limited: only three predetermined
offsets below the selected fine threshold, and only if the initial full count
completes within the recorded limits. The selected threshold must have a
completed valid certificate. This neither finds globally optimal confidence
sequences nor exhausts possible repair-aware calibration.

## Reusing Stage 9 correctly

Stage 10 changes only model-free calibration. It does not recompute, retrain,
shrink or select any historical prediction branch. The full source Stage 9
run must have a passing independent audit. Its protocol, every query ledger,
every curve-file byte hash, all 46,800 saved decisions and all 2,340 target
metric values are checked before reuse. The canonical reference source is
separately hashed before examining the Stage 10 benchmark comparisons.

The new audit independently replays the two added control curves from the
original PPR interval function and cumulative interval reductions. It checks
all six methods' decisions and all preserved source metrics, without claiming
to repeat the original prediction-capital audit. Runtime-dependent local
prediction paths are preserved and any differences from archived reference
metrics are reported in the source manifest.

The confidence and cost arguments apply to fixed recorded binary pools under
uniform sampling without replacement, with the runtime checks and arithmetic
assumptions inherited from Stage 9. They do not cover official weighted MQM,
new annotator noise, future populations, nonuniform acquisition or collection
of historical labels. All benchmark evidence remains development evidence.
