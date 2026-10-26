# One preserved anomalous worker timeout

The first complete-graph S=100,N=1024 worker reached the frozen 180-second
deadline without leaving a plain-evidence checkpoint. The same case's other
two workers completed plain evidence in 5.09 and 3.41 seconds. Root cause is
unknown; do not attribute this stall to a measured CS operation or discard it.

After the main matrix finishes, run one additional identical-input diagnostic
with the same 180/45-second rules. Save it separately, excluded from main timing
medians; do not add new fixtures or tune thresholds. This diagnoses reproducibility,
not a statistical efficacy experiment. Source/parameter hashes remain frozen.
The main result still reports two completed repetitions and the original timeout.

Outcome: retry completed with exact evidence parity, 4.552 seconds plain evidence
and 27.831 seconds instrumented replay, 87,899 labels. It is excluded from main
medians. This establishes repeat completion on the same input, not the stall's
root cause. See results/diagnostic_retry.json for all phases and peaks.
