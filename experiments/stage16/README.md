# Stage 16

The protocol froze an external validation of the Stage 15 frontier rule on
WMT25 before the complete human-evaluation JSONL was downloaded or parsed.
Implementation and source hashes were committed before inspecting results.
The first parse produced no output because the file contained the documented
`undecided` severity; `AMENDMENT_1.md` records the result-blind schema fix.

The external gate passed. At the primary 75% unique-label budget,
`frontier_evidence` gained 76.76 correctly certified pairs over
`evidence_first` (conditional MCSE 5.44), won 49/50 matched blocks, and had a
positive mean in all 14 included languages. See `FINDINGS.md` and the complete
compact `results_reference` package.

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

To verify the committed result grid without downloading WMT25:

```bash
python experiments/stage16/summarize_stage16.py \
  --input experiments/stage16/results_reference
```

With locally prepared data, the stronger audit also checks source and matrix
hashes and can compare a separately generated one-repeat replay:

```bash
python experiments/stage16/audit_stage16.py \
  --data results/stage16_data \
  --input results/stage16_external \
  --repeat-zero-replay results/stage16_smoke
```
