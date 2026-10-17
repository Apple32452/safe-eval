# Stage 11: sequential-boosting baseline check

This implements a published method on the same PPR process and fixed query
paths. Read PROTOCOL.md and THEORY.md. No new prediction algorithm or novelty
claim is introduced. WMT23 remains development data.

Start with complete independently audited 100-repeat Stage 9 and Stage 10
outputs, generated using their instructions. Committed reference tables omit
the full traces required here. From the complete repository root:

    python -m unittest discover -s experiments/stage11 -p 'test_*.py' -v
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage11/run_stage11.py --stage9-input results/stage9_local --stage10-input results/stage10_local --output results/stage11_local
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage11/analyze_stage11.py --input results/stage11_local --stage9-input results/stage9_local --stage10-input results/stage10_local

Use a new output directory. The comparison retains 70,200 previously audited
source trajectories and adds 23,400 control trajectories, for 93,600 compared
trajectories across all 117 cases. Both controls are model-free and use exact
integer updates. The auditor independently replays the new candidate rejection
times, returned intervals, holes, fallbacks and all saved decisions. Existing
prediction-capital and calibration audits are explicitly reused.

The default preserves any differences in an audited local source. The optional
--canonical-reference run flag additionally requires the archived source file
fingerprints. No GPU, paid service, new annotations or dataset download is needed.
