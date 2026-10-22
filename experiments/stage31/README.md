# Stage 31 development pilot: Koehn-style five-system panels

This exploratory experiment follows the judgment unit in Philipp Koehn's
[2012 IWSLT paper](https://aclanthology.org/2012.iwslt-papers.5.pdf): rank
five translations of the same input and obtain ten **dependent** pairwise
outcomes. Its question is whether allocating those panels to unresolved
system pairs reduces the number of five-way judge tasks needed for a
simultaneously valid partial ranking. A panel is the cost unit; ten derived
pairwise outcomes are not ten independent human judgments or ten separately
priced judge tasks. The paper did not measure a universal panel-to-pair cost
conversion.

The synthetic model has 15 systems with independent translation qualities
`Normal(mu_j, sigma^2)` on each fresh input, `mu_j ~ Uniform(0,10)` and
`sigma^2 = 10`, following the central 2012 example. Each method sees the
same full (hidden) quality ledger and the same list of 16 candidate panels
per round. `uniform_panel` selects the first uniformly sampled panel;
`unresolved_panel` selects the candidate with the most as-yet-unresolved
edges, breaking ties by candidate order. Both select before seeing that
round's qualities. Only the five selected qualities are revealed.

For edge `(i,j)`, the observed outcome is `Y = +1` if `i` wins and `-1`
otherwise. Each preselected panel either includes this edge or leaves its
evidence unchanged. Conditional on the past and the panel, the included
outcome has mean `Delta_ij = E[Y]` under the independent fresh-input model.
For the null `Delta_ij <= 0`, `1 + rho*Y` is a nonnegative conditional
supermartingale factor for every fixed `rho` in `(0,1)`. Reverse the sign
for the opposite null. We average four predeclared wealth processes with
`rho = (0.10, 0.25, 0.50, 0.80)` and use threshold
`2 * choose(15,2) / 0.05 = 4200` per direction. Ville's inequality and a
union bound give at most 0.05 probability of **any false directional edge
at any time**, even with adaptive panel selection and arbitrary dependence
among the ten outcomes within a panel. Transitive rank ranges from certified
edges inherit that event. This is a straightforward application of existing
methods, **not a novel guarantee**.

The target is direct certification of at least 70% (74 of 105) unordered
pairs within 6,000 panels. We report completion, capped panel cost, direct
wrong declarations, and transitive rank-range widths. An uncompleted run
is censored at the cap; its cheaper cost is not counted as success. The
20-repeat default is a development screen, not a paper-level comparison.
The paper's 2012 judgment-count table used pairwise counts and per-pair
sign tests, so its numbers cannot be compared directly with our panel-task
counts and simultaneous familywise threshold.
Context effects from the other three translations, ties, correlated or
nonrandomly assigned raters, annotation time, and actual human judgments
are absent. If real judges change their preference with panel composition,
the conditional mean above changes and this guarantee does not directly
apply to a fixed pairwise target.

Related baselines that a future paper-level study must match include
[Active Evaluation (ACL 2022)](https://aclanthology.org/2022.acl-long.600/),
[active subset-wise ranking (AISTATS 2019)](https://proceedings.mlr.press/v89/saha19a.html),
[SERPANT (ICML 2026)](https://proceedings.mlr.press/v306/gu26l.html), and
[Rank Confidence Sequences (2026)](https://arxiv.org/abs/2609.32211).

From the repository root:

```bash
python -m unittest discover -s experiments/stage31 -p 'test_*.py' -v
python experiments/stage31/run_koehn_panels.py --repeats 20 --rounds 6000 \
  --output results/stage31_development
```

If this development screen fails, do not relabel panel allocation as a new
ICML contribution. If it succeeds, inspect the cited methods at the theorem
and cost-definition level, add actual five-way judgments and human time
costs, and freeze a matched external validation protocol before using any
held-out dataset.
