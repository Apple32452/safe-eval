# SAFE-EVAL

Research prototype for prediction-assisted evaluation of a fixed benchmark
with anytime-valid confidence sequences. The goal is to reduce target-label
queries while measuring the cost of unreliable historical predictions.

This repository starts from the **released Stage 7 snapshot**. Its statistical
code, data, protocol locks, audit records and reference results are preserved
byte for byte under [`experiments/stage7`](experiments/stage7/README.md).
Repository setup and automated checks are additions around that snapshot.

## Set up on your Mac

From this repository's root, using your existing activated environment:

```bash
python -m pip install -r requirements.txt
python scripts/check_release.py
python -m unittest discover -s experiments/stage7 -p 'test_*.py' -v
python -m unittest discover -s experiments/stage8 -p 'test_*.py' -v
python -m unittest discover -s experiments/stage9 -p 'test_*.py' -v
python -m unittest discover -s experiments/stage10 -p 'test_*.py' -v
python -m unittest discover -s experiments/stage16 -p 'test_*.py' -v
python -m unittest discover -s experiments/stage17 -p 'test_*.py' -v
```

Expect **87 passing tests in total** (28 Stage 7, seven Stage 8, eight Stage 9,
six each for Stages 10, 11, 12 and 13, four Stage 14 tests, and five Stage 15
tests, plus six Stage 16 and five Stage 17 tests). Also run
`python -m unittest discover -s experiments/stage11 -p 'test_*.py' -v` and
`python -m unittest discover -s experiments/stage12 -p 'test_*.py' -v`, followed by
`python -m unittest discover -s experiments/stage13 -p 'test_*.py' -v` and
`python -m unittest discover -s experiments/stage14 -p 'test_*.py' -v`, then
`python -m unittest discover -s experiments/stage15 -p 'test_*.py' -v` and
`python -m unittest discover -s experiments/stage16 -p 'test_*.py' -v`, then
`python -m unittest discover -s experiments/stage17 -p 'test_*.py' -v`.
The code uses NumPy and Matplotlib; no GPU is
required. Python 3.9 syntax is supported. This repository preparation was
tested locally with Python 3.12; the GitHub workflow is configured to check
Python 3.9 and 3.12 on Ubuntu and Python 3.12 on macOS.

## Reproduce the fixed Stage 7 comparison

Run each command after the previous one finishes:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage7/run_stage7.py --repeats 100 --workers 2 --output results/stage7_local
python experiments/stage7/analyze_stage7.py --input results/stage7_local
```

The complete run saves 117,000 method trajectories. Analysis checks 35,100
reserved stopping bounds and matches 11,700 Stage 6 raw stops. Full saved
curves and per-trial data are generated locally rather than committed.

For a smaller installation check:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage7/run_stage7.py --repeats 1 --workers 2 --output results/stage7_smoke
python experiments/stage7/analyze_stage7.py --input results/stage7_smoke
```

The one-repeat run is a software check. It does not reproduce the fixed
100-repeat Stage 6 pairing or supply new research evidence.

## Current research status

- Stage 6's primary extra-query policy increased paid query cost overall.
- Stage 7's unchanged 75% raw-capital reserve reduced aligned-history mean
  query cost by 7.428% with equal weighting of the three languages. German
  cost increased by 0.871%; Hebrew and Chinese costs fell by 9.121% and 8.577%.
- Stage 7/8's reserve stopping bound is against the stricter **96.25% raw
  control**. That reserve construction does not guarantee lower cost than
  the ordinary 95% raw control.
- All Stage 7 queries are uniform without replacement. Prediction changes
  inference, not acquisition. ICML novelty remains unresolved.
- Stage 8's matched zero-trust ablation is complete: enabling aligned history
  reduces reserve query cost by 6.815% versus the otherwise matched control.
  The reversed-history primary instead adds 0.075% on average. See the
  [Stage 8 findings](experiments/stage8/FINDINGS.md) and fixed
  [protocol](experiments/stage8/PROTOCOL.md).
- Stage 9 supplies a separate ordinary-raw95 stopping safeguard using exact
  finite-state calibration and error allocation. Its fixed aligned comparison
  saves 2.801% versus raw95, 2.798% versus matched zero, and 1.141% versus
  integer-grid calibrated raw95. German and both adverse-history conditions
  lose to calibration. See the [Stage 9 findings](experiments/stage9/FINDINGS.md).
