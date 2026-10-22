# Stage 32 findings: synthetic panel-context diagnostic

The reference run uses the parameters frozen in [PROTOCOL.md](PROTOCOL.md):
500 synthetic repeats, at most 2,000 five-way tasks per method, target
`pi(G)=0.25`, `pi(B)=0.75`, and a target A/B signed mean `Delta=-0.4`.
Thus **B is the target winner**. A wins 90% of G judgments but only 10% of
B judgments. The adaptive selector disproportionately shows G. Methods
share random-number ledgers within each repeat and each judge is fresh in
the simulation.

| Method | Wrong A declarations | Correct B declarations | Abstentions | Mean capped tasks | Mean tasks when correct | Observed G share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Target-randomized, raw | 0/500 | 500/500 | 0/500 | 52.306 | 52.306 | 0.2493 |
| Adaptive, naive raw | 500/500 | 0/500 | 0/500 | 23.296 | n/a | 0.8801 |
| Same adaptive policy, IPW | 0/500 | 500/500 | 0/500 | 221.984 | 221.984 | 0.8805 |

The exact conditional naive mean is `+0.64` when its G propensity is 0.9
and `+0.48` when it is 0.8, even though the target mean is `-0.4`.
Propensity weighting restores a conditional mean of `-0.4` at both
propensities. The naive policy makes a confident **wrong-target** declaration
under this deliberately extreme, specified context effect; its low task
count is failure, not efficiency. Correction uses about 4.24 times as many
tasks as target randomization here. The bound becomes costly because a
rare B panel can receive a weight up to 7.5. No method abstained at this
cap. The 0/500 observed errors for the two valid methods are descriptive;
their anytime error claims rely on the stated conditional-mean assumptions
and established e-process reasoning.

This demonstrates a **boundary of the Stage 31 guarantee**: if companion
translations change the A/B preference, a context-invariant target cannot
be inferred merely from the selected panels. It does **not** establish that
real humans show this effect, that the chosen effect size is realistic, that
IPW is optimal, or that the statistical correction is novel. Active MT
evaluation and subset ranking already have established literature, as does
anytime-valid off-policy inference. The useful next experiment is the
randomized human study in [ANNOTATION_PROTOCOL.md](ANNOTATION_PROTOCOL.md),
followed by a cost-matched comparison on untouched external data.

Reproduce from the repository root:

```bash
python -m unittest discover -s experiments/stage32 -p 'test_*.py' -v
python experiments/stage32/run_context_panels.py --repeats 500 --cap 2000 \
  --output experiments/stage32/results_reference
```

The JSON summary and per-repeat CSV are in `results_reference/`.
