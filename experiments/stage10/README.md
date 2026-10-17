# Stage 10 stronger-calibration and novelty study

Stage 10 keeps every Stage 9 prediction output fixed and adds two model-free
controls: a twelve-round finer PPR calibration, and a limited exact repaired
calibration when the state-counting certificate completes. If no lower
threshold is certified, the repaired control equals the fine control.
Read PROTOCOL.md, THEORY.md and NOVELTY_REVIEW.md. Neither a new prediction
method nor an ICML contribution is established by this study.

The study reuses a COMPLETE independently audited 100-repeat Stage 9 run.
First finish the Stage 9 commands, including its analyzer. Its compact
committed reference tables omit full curves and cannot serve as source input.
No GPU, new data download or new API usage is needed.

From the complete repository root, using your existing environment:

    python -m unittest discover -s experiments/stage10 -p 'test_*.py' -v

Generate fresh Stage 10 certificates from the same Stage 9 certificate folder
used in the source run. Fine search and exact repaired counting can take time;
capped attempts are recorded and cannot authorize a threshold.

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage10/calibrate_stage10.py --stage9-certificates results/stage9_certificates --output results/stage10_certificates

Run the fixed comparison. It verifies the source protocol, previous audit,
full query ledgers, saved decisions and metrics before reuse. It preserves
local runtime-dependent prediction results and records any differences from
the archived reference. The canonical reference additionally matches the
committed STAGE9_TRACE_MANIFEST.json, which is not required for local runs.

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage10/run_stage10.py --stage9-input results/stage9_local --stage9-certificates results/stage9_certificates --certificates results/stage10_certificates --output results/stage10_local

Independently audit the fine/repair certificates and both new control curves,
then reconstruct all six methods' decisions and paired comparisons:

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage10/analyze_stage10.py --input results/stage10_local --stage9-input results/stage9_local --certificates results/stage10_certificates

Use new certificate and output directories for each run. The complete study
has 117 cases, 100 repeats and 70,200 method trajectories, including 46,800
unchanged source trajectories. It does not claim those source trajectories
are newly generated or independently re-audited prediction capital.

The compact results_reference package contains summaries, metadata and the
completed audit, not full per-trial outputs or new control curves. Reproduce
locally to obtain them. Source and reference file hashes are recorded in
MANIFEST_SHA256.json; the pre-comparison implementation lock is separate.
