# SVD ablation findings

All 117 original WMT23 cases were evaluated with 100 repeats per arm (23,400 trajectories).
The SVD arm reproduced all 117 published Stage 9 mean label costs; both arms reproduced
the original query-ledger hashes. Exact pruning equivalence was tested against
the original engine in both arms on synthetic and real-pool paths.

Means below weight languages equally, then systems equally. Lower MSE, MAE, residual
variance and label cost are better. Prediction metrics use the full shared prequential
path; label cost uses the original first precision stop.

| History | Arm | Brier/MSE | MAE | Residual variance | Mean labels |
| --- | --- | ---: | ---: | ---: | ---: |
| aligned | svd | 0.169079 | 0.388743 | 0.156633 | 270.218 |
| aligned | no_svd | 0.171153 | 0.392958 | 0.158845 | 271.746 |
| permuted_history | svd | 0.246787 | 0.495061 | 0.210123 | 277.990 |
| permuted_history | no_svd | 0.246196 | 0.494462 | 0.210067 | 277.991 |
| reversed_history | svd | 0.250202 | 0.499709 | 0.209562 | 277.999 |
| reversed_history | no_svd | 0.250643 | 0.500330 | 0.209349 | 277.999 |

Paired label differences are SVD minus no-SVD. Negative differences favor SVD.

| History | Label difference | Relative change | Repeat-block MCSE | Target wins / ties / losses |
| --- | ---: | ---: | ---: | --- |
| aligned | -1.528 | -0.562% | 0.110 | 14 / 10 / 15 |
| permuted_history | -0.001 | -0.000% | 0.002 | 5 / 31 / 3 |
| reversed_history | +0.000 | +0.000% | 0.000 | 0 / 38 / 1 |

On aligned history, adding SVD changes Brier/MSE by -1.212%,
residual variance by -1.392%, and average label cost by -0.562%.
These effects isolate adding SVD features within this fixed ridge/trust pipeline.
See summary.csv for each language and coverage diagnostics, and by_target.csv for heterogeneity.

This is a development-data ablation, not independent confirmation on a new release.
Trust and stakes use identical update rules but their realized values may differ across arms.
The MCSE measures query randomization on fixed recorded pools, not generalization to new
systems, items or raters. Residual variance excludes bias; residual means and MSE are saved.
Full-path diagnostics include labels after stopping only for analysis. Historical-label
acquisition cost, human annotation time and computational speedup are not measured.

Validation: six new ablation tests, all 61 existing stage tests, release-manifest checks,
canonical-arm reference costs, ledger equality, exact pruning equivalence, independent
per-repeat/target/summary aggregation and MSE = variance + squared bias checks.
The saved artifacts contain metrics and hashes; full confidence curves are regenerated
by rerunning the experiment. See TEST_RESULTS.txt and run_metadata.json for evidence.
