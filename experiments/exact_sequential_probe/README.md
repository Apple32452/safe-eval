# Sequential exact-factor development screen

**Status:** prespecified two-system synthetic screen; expansion gate **failed**.
The resulting method is valid for this fixed binary pool under its randomized
acquisition design, but this is not an ICML novelty claim.

For the positive comparison, the null is the fixed-pool total difference
`T = sum_i(A_i - B_i) <= 0`; for the negative direction it is `T >= 0`.
At each history, the acquisition design chooses uniformly among items with
an unpurchased endpoint. It buys A if unseen; when both endpoints are unseen
it buys B with predictable probability `q`; when only B is unseen, B is
bought with certainty. Purchased cells are cached. The factor is grouped
by the observed values and cache state. For every full binary completion
consistent with prior purchases and the appropriate null, a dynamic program
maximizes the next factor's exact expectation under the randomized purchase.
A cutting-plane optimizer chooses a factor under these null constraints and
checks the worst completion before each purchase. A solver failure returns
the unit factor, which cannot create evidence. Optional stopping uses a
two-sided threshold of `2/alpha`; logical bounds or full exposure also
resolve a pair exactly. The conditional expectation check does not assume
that the supplied predictive probabilities are correct.

The 10-repeat development screen was locked in [PROTOCOL.md](PROTOCOL.md).
Predictions in the two aligned synthetic scenarios equal their generating
base rates, an intentionally favorable setup. They were not fitted on
target scores, but neither were they learned from a separate historical
dataset. The shifted scenario tests a mismatched `.90/.10` positive
alternative against a `.30/.70` target; the negative alternative is
deliberately sign-flipped to `.10/.90` and remains misspecified. The matched
Stage 22 control uses the full-block method's item order.

| Fixed target scenario | Exact full, `q=1` | Partial `q=.75` | Partial `q=.5` | Stage 22 |
| --- | ---: | ---: | ---: | ---: |
| Aligned strong | 11.8 | 11.3 | 11.0 | 18.6 |
| Aligned moderate | 29.6 | 29.4 | 27.6 | 36.0 |
| Shifted opposite sign | 24.2 | 29.1 | 22.7 | 30.4 |

Values are mean **purchased system–item judgments**, out of 64 available,
over ten paired fixed matrices. Against exact full blocks, `q=.5` saved
6.78% and 6.76% in the two aligned scenarios. The descriptive paired
bootstrap intervals for its cost difference were `[-2.0, 0.6]` and
`[-7.5, 4.1]` judgments; both include zero. `q=.75` cost 20.25% more than
full blocks in the shifted scenario. Both candidates failed the locked gate
of at least 10% saving against **both** exact full blocks and Stage 22 in
both aligned scenarios, with no more than 10% shifted regression. There
were no wrong completed signs and no optimizer fallbacks in these saved
paths. Correctness of a small pilot is not an empirical coverage proof; the
conditional e-factor construction gives the validity claim.

The difference against Stage 22 alone does not establish a partial-block
contribution: the exact full-block method already costs fewer labels in
these favorable synthetic settings. The current method covers two binary
systems with homogeneous predictive probabilities. It has no adaptive
shared graph, no realistic historical fit, and no WMT25 comparison. WMT24
remains reserved. Growth-optimal e-variables and conditional RIPr factors
were established before this pilot in
[Safe Testing](https://arxiv.org/abs/1906.07801) and
[Hsu and Shekhar (2026)](https://arxiv.org/abs/2607.17409). Shared-item
rank confidence sequences also provide relevant prior art:
[Rank Confidence Sequences (2026)](https://arxiv.org/abs/2609.32211).

The remaining scientific question is whether a **shared, adaptive
multi-system design** can show a reproducible purchased-judgment saving
against its own strong, prediction-aware full-block control while retaining
simultaneous finite-pool validity. These results do not justify claiming it.

From the repository root:

```bash
python -m pip install -r experiments/exact_sequential_probe/requirements.txt
python -m unittest discover -s experiments/exact_sequential_probe -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python \
  experiments/exact_sequential_probe/sequential_probe.py \
  --repeats 10 --items 32 \
  --output experiments/exact_sequential_probe/results_reference.json
python experiments/exact_sequential_probe/audit.py \
  --input experiments/exact_sequential_probe/results_reference.json
```
