# Stage 20

Stage 20 tests active-system pruning on the exact common random test streams
from Stage 18. The candidate has a pathwise label-cost dominance theorem over
the unpruned common control. WMT25 is development data; WMT24 remains untouched.

After preparing the Stage 17 matrices, run:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python experiments/stage20/run_stage20.py \
  --data results/stage17_data --repeats 50 \
  --output results/stage20_development
python experiments/stage20/summarize_stage20.py \
  --input results/stage20_development
python experiments/stage20/audit_stage20.py \
  --data results/stage17_data \
  --input results/stage20_development \
  --repeat-zero-replay results/stage20_smoke
```
