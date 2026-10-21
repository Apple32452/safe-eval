# Stage 22: graph-aware safe evaluation

Stage 22 is a precommitted WMT25 development test of the Stage 20 pruning
theorem on sparse requested-comparison graphs. The primary task compares every
candidate system with one reference system and averages over every possible
reference. The strong control evaluates all systems on the same common item
stream; the candidate skips a system only after all of its requested incident
edges have resolved.

The protocol and related-work boundary were committed before implementation or
Stage 22 outcome computation. WMT24 remains untouched.

After the implementation lock is committed, reproduce from the repository
root with:

```bash
python -m unittest discover -s experiments/stage22 -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage22/run_stage22.py \
  --data results/stage17_data --repeats 50 --output results/stage22_development
python experiments/stage22/summarize_stage22.py --input results/stage22_development
python experiments/stage22/audit_stage22.py --input results/stage22_development \
  --data results/stage17_data
```