- Stage 10's finer calibrated control reduces the aligned prediction advantage
  to 0.666%, or 1.813 labels per benchmark. Prediction improves 18 target means
  and worsens 21; both adverse histories favor calibration. Larger-pool exact
  repair calibration remains unfinished. Stage 11 checks the remaining gain
  against published sequential boosting. See the [Stage 10 findings](experiments/stage10/FINDINGS.md).
- Stage 11 completes that published boosting comparison on the same PPR
  process. The aligned prediction gain shrinks to 0.341% (0.925 labels), with
  15 target mean wins and 24 losses. Both adverse histories favor boosting;
  the worst extra cost is 260 labels. See the [audited Stage 11 findings](experiments/stage11/FINDINGS.md).
- Stage 12 reviews the closest prior work and checks a finite-assignment
  boosting calculation with exact arithmetic. Substantial overlap blocks the
  broad novelty claims; the checked extension is not an established new
  method. A finite-pool label-cost guarantee remains an unresolved research
  target. See the [contribution audit](experiments/stage12/NOVELTY_AUDIT.md).
- Stage 13 studies a separate MT-facing objective: recovering fixed-benchmark
  pairwise system conclusions using fewer paired target judgments. All 237
  system pairs are included, with both targets excluded from history and
  separate per-pair and family-wide error settings. See the
  [locked protocol and reproduction commands](experiments/stage13/README.md).
  Its audited paired-PPR baseline uses 68.8614% of each pair's full budget on
  average under the family-wide setting, with no observed wrong decisions in
  11,850 query-order trials. Historical added value remains unestablished, and
  the reserve's family-wide component cap needs correction before efficiency
  conclusions. See the [Stage 13 findings](experiments/stage13/FINDINGS.md).
- Stage 14 is an exploratory shared-annotation scheduling pilot on the same
  WMT23 binary outcomes. At half of the unique-label budget, evidence priority
  certifies 28.25/237 pairs on average over 12 order blocks, versus 23.08 for
  fixed pair focus and 16.33 for random pair focus. Most pairs remain
  unresolved; the two concentration controls were added after the initial
  pilot. See the [Stage 14 findings and reproduction](experiments/stage14/README.md).
- Stage 15 tests a locked annotation-level frontier utility over 50 matched
  WMT23 order blocks. Its primary 50% gain over evidence-first is only 0.82
  certified pairs (conditional MC SE 0.664); at 75% the gain is 10.80 pairs.
  This is a development candidate, not an ICML contribution. See the
  [Stage 15 findings](experiments/stage15/FINDINGS.md).
- Stage 16 externally validates that unchanged scheduler on 14 WMT25 language
  directions and 2,197 system pairs. At the frozen 75% label budget it gains
  76.76 correctly certified pairs over evidence-first (conditional MCSE 5.44),
  wins 49/50 matched blocks, has positive means in all 14 languages, and has
  zero observed wrong declarations. The external gate passes. This supports
  the scheduling effect but does not yet supply the needed theorem, practical
  score margin, or matched active-ranking baselines. See the
  [Stage 16 findings](experiments/stage16/FINDINGS.md).
- Stage 17 tests a continuous WMT25 mean-score target and supplies the
  scheduler-independent validity and allocation formulation. At 75% labels,
  frontier evidence gains 12.82 correctly certified pairs over evidence first
  (MCSE 1.68), with zero observed wrong declarations and positive mean gains in
  11 of 14 languages. The frozen gate passes. The random-label control is
  structurally weak, so a common random test-set baseline is required before
  claiming an ICML contribution. See the
  [Stage 17 findings](experiments/stage17/FINDINGS.md).

See the complete [Stage 7 findings](experiments/stage7/FINDINGS.md),
[Stage 6 findings](experiments/stage7/STAGE6_FINDINGS.md),
[theory](experiments/stage7/STAGE5_THEORY.md) and
[next research question](experiments/stage7/NEXT_RESEARCH_QUESTION.md).

## Data and reference results

The bundled public WMT23 extracts contain recorded binary error-free scores
for three fixed annotated pools. This derived outcome is distinct from the
official severity-weighted MQM score. Synthetic permuted and reversed histories
are stress tests. The detailed filtering, upstream commit, hashes and source
license are in [data provenance](experiments/stage7/data/DATA_PROVENANCE.json)
and [the upstream license](experiments/stage7/UPSTREAM_LICENSE.txt).

