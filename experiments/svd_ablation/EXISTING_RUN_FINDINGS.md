# Audit of the existing dense-engine run

All 117 cases and 23,400 arm/repeat records are present. Saved metric checks passed.
The process failed after writing all four CSVs at `AssertionError: Source changed during run`.
Original run_metadata.json is preserved and still says running; it has not been marked complete.

| Aligned-history metric | With SVD | Without SVD | SVD relative change |
| --- | ---: | ---: | ---: |
| mean_queries | 270.218333 | 271.746389 | -0.562% |
| mse | 0.169079 | 0.171153 | -1.212% |
| mae | 0.388743 | 0.392958 | -1.073% |
| residual_variance | 0.156633 | 0.158845 | -1.392% |

| History | SVD minus no-SVD labels | Change | MCSE | Target wins / ties / losses |
| --- | ---: | ---: | ---: | --- |
| aligned | -1.528056 | -0.562309% | 0.109899 | 14 / 10 / 15 |
| permuted_history | -0.000722 | -0.000260% | 0.002380 | 5 / 31 / 3 |
| reversed_history | +0.000222 | +0.000080% | 0.000222 | 0 / 38 / 1 |

Checks: unique and complete repeat IDs; finite bounded metrics; valid label costs;
MSE = residual variance + squared residual mean; coverage/error consistency;
all target and equally weighted language/overall aggregates; paired differences and MCSE;
all 117 SVD reference target costs and coverage values; existing release manifests.

Interpretation: SVD has a small aligned-history average benefit in this fixed ridge/trust
pipeline, concentrated in Hebrew/Chinese. German has a tiny average label-cost increase.
Permuted/reversed histories show effectively no label-cost benefit. This is development
evidence on previously inspected fixed pools, not new-data confirmation.

Provenance limit: wrapper/source files changed during execution. The metric audit cannot
recover unsaved full curves, per-step predictions or the final run ledger-hash dictionary.
Existing engine/data files are unchanged. Keep these outputs as an audited development run,
not a successfully completed frozen-source or full pruned-engine validation run.

Next: preserve these files, freeze the current implementation, rerun to a NEW directory
only if a fully reproducible final release is needed, then use report.py on that directory.
