# Stage 21

Stage 21 uses a disjoint common-item pilot to select a system-order chain,
tests only adjacent relations on the remaining finite pool, and uses transitive
closure to recover all-pair conclusions. WMT25 is development data; WMT24
remains untouched.

After preparing the Stage 17 matrices, run:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python experiments/stage21/run_stage21.py \
  --data results/stage17_data --repeats 50 \
  --output results/stage21_development
python experiments/stage21/summarize_stage21.py \
  --input results/stage21_development
python experiments/stage21/audit_stage21.py \
  --data results/stage17_data \
  --input results/stage21_development \
  --repeat-zero-replay results/stage21_smoke
```
