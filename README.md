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
```

Expect **28 passing tests**. The code uses NumPy and Matplotlib; no GPU is
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
- The formal stopping bound is against the stricter **96.25% raw control**.
  It does not guarantee lower cost than the ordinary 95% raw control.
- All Stage 7 queries are uniform without replacement. Prediction changes
  inference, not acquisition. ICML novelty remains unresolved.
- The next important ablation is a matched zero-trust count-grid control.
  It is a proposed next step, not implemented in this snapshot.

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
The submitted Mac reproduction is documented in [MAC_VERIFICATION.md](docs/MAC_VERIFICATION.md).
