# Population-informed panel allocation: proxy headroom, not a method win

The protocol was published on `main` at `700338a2` before the new ledgers
were generated. The numerical amendment and implementation were published
before the full 100-repeat run. Three local tests passed. The independent
audit regenerated all **300** matrices, checked every saved proposal and
proxy, reproduced the bootstrap summaries, and passed. There were two
feasible, SciPy-reported successful solver starts on every matrix.

| Synthetic scenario | Mean proxy, uniform | Mean proxy, all-pair control | Mean proxy, population-informed proposal | Mean paired headroom vs all-pair | 95% bootstrap interval for ratio of mean proxies |
| --- | ---: | ---: | ---: | ---: | ---: |
| No context shift | 216.56 | 215.75 | 157.54 | 23.83% | 26.33%–27.48% |
| Context shift | 401.48 | 403.40 | 314.53 | 21.26% | 20.31%–23.67% |
| Context shift and unequal duration | 789.90 | 774.40 | 628.32 | 18.80% | 16.60%–21.27% |

The paired headroom column averages each matrix's fractional reduction;
the interval estimates a **different statistic**, the reduction in the
ratio of the mean proxies. In context shift and unequal duration those
ratios of means are 22.03% and 18.86%, respectively. Both shifted scenarios
exceed the frozen 10% *resource-prioritization* screen. The full-population
proposal's proxy was lower than the all-pair control on all 100 matrices in
each scenario. The proxy is a target-gap-scaled centered variance multiplied
by expected task duration; it is dimensionless after division by the squared
gap. Its absolute value is **not a count of human judgments or minutes**.

The proposal is built using every future simulated outcome and is therefore
unavailable in an actual sequential study. The proxy omits the finite-time
range terms in the real e-process, depletion, pilot costs, and the stopping
condition. This experiment shows headroom in an infeasible proxy allocation,
**not** an observed reduction in purchased labels, guaranteed lower cost,
or a new theorem. The optimizer returned feasible best-found values but no
formal certificate of global numerical optimality. No human ratings,
measured durations, WMT25, or WMT24 results were used.

The next frozen experiment should purchase panels using only past
observations, retain the same finite-pool inference and 15-pair completion
rule, and report **correct completed conclusions per task and simulated
duration** on fresh matched trajectories. It must compare against uniform
centered and the original adaptive all-pair method, with the same target,
familywise error budget, and costs. A positive feasible result would still
need a contribution beyond known target-aware pooled allocation (e.g.,
[Hait 2026](https://arxiv.org/abs/2609.37873)), plus prospective human
panel effects and cost evidence, before an ICML novelty claim is justified.

Reproduce from the repository root:

```bash
python -m pip install -r experiments/panel_oracle_gap/requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest -v experiments/panel_oracle_gap/test_panel_oracle_gap.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/panel_oracle_gap/run_probe.py --repeats 100 --output results/panel_oracle_full
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/panel_oracle_gap/audit.py --input results/panel_oracle_full
```
