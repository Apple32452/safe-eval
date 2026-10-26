# Shared dual acquisition: negative matched-control screen

26 October 2026. The prespecified primary efficiency gate **failed**. A
dual allocation optimized for a shared one-step variance proxy did not beat
both same-inference acquisition controls. This remains an incremental
algorithmic experiment, not an ICML novelty or end-to-end cost theorem.

The [protocol](PROTOCOL.md) was committed before target generation and the
implementation before the full run. The [theory note](THEORY.md) derives the
convex one-step proxy and explains why it does not bound stopping cost. The
full run had 100 independent synthetic matrices (60 primary and two
20-case diagnostics); none used WMT or new human judgments.

## Primary: 60 aligned stratified matrices, 3 systems × 128 items

All methods use the same target matrix. The dual, row-peer, peer-cell and
approximate EC² methods share the stratum-conditioned predictor and inference.
Paired closure instead uses global historical marginals, and Stage 22 does
not use the historical bank or strata. Lower charged unique-label cost is
better. Wrong output would have cost 384; none was observed.

| Method | Mean charged labels | Candidate saving | Adjusted paired bootstrap interval |
| --- | ---: | ---: | ---: |
| Shared dual candidate | 227.20 | — | — |
| Matched row-uniform peer | 234.53 | 3.13% | [−3.48%, 9.23%] |
| Earlier peer-cell heuristic | 222.22 | −2.24% | [−8.06%, 3.37%] |
| Approximate 256-particle EC² acquisition | 241.18 | 5.80% | [0.92%, 10.53%] |
| Paired exact closure | 267.83 | 15.17% | [7.80%, 21.46%] |
| Stage 22 | 286.85 | 20.79% | [15.46%, 25.79%] |

The two closest same-inference controls determine the result. The row
comparison interval includes zero, and the previous cell policy has a
lower point cost. The EC² comparison is against our explicitly **approximate
particle acquisition**, not exact published EC² with its own stopping rule.
The paired-closure and Stage 22 contrasts change more than the acquisition
objective and cannot isolate the new rule's contribution. The intervals are approximate
case-sampling summaries, not the statistical validity guarantee.

## All diagnostics (20 matrices per row)

| Condition | Dual | Row peer | Peer cell | Approx. EC² | Paired closure | Stage 22 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Homogeneous strata | 127.10 | 118.75 | 121.35 | 125.65 | 145.15 | 158.55 |
| Reversed historical strata | 308.90 | 320.90 | 322.40 | 343.35 | 280.10 | 298.60 |

In the homogeneous diagnostic the candidate again loses to matched
row-uniform and peer-cell methods. In reversed history it beats those two
but loses to both shared-item controls. Neither diagnostic can replace the
failed prespecified primary. All 600 method trajectories had zero observed
wrong final conclusions; that count alone does not prove error control.

## Reproduce

From the repo root after installing NumPy and SciPy:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest discover -s experiments/dual_shared_acquisition -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/dual_shared_acquisition/experiment.py --workers 4 --output results/dual_shared_acquisition_20261026
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/dual_shared_acquisition/audit.py --workers 4 --input results/dual_shared_acquisition_20261026
```

The compact summary, metadata and audit are committed. Individual
query ledgers are generated in `cases.json.gz` by the run command and are
not committed here. The scripts refuse to overwrite an existing result
folder; use a fresh output path on rerun.

## Research decision

This is a second independent case in which a principled one-step objective
fails to deliver a reliable advantage over matched acquisition with the
same valid inference. Further tuning on these cases would not validate
novelty. The unresolved task is a credible guarantee on total stopping
cost, or a policy with a prespecified advantage over both matched controls
on an independent evaluation target. Existing active-testing and EC²
results must be accounted for in any such claim.
