# SAFE-EVAL Stage 8: matched zero-trust controls

Read PROTOCOL.md for the fixed comparisons and scope. This stage imports the
preserved Stage 7 modules and data from the sibling directory; use the complete
repository rather than moving this directory by itself.

From the repository root, run each line separately:

```bash
python -m unittest discover -s experiments/stage8 -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage8/run_stage8.py --repeats 100 --workers 2 --output results/stage8_local
python experiments/stage8/analyze_stage8.py --input results/stage8_local
```

There are seven new tests, alongside the preserved 28 Stage 7 tests. The full
comparison has 117 cases, 70,200 method trajectories and 23,400 reserved stopping
bounds. The audit also checks 11,700 paired raw stops and 2,340 preserved Stage 7
target metrics. No GPU or new data download is required.

For an installation check, use `--repeats 1` and a new output directory such as
`results/stage8_smoke`, then analyze that directory. Reduced-repeat runs use a
different vectorized RNG stream and do not reproduce the fixed reference.

Local output includes per-trial decisions and lossless full curves. Compact
reference tables, figures and the audit record will be retained after the fixed
comparison. Full curves remain local. The published PPR baseline has a different
betting construction from the zero-trust control; both are needed to separate
inference-rule effects from historical predictions.
