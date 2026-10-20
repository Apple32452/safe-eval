# SVD ablation

The existing results_reference directory contains the completed DENSE-engine
run whose final source-integrity check failed after CSV writes. It is not a
completed pruned-engine reference release. Its 23,400 records have been audited
separately: read EXISTING_RUN_FINDINGS.md and EXISTING_RUN_AUDIT.json. Original
CSV files and running-status metadata are preserved unchanged. Reproduce that
saved-metric audit with `python experiments/svd_ablation/audit_existing_results.py`.
For a clean final run, use a fresh output directory and keep sources unchanged
until completion. Do not run report.py against the failed-run metadata.

This experiment compares the current SAFE-EVAL predictor (item means + SVD +
ridge + trust) with item means + intercept ridge + trust, using the unchanged
Stage 9 inference rules retained by subsequent stages. Existing experiments are
imported read-only. The reference adapter loads a private module namespace,
and the full run uses exact candidate pruning for both arms. Pruning drops only
permanently excluded candidates and unused control branches. Tests compare
full confidence curves against the unchanged engine in both arms on synthetic
and real pools, and the full run checks all published original-arm mean costs.

The ablation is `reference_features(history, rank=0)` rather than disabling
prediction, ridge, or trust. It preserves the intercept and historical means.
The canonical feature function still computes its SVD internally; this study
tests statistical feature contribution, not computational speedup.

Read PROTOCOL.md for metric definitions and TEST_RESULTS.txt for existing test
evidence. ABLATION_TEST_RESULTS.txt records the six new tests. The initial_attempt
metadata documents the sandbox failure before worker creation. The old dense
run was not successfully interrupted and ultimately produced the audited CSVs.

From the repository root in PowerShell:

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -m unittest discover -s experiments/svd_ablation -p test_ablation.py -v
python experiments/svd_ablation/run_ablation.py --workers 2 --output experiments/svd_ablation/results_local
```

Use a new output directory for every run. The default is results_reference,
which already exists and cannot be overwritten by this command.
The working files are not yet committed.
No downloads, external services or additional annotations are required.

Results include per_trial.csv (all 23,400 arm/repeat records), by_target.csv,
summary.csv (language and equally weighted overall means), comparison.csv
(paired cost differences), and run_metadata.json (case definitions, original
seeds, history hashes, source hashes, matched ledger hashes and artifact hashes).
Full trajectories are computed and checked in memory; rerun to regenerate
them. Full-path prediction diagnostics deliberately include labels after
the inference stopping time; those labels are excluded from label cost.

Negative SVD-minus-no-SVD cost differences favor SVD. For prediction MSE, MAE
and residual variance, smaller is better; consult residual mean alongside
variance because variance alone ignores bias. Coverage is reported as an
empirical diagnostic, not as a proof from simulation.
