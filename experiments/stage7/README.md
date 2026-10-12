# SAFE-EVAL Stage 7: unchanged prediction methods on WMT23

This is a follow-up diagnostic after Stage 6's active extra-query policy failed
to save paid labels. It applies the unchanged Stage 5 inference engine to the
same WMT23 pools and matches Stage 6's raw query paths exactly. The verified
findings are in `FINDINGS.md`; this experiment is not a new method.

## Run on your Mac

Unzip `SAFE_EVAL_Stage7_Code.zip` in Downloads. Run each line separately in your
existing activated Python environment:

```bash
cd ~/Downloads/SAFE_EVAL_Stage7_v1
```

```bash
python -m unittest -v test_stage3.py test_binary_control.py test_stage5.py test_stage7.py
```

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_stage7.py --repeats 100 --workers 2 --output results_local
```

```bash
python analyze_stage7.py --input results_local
```

Expect **28 passing tests**, 117 printed cases and **117,000 method trajectories**.
The analysis checks **35,100 reserved stopping bounds**, all full saved
confidence-sequence paths and **11,700 paired Stage 6 raw stops**. Allow a few
minutes for the run and analysis; no GPU or raw-data download is needed.
Python 3.9+ grammar is supported. NumPy and Matplotlib are the dependencies.
If needed, install them in the current environment with
`python -m pip install -r requirements.txt`.

Expected analysis completion:

```text
Checked 117000 saved decisions and 35100 reserved stopping bounds; audited 117 case bundles of full confidence-sequence curves and 11700 Stage 6 paired raw stops; wrote comparison tables and figures.
```

The package is standalone: it contains the numeric data, Stage 6 comparator
rows and all required statistical modules. Your previous Stage 5/6 folders
and local results do not need to be moved or modified.

## Fixed comparison

| Method | Role | Nominal anytime confidence |
| --- | --- | ---: |
| published_ppr95 | Published binary raw baseline | 95% |
| legacy_trust201 | Original Stage 2 trust process, legacy 201-point inversion | 95% |
| prediction_count_grid | Stage 5 standalone prediction process | 95% |
| reserve_mix75 | Primary Stage 5 mixture, fixed 75% raw-capital reserve | 95% |
| legacy_gate201 | Original Stage 3 gate diagnostic | 95% |
| reserve_mix50 / reserve_mix90 | Prespecified reserve-weight diagnostics | 95% |
| ppr_reserve50 | Raw control for the 50% reserve guarantee | 97.5% |
| ppr_reserve75 | Raw control for the 75% reserve guarantee | 96.25% |
| ppr_reserve90 | Raw control for the 90% reserve guarantee | 95.5% |

The existing Stage 6 active10 and random10 stopping costs are also compared
on the matched 100-repeat paths. These have nominal 95% anytime confidence.
Different repeat counts run as small diagnostics, but omit Stage 6 pairing:
the vectorized random stream depends on the repeat count. Keep `--repeats 100`
for the full fixed comparison.

Stage 5's SVD/ridge, trust updates, stakes, gates, grids, confidence thresholds
and mixture weights are unchanged. Their source hashes are recorded in
`PARENT_RECORDS.json`, with the new adapter/protocol hashes in
`PROTOCOL_LOCK.json`. Features are recomputed using each target-excluded WMT23
background bank; this is the same algorithm, not a trained WMT24 model carried
across different sentences. Online target updates use previous query labels.

Every Stage 7 method queries uniformly without replacement. The predictor
changes statistical capital and intervals; it does not choose query indices.
Stage 6's active policies used additional historically ranked/random queries.
The comparison therefore changes both the predictor and statistical treatment;
it cannot isolate either ingredient's causal contribution.

The primary mixture's formal stopping bound remains against **raw 96.25%**,
not ordinary raw 95%. Stage 6's 10% paid-query cap does not apply to Stage 5
methods. See `STAGE5_THEORY.md`. Fixed-weight mixtures and confidence sequences
are existing tools; this diagnostic does not establish ICML novelty.

## Data and scope

Data are the **unchanged Stage 6 WMT23** extracts: 12 systems x 154 common
segments for en-de, 12 x 820 for he-en, and 15 x 589 for zh-en. Every target row
is excluded before features or history transformations are constructed.
Aligned, permuted and reversed histories give 117 cases from 39 target rows.
The latter two are synthetic stresses on recorded outcomes, not observed
natural shifts. No provider/family holdout is claimed.

The target is the unweighted fixed-pool mean of a derived recorded-human binary
error-free indicator. It is not official severity-weighted MQM, latent true
human quality or a future sentence-population mean. Quality-control segments
with HOTW-test injections, canaries and reference/human outputs are excluded.
Source issues and neutral opinions do not count as translation errors.
All retained system/segment ratings in these extracts have one rater.

WMT23 was new to Stages 1–5, but **was inspected in Stage 6**. Stage 7 is a
diagnostic on already examined data. Newly tuned policies would require a
separate untouched public release for later confirmation. Repeats measure
query randomization on fixed pools; they do not create independent new systems.
No private Hayden/Carey data or unpublished findings are used.

## Audit and outputs

`results_local` includes per-trial decisions, target and scenario summaries,
comparison tables, two PNG figures and `VERIFICATION.json`. The `curves/`
folder contains full saved interval paths and query indices. Integer count
endpoints are stored losslessly; legacy intervals retain their original floats.
The simulation continues to full evaluation after saving each first stop.
Stopping costs use only that prefix; full-path coverage failures are retained.

The analyzer reconstructs every first nonempty precision stop from the curves,
checks its endpoints, midpoint error and simultaneous coverage, independently
replays original-grid raw PPR at all four confidence levels, checks reserve
containment throughout each saved path and verifies the Stage 6 paired stops.
Both printed means and all saved aggregates are checked against path records.

Empty confidence sets can have different inverted endpoint representations.
The raw audit requires identical nonempty flags and exact nonempty endpoints;
both-empty cases remain coverage failures. The original endpoint-comparison
error, regression fix and presentation-only figure change are recorded in the
protocol/research record. Neither changed the inference engine or results.

Shared predictor strength and gate values are diagnostics evaluated at each
method's stop. The raw controls do **not** use those predictions or gates.

The compact `results_reference` folder includes verified aggregate tables,
figures and the audit record. Large per-trial decisions and curves are omitted
from the ZIP and regenerated by your run. Analyze your `results_local`, not
the trimmed reference folder. Case printing order may vary with worker timing.
