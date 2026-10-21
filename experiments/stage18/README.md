# Stage 18

Stage 18 compares the frozen Stage 17 frontier scheduler with a common random
test set that scores every system on the same growing subset of WMT25 items.
Read [PROTOCOL.md](PROTOCOL.md) before running the experiment.

After preparing the frozen Stage 17 matrices, run:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python experiments/stage18/run_stage18.py \
  --data results/stage17_data --repeats 50 \
  --output results/stage18_development
python experiments/stage18/summarize_stage18.py \
  --input results/stage18_development
python experiments/stage18/audit_stage18.py \
  --data results/stage17_data \
  --input results/stage18_development \
  --repeat-zero-replay results/stage18_smoke
```

Run the same command with `--repeats 1 --output results/stage18_smoke` before
the full experiment for an end-to-end software check. WMT25 is development
data in this stage. WMT24 remains untouched.
