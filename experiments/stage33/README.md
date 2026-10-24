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

## Offline rater packets

The optional [collection kit builder](build_collection_kit.py) presents the
same frozen assignment as four private, single-file browser pages. This is a
pre-collection interface, not a change to the statistical protocol. It
checks the selected WMT25 candidate CSV against its recorded SHA256 before
producing the packets. Give volunteers only their own HTML file; the full
ZIP contains the researcher-only panel key. Obtain appropriate consent and
privately map R01 through R04 to four distinct English-Chinese bilingual
volunteers before distributing any pages.

```bash
printf 'rater_id\nR01\nR02\nR03\nR04\n' > results/stage33_raters.csv
python experiments/stage33/build_collection_kit.py \
  --items results/stage33_candidates/candidate_items.csv \
  --raters results/stage33_raters.csv \
  --output results/stage33_collection_kit
```

Open `results/stage33_collection_kit/START_HERE.txt` and send each volunteer
only `rater_packets/<their ID>.html`. The page works offline, displays
one task at a time in assigned order, records active task time, pauses when
the tab is hidden, permits tied ranks, and downloads `<ID>_responses.csv`
after 40 responses. A given browser stores progress locally when permitted;
ask volunteers to save and return the completed CSV privately. If storage
is blocked, they must keep the page open until completion. Log deviations,
interruptions, missingness, consent and recruitment outside the response
file. Never silently regenerate packets after one has been sent.

Once **real** completed CSVs are returned, put them in a private `responses/`
folder and merge, validate, then analyze:

```bash
python experiments/stage33/combine_responses.py \
  --template results/stage33_collection_kit/researcher_only/responses_template.csv \
  --responses results/stage33_collection_kit/responses/*.csv \
  --output results/stage33_collection_kit/researcher_only/responses.csv
python experiments/stage33/analyze_human_pilot.py \
  --key results/stage33_collection_kit/researcher_only/private_key.csv \
  --responses results/stage33_collection_kit/researcher_only/responses.csv \
  --output results/stage33_human_summary.json
python experiments/stage34_panel_randomization/exact_test.py \
  --key results/stage33_collection_kit/researcher_only/private_key.csv \
  --responses results/stage33_collection_kit/researcher_only/responses.csv \
  --output results/stage33_exact_result.json
```

Keep the source texts, assignment key, correspondence, and human response
CSVs out of the public repository. This pilot measures the chosen contrast;
it does not establish an ICML method contribution or measured gains from an
adaptive algorithm.

```bash
python -m unittest discover -s experiments/stage33 -p 'test_*.py' -v
```
