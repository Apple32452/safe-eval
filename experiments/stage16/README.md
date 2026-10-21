# Stage 16

The protocol freezes an external validation of the Stage 15 frontier rule on
WMT25 before the complete human-evaluation JSONL is downloaded or parsed.
Implementation and source hashes will be committed before inspecting results.

After obtaining the exact frozen upstream JSONL, run:

```bash
python experiments/stage16/prepare_wmt25.py \
  --source external/wmt25/wmt25-genmt-humeval.jsonl \
  --output results/stage16_data
python experiments/stage16/run_stage16.py \
  --data results/stage16_data \
  --repeats 50 \
  --output results/stage16_external
python experiments/stage16/summarize_stage16.py \
  --input results/stage16_external
```

The parser rejects any source whose byte count or SHA256 differs from the
precommitted WMT25 Git LFS object. `SUMMARY.json` reports the complete frozen
external gate, including losses at every budget.
