# Stage 19

Stage 19 tests a common-core adaptive-tail design against the strong common
random test-set control from Stage 18. The protocol is frozen before
implementation and experiment execution. WMT25 is development data; WMT24
remains untouched.

After preparing the frozen Stage 17 matrices, run:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python experiments/stage19/run_stage19.py \
  --data results/stage17_data --repeats 50 \
  --output results/stage19_development
python experiments/stage19/summarize_stage19.py \
  --input results/stage19_development
python experiments/stage19/audit_stage19.py \
  --data results/stage17_data \
  --input results/stage19_development \
  --repeat-zero-replay results/stage19_smoke
```
