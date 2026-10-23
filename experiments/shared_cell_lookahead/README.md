# Three-system cell lookahead: negative diagnostic

This is the [frozen development protocol](PROTOCOL.md) for buying individual
binary system--item judgments to settle a fixed set of comparison signs.
One reference-system judgment can help both star edges. Every policy uses
the same logically exact completion-based certificate, so all declared signs
hold for every compatible hidden-score completion. The predictive Bernoulli
probabilities are used **only** to choose purchases and weight the exhaustive
synthetic matrices, not to make a sign valid.

The table gives exact expected unique purchased judgments over all 512
possible three-system, three-item binary matrices in each setting. Lower is
better. `pruned_blocks` follows the Stage 22 acquisition *pattern* under the
same logical certificate; it does not implement the Stage 22 e-process.

| Setting, requested graph | Lookahead | One-step greedy | Pruned item blocks | All-system item blocks | Lookahead savings vs greedy |
| --- | ---: | ---: | ---: | ---: | ---: |
| Easy, reference star | 6.4448 | 6.4458 | 7.9748 | 8.5079 | 0.016% |
| Moderate, reference star | 7.7126 | 7.7126 | 8.6427 | 8.8798 | 0% |
| Heterogeneous, reference star | 7.2567 | 7.2589 | 8.4637 | 8.7657 | 0.030% |
| Shifted, reference star | 6.4448 | 7.1738 | 7.9748 | 8.5079 | 10.162% |
| Easy, complete triangle | 8.0004 | 8.3621 | 8.6679 | 9.0000 | 4.325% |
| Moderate, complete triangle | 8.4513 | 8.6295 | 8.8780 | 9.0000 | 2.065% |
| Heterogeneous, complete triangle | 8.2655 | 8.5618 | 8.8454 | 9.0000 | 3.460% |
| Shifted, complete triangle | 8.0004 | 8.0998 | 8.6679 | 9.0000 | 1.226% |

The prespecified diagnostic gate **failed**: the oracle-like lookahead rule
did not save 10% against the one-step greedy rule in either primary aligned
setting. In the easy star, a reachable state causes the two policies to buy
different next cells, but the resulting root cost difference is only 0.001
judgments. In the moderate star, their exact expected costs coincide. Savings
against complete item blocks largely reflect the ability to buy one cell at
a time, which previous SAFE-EVAL branches already explored; they are not a
new publication claim.

The independent audit checked **16,384 complete acquisition paths** and
**27,448 compatible hidden-score completions**. It found no wrong signs or
repeat purchases. The expectations are exact *under the chosen product
Bernoulli design*. They do not imply a general efficiency guarantee, nor do
they validate historical predictions, correlated human judgments, the
Stage 36 e-factor, or real WMT data. The Stage 22 comparison here shares a
purchase pattern and logical certificate, not its 95% e-process; no direct
cross-method significance claim is justified.

Run from the repository root with Python 3.9 or later:

```bash
python -m unittest discover -s experiments/shared_cell_lookahead -p 'test_*.py' -v
python experiments/shared_cell_lookahead/diagnostic.py \
  --output experiments/shared_cell_lookahead/results_reference.json.gz
python experiments/shared_cell_lookahead/audit.py \
  --input experiments/shared_cell_lookahead/results_reference.json.gz \
  --output experiments/shared_cell_lookahead/audit_reference.json
```

The complete weighted matrix-level ledgers are saved in
[`results_reference.json.gz`](results_reference.json.gz), with a concise independent
check in [`audit_reference.json`](audit_reference.json).
