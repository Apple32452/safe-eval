# Stage 33: public panel overlap and human validation preparation

This follows [Stage 32's synthetic diagnostic](../stage32/README.md).
The [WMT11 audit](FINDINGS.md) has enough repeated pair/input
observations for a retrospective diagnostic, but its reference-presence
association has an interval spanning zero. Different raters' opposite
preferences are not evidence of a caused panel effect.

The [prospective protocol](PROTOCOL.md) prepares a development-only
40-document, 160-task English to Chinese feasibility pilot.
The [candidate manifest](results_reference/candidate_manifest.json)
specifies systems, seed and source hash. Candidate texts and private
rater assignments are generated locally and not committed.

## Reproduce the historical audit

From the repository root:

```bash
mkdir -p results/stage33_inputs
curl -L https://raw.githubusercontent.com/alopez/wmt-ranking/master/raw_data/wmt11/wmt11-maneval-indivsystems.RNK_results.csv \
  -o results/stage33_inputs/wmt11_indivsystems.csv
python experiments/stage33/audit_legacy_panels.py \
  --input results/stage33_inputs/wmt11_indivsystems.csv \
  --output results/stage33_legacy.json
```

Expected upstream Git blob SHA:
`3cc09d886b26706b44b3a18564a5878dfbc9abc8`.
The committed [summary](results_reference/wmt11_indivsystems_audit.json)
uses the full 7,842-ranking archive. No historical raw rankings are
copied into SAFE-EVAL.

## Prepare blinded tasks when raters are available

The WMT25 human-evaluation JSONL is a separate public download; see
[Stage 16 provenance](../stage16/DATA_PROVENANCE.json). Once the
128,674,273-byte file with SHA256
`a36ebce10c9ea26f71449933721de3a87e27f6a5b09d96b5daa026eaf1d197ab`
is available locally:

```bash
python experiments/stage33/extract_wmt25_candidates.py \
  --source external/wmt25/wmt25-genmt-humeval.jsonl \
  --output results/stage33_candidates
```

Create `results/stage33_raters.csv` from the
[template](raters_TEMPLATE.csv), with unique **pseudonymous** IDs
for at least four English and Chinese bilingual raters. A larger pool
is preferable. Keep names and contact details out of the repository.

```bash
python experiments/stage33/prepare_human_pilot.py \
  --items results/stage33_candidates/candidate_items.csv \
  --raters results/stage33_raters.csv --repeats 2 \
  --output results/stage33_tasks
```

Give each rater only their rows of `tasks.csv` and keep
`private_key.csv` hidden. The visible task IDs do not encode companion
contexts. Each rater's rows are sorted by the randomized `task_order`
column; the annotation interface must present them in that order and
record any deviations. The `task_order` is recorded in both the task
file and the private key. Enter five ranks (ties permitted) and task
duration in `responses_template.csv`. The analyzer runs only after all
tasks have responses:

```bash
python experiments/stage33/analyze_human_pilot.py \
  --key results/stage33_tasks/private_key.csv \
  --responses results/stage33_tasks/responses_template.csv \
  --output results/stage33_human_summary.json
```

The CSVs are a task specification and audit trail; use an appropriate
annotation interface and consent process before recruiting. No new
human judgments have been collected.
The [pre-collection handoff amendment](AMENDMENT_ORDER.md) records a
correction to the task presentation and blinding fields; the selected
documents, panel composition, and statistical contrast did not change.

```bash
python -m unittest discover -s experiments/stage33 -p 'test_*.py' -v
```
