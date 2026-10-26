# Scalable individual-judgment study: findings

**Status (26 October 2026):** The implementation and frozen 190-case synthetic study are complete. The prespecified matched-efficiency gate failed. This is not an established ICML-level cost contribution or evidence of a general expected-cost guarantee.

## Research question

Can a predictable policy choose individual system–item judgments, share each judgment across active comparisons, and certify comparisons on a fixed finite test set at lower label cost than strong methods given the same inference machinery?

The code in this directory implements conditional null-calibrated factors, peer-score acquisition, and a binary-completion support calculation that avoids enumeration of every full outcome matrix. [Protocol](PROTOCOL.md) and [theory](THEORY.md) state the fixed design and validity assumptions. The conditional e-process validity result does **not** imply the missing comparative cost guarantee.

## Frozen study

There were 190 synthetic matrices with 1,460 trajectories, including primary one-hot reference stars and diagnostic independent, monotone, opposed, reversed-history, near-tie, and complete comparison settings. No new human judgments or WMT data were used. In the 50-case primary one-hot 3-system × 64-item reference-star setting:

| Method | Mean distinct labels |
| --- | ---: |
| Individual-cell peer acquisition | 84.28 |
| Matched random-item peer control | 85.20 |
| No-peer cell control | 86.84 |
| EC²-weighted control | 91.90 |
| Paired exact closure | 97.60 |
| Stage 22 | 107.76 |

The candidate saved **0.92 labels (1.08%)** against the closest matched random-item peer control. The multiplicity-adjusted paired bootstrap interval for relative saving was **−9.38% to +11.03%** and includes zero. Against Stage 22, the observed saving was **21.79%** with adjusted bootstrap interval **14.35% to 29.20%**. This latter comparison changes other parts of the pipeline; it cannot isolate a benefit from individual-item acquisition. These intervals are approximate empirical intervals, not a theorem about future data. Several diagnostics did not show a cost advantage.

The auditor replayed all 190 cases and 1,460 trajectories, checked 199,796 paid cells and 305,931 actual true-null conditional factors, and found zero observed wrong final decisions; its maximum checked conditional expectation was 1.0000000000000007 (numerical tolerance). Eight unit tests passed locally, and the implementation passed Ubuntu 3.9/3.12 and macOS 3.12 CI on commit 6d7a0242f95beac9aeb10fc254701f3135476089. Observed zero errors alone is not a general performance guarantee.

## Reproduce

From the repository root with NumPy and SciPy installed:

```bash
python -m unittest -v experiments/peer_cell_scale/test_engine.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/peer_cell_scale/study.py --workers 4 --output results/peer_cell_scale_full
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/peer_cell_scale/audit.py --workers 4 --input results/peer_cell_scale_full
```

The [summary](../../results/peer_cell_scale_full/summary.json), [audit](../../results/peer_cell_scale_full/audit.json), and [metadata](../../results/peer_cell_scale_full/metadata.json) are committed. The full per-case ledgers archive was generated locally but is not part of this commit; rerunning the frozen study regenerates it for audit. The fixed protocol hash is `0c50de2211726543975d2b0de9cb37f49c3c96af58c26e6f12e610424a968344`.

## Research conclusion

A scalable valid algorithm exists, but the strongest matched control erases the apparent acquisition advantage in this study. Next work needs either a proved comparative cost result under explicit assumptions or reproducible lower label cost than the matched control across larger settings and independent data.