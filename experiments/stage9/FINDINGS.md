# Stage 9: ordinary raw95 cost safeguard

The complete independent replay and exact-count audit passed.

The fixed development comparison finds a modest useful-history gain while
strengthening the reference guarantee from the stricter raw control used in
Stage 7/8 to unchanged ordinary raw95. With aligned histories, prediction
uses 2.801% fewer target labels than raw95, 2.798% fewer than its matched
zero-trust control, and 1.141% fewer than the integer-grid calibrated raw
control. The improvement against calibration is uneven: German is worse,
and the prediction method also loses to calibration under both history
stress conditions. This is development evidence, not an established ICML
contribution or a new statistical principle.

## Fixed comparison

The protocol and eleven implementation/protocol files were frozen at commit
4e7aa1dd9c83a5163778e66b42735d97f4224ece before the 100-repeat run. The
comparison retains all 39 targets, three languages and aligned, permuted and
reversed histories: 117 cases and 46,800 method trajectories. Every method
shares the same uniform query ledger for its target. WMT23 is development
data; no new human annotations were collected.

The primary contrast is prediction minus matched zero under aligned history.
Overall means weight the three languages equally, then systems equally within
language. They are not pooled means over the unequal target counts.

| History | Ordinary raw95 | Calibrated raw95 | Matched zero | Prediction |
| --- | ---: | ---: | ---: | ---: |
| Aligned | 278.006 | 273.337 | 277.998 | 270.218 |
| Permuted | 278.006 | 273.337 | 277.998 | 277.991 |
| Reversed | 278.006 | 273.337 | 277.998 | 277.999 |

Entries are mean target labels at the first nonempty interval of width at
most .10. Historical label collection, human time and computation are not
included in that cost. They must not be interpreted as total annotation cost.

| Aligned history | Prediction vs raw95 | Prediction vs calibrated raw95 | Prediction vs matched zero |
| --- | ---: | ---: | ---: |
| en-de | -0.004% | +1.390% | -0.004% |
| he-en | -3.139% | -1.750% | -3.139% |
| zh-en | -3.520% | -1.361% | -3.512% |
| Equal-language overall | -2.801% | -1.141% | -2.798% |

Negative changes mean fewer labels. The primary paired mean difference is
-7.779 labels, with conditional query-randomization Monte Carlo standard
error 0.203. Against calibrated raw95 the difference is -3.119 labels,
MCSE 0.255. These MCSEs condition on the fixed data and fitted historical
setup; they do not quantify generalization to new systems, languages,
annotators or benchmarks.

Prediction improves the aligned target mean against matched zero in 29 of
39 targets and ties in ten. Against calibration it improves 20 target means
and worsens 19, including all twelve German targets. Keep this heterogeneity
when presenting the overall result.

Under permuted/reversed histories, prediction is essentially raw95: changes
of -0.0056% and -0.0024%, respectively. It is 1.703% and 1.706% MORE costly
than calibrated raw95. Relative to matched zero, the changes are -0.0025%
and +0.0006%. The calibrated raw control is the more useful model-free
procedure in these stress conditions.

## Exact calibration and guarantee

| Pool size N | Raw95 worst error | Calibrated threshold | Calibrated worst error | Prediction error allowance |
| --- | ---: | ---: | ---: | ---: |
| 154 | .037902262 | 16 | .048068169 | .012097 |
| 589 | .042459502 | 17 | .049389775 | .007540 |
| 820 | .042943077 | 18 | .047311342 | .007056 |

These error probabilities are exact integer path counts, displayed as rounded
decimals. The certificate JSON files retain the exact fractions and all
surviving-string counts. Calibration uses only N and the implemented raw
rule, not target outcomes or history quality. The calibrated threshold is
the smallest valid integer from 2 through 20 for the pre-repair PPR rule;
it is not globally optimal calibration. Empty-set repair could permit
additional calibration, so this remains a limited baseline search.

The certified raw error plus the prediction error allowance is at most .05.
The returned intersection is a subset of raw95, or falls back to raw95 if
empty. Consequently the first valid precision stop is no later than raw95
on every common query path. This is a deterministic containment argument,
including failure paths, rather than an empirical average-cost claim.
At least 95% simultaneous coverage is per fixed target and method over time,
not a familywise guarantee across all 117 cases or all compared methods.

The largest observed extra cost versus raw95 is zero. The bound does not
extend to matched zero or calibrated raw95: prediction can cost two extra
labels versus matched zero on an aligned path and six under reversed
history; its largest extra cost versus calibration is 188 labels. Those
paths are retained in worst_paths.csv.

## Coverage and empty sets

Equal-language full-path coverage is 96.483% for raw95, matched zero and
prediction, and 95.744% for calibrated raw95 in each history condition.
These are empirical frequencies from finite simulated query paths, not
the justification of nominal validity. The exact raw certificate and
conservative predictable-capital construction supply that justification
under the assumptions in THEORY.md.

The target is the unweighted mean of recorded binary error-free outcomes in
these fixed pools. It is distinct from official severity-weighted MQM,
latent translation quality, future-population risk and uncertainty from
repeated human annotation. Certification has been demonstrated for N=154,
589 and 820 only; its cost on substantially larger pools remains untested.

The equal-language fraction of trajectories with an empty interval at any
time is 3.150% for all four outputs. No method repairs an interval before
its reported precision stop in this run. Empty intervals are never counted
as precision. Later emptiness remains a full-path coverage failure; the
exact mean at full evaluation does not erase an earlier failure.
Stopped midpoint error exceeds .05 in 3.261% of raw95, matched-zero and
prediction paths, and 3.922% of calibrated paths under the same weighting.

## Verification and reproduction

The independent audit passed all 46,800 saved stopping decisions, 35,100
raw95 stopping bounds, 6,156,900 query/capital replay steps and 1,571 exact
backward risk counts. Every raw query stream and all 585 raw Stage 8 reference
metrics matched. No frozen implementation file changed during the run or audit.
The report's 36 prediction contrasts were also reconstructed from the saved
per-trial costs and matched the frozen analyzer. The audit took 940.7 seconds.

The complete run took 447.1 seconds on the recorded Python/NumPy runtime,
using two workers and one BLAS thread per worker. All 43 local tests and
the GitHub Ubuntu 3.9/3.12 and macOS 3.12 checks passed for the frozen
implementation. Full curves and per-trial outputs are generated locally;
compact tables, exact certificates and logs are committed. See README.md
for commands and REFERENCE_FILES.md for the reference-package contents.

## Interpretation and next research decision

This addresses the specific ordinary-raw95 cost limitation of the earlier
reserve construction, with a smaller aligned gain. It applies known finite
state calibration, error allocation, betting and confidence-set intersections.
It does not show superiority to calibrated procedures in every condition,
or establish novelty beyond the literature listed in THEORY.md.

Before making a publication claim, compare the exact construction with prior
forecast-assisted inference and sequential calibration, and lock a new public
confirmation pool before inspecting its outcomes. Include stronger model-free
calibration and predictive baselines, real historical distribution shifts,
historical-data costs and annotation uncertainty. WMT23 is already development
data, and previously inspected WMT24 data cannot serve as untouched confirmation.
Any new tuning belongs in a separately recorded development study; do not
rerun this comparison until its outcome looks favorable.
