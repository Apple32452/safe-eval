# Stage 17

Stage 17 develops the paper-facing formulation of anytime-valid shared-label
allocation and tests it on WMT25's recorded continuous human scores. Read the
protocol, theory record and closest-work boundary before running experiments.

WMT25 is development data in this stage. WMT24 is reserved for a later frozen
confirmation and must remain untouched while Stage 17 is developed.

After obtaining the exact Stage 16 WMT25 source file, run:

```bash
python experiments/stage17/prepare_scores.py \
  --source external/wmt25/wmt25-genmt-humeval.jsonl \
  --output results/stage17_data
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python experiments/stage17/run_stage17.py \
  --data results/stage17_data --repeats 50 \
  --output results/stage17_development
python experiments/stage17/summarize_stage17.py \
  --input results/stage17_development
python experiments/stage17/audit_stage17.py \
  --data results/stage17_data \
  --input results/stage17_development \
  --repeat-zero-replay results/stage17_smoke
```

The frozen development result, audit, and interpretation are stored in
`results_reference` and [FINDINGS.md](FINDINGS.md). The gate passed, but a
common random test-set baseline remains necessary before making an efficiency
or ICML contribution claim.
