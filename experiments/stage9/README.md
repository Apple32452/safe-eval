# Stage 9 ordinary raw95 safeguard

This fixed development comparison tests whether certified spare raw error
probability permits useful prediction gains while stopping no later than the
unchanged ordinary raw95 baseline on every shared uniform query path.

Read PROTOCOL.md and THEORY.md. There are four methods, including matched
zero-trust and calibrated raw controls. All Stage 7 and Stage 8 files are
preserved. A new method or ICML contribution is not established by this setup.

From the COMPLETE repository root, use your existing environment:

    python -m unittest discover -s experiments/stage9 -p 'test_*.py' -v
    python experiments/stage9/certify_stage9.py --output results/stage9_certificates
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage9/run_stage9.py --certificates results/stage9_certificates --repeats 100 --workers 2 --output results/stage9_local
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage9/analyze_stage9.py --certificates results/stage9_certificates --input results/stage9_local

Use NEW certificate and run directories. Certificates refer to the runtime's
actual raw state gates. The runner verifies them on that runtime, and the
analyzer checks them with an independent backward recurrence. The fixed run
has 117 cases and 46,800 method trajectories. No GPU or data download is needed.

For a software smoke check, use --repeats 1 and a separate output directory.
Such a check skips reference stream/metric matching and is not new research
evidence. Full local output includes lossless count curves, query ledgers,
scalar enclosures, per-trial decisions, and replayable certificate files.