The compact [reference results](experiments/stage7/results_reference) include
tables, figures and the completed audit. They omit full per-trial curves and
cannot be passed directly to the analyzer. No private Hayden/Carey data are
included.

## Working on GitHub

Follow [the setup instructions](docs/GITHUB_SETUP.md) to clone the working
repository and continue development. The workflow runs the release integrity check
and invariant tests on pushes and pull requests, plus one small end-to-end run
on Ubuntu/Python 3.12. Its configuration follows
[GitHub's Python workflow documentation](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).

Keep the released experiment intact. Put new research stages in a new
directory and record their own protocol and evidence before comparing results.
The default working branch is `main`; future changes can use branches and pull
requests. The working repository is [Apple32452/safe-eval](https://github.com/Apple32452/safe-eval).
The submitted Mac reproductions are documented for
[Stage 7](docs/MAC_VERIFICATION.md) and
[Stage 8](docs/STAGE8_MAC_VERIFICATION.md).

## Reproduce Stage 8

From the repository root:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage8/run_stage8.py --repeats 100 --workers 2 --output results/stage8_local
python experiments/stage8/analyze_stage8.py --input results/stage8_local
python experiments/stage8/report_details.py --input results/stage8_local
```

Use a new output directory for each run. Stage 8 imports the frozen Stage 7
modules and public data. Its reference tables and figure are included, while
large per-trial files and full curves are generated locally.

## Stage 9 ordinary raw95 safeguard

Stage 9 uses exact finite-state calibration to allocate spare raw error
probability to a prediction confidence sequence. The returned interval is
contained in unchanged raw95, with fallback equality when needed. This
supplies an ordinary-raw95 stopping bound under the stated uniform-sampling
and arithmetic assumptions. The fixed development comparison includes matched
zero-trust and calibrated raw controls. The aligned mean gain versus calibrated
raw is modest and uneven; no ICML novelty is established.

See the [instructions](experiments/stage9/README.md),
[protocol](experiments/stage9/PROTOCOL.md), [theory](experiments/stage9/THEORY.md)
and [findings](experiments/stage9/FINDINGS.md). Generate fresh certificates for
the runtime before reproducing the fixed comparison:

    python experiments/stage9/certify_stage9.py --output results/stage9_certificates
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage9/run_stage9.py --certificates results/stage9_certificates --repeats 100 --workers 2 --output results/stage9_local
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage9/analyze_stage9.py --certificates results/stage9_certificates --input results/stage9_local

The audit can take substantially longer than the run because it rebuilds
capital and raw PPR intervals from every query. It prints an `Audited ...`
line for each completed case. The committed compact reference package omits
the full curves required by the analyzer; see
[reference file details](experiments/stage9/REFERENCE_FILES.md).

## Stage 10 stronger-calibration and novelty study

Stage 10 preserves all Stage 9 prediction paths and adds a finer calibrated
PPR control, with an exact repaired-control investigation and a focused
primary-source novelty review. It reuses a complete audited 100-repeat Stage 9
run. Read the [Stage 10 instructions](experiments/stage10/README.md),
[protocol](experiments/stage10/PROTOCOL.md), [theory](experiments/stage10/THEORY.md)
and [novelty review](experiments/stage10/NOVELTY_REVIEW.md). Full source curves
are required; the compact archived summaries cannot replace them.
The [audited findings](experiments/stage10/FINDINGS.md) and
[reference package](experiments/stage10/results_reference) report the completed
comparison and its limits.

## Stage 11 published sequential-boosting baseline

Stage 11 applies Fischer and Ramdas's published sequential-boosting algorithm
to the same PPR process, with conservative integer updates and inversion of
every candidate total. It preserves the complete audited Stage 9/10 outputs.
See the [instructions](experiments/stage11/README.md),
[fixed protocol](experiments/stage11/PROTOCOL.md) and
[numerical argument](experiments/stage11/THEORY.md). This is a baseline study,
not a new method or an established novelty claim.
The [findings](experiments/stage11/FINDINGS.md) and
[reference results](experiments/stage11/results_reference) include the completed
audit, all paired comparisons, diagnostics and a figure.
