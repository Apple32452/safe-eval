# Stage 28: coupled queries and variance-adaptive betting gate

This is a frozen **synthetic baseline experiment**, not a claim of a novel
ICML method. Its question is whether querying two candidate systems on the
same prospectively sampled item–rater pairs and adapting the betting stake
to past outcomes saves human judgments over paired labeling. It extends the
explicit prospective target in [Stage 27](../stage27/README.md); WMT24 is
untouched, and WMT25's retrospectively assigned rater IDs do not establish
this prospective target.

## Target, costs, and stopping

There are three fixed systems with binary potential scores `Y_s(i,r)`.
For each of the three predeclared unordered edges `(a,b)`, the target is
the sign of `Delta_ab = E[Y_a(I,R)-Y_b(I,R)]`. On every round a new item and
rater are drawn independently and uniformly from 32 synthetic items and
six synthetic raters; all systems on that round share that pair. The
protocol charges one **fresh blinded system–item–rater judgment** per queried
score, even if an index recurs. No earlier judgment is cached. This artificial
cost definition is a limitation of the sanity check.

All methods use the same item/rater ledger in each repeat, all three edges,
the same alpha `0.05`, and the same 1,600-round cap. Each direction on each
edge has a separate e-process and a crossing threshold of
`2 * 3 / 0.05 = 120`. A run is complete only after every pairwise sign is
certified. It is unresolved at the cap if any edge remains; fewer labels on
an unresolved run are **not** counted as a low-cost conclusion. The paired
control may stop buying the reference if only the candidate–candidate edge
remains active; its costs are charged per actually obtained label.

## Frozen methods

| Method | Query design | Betting rule |
| --- | --- | --- |
| `paired_fixed` | All scores required by active edges | Fixed mixture |
| `paired_adaptive` | Same | Fixed mixture plus predictable regularized stake |
| `independent_fixed` | Independent candidate coins, each `q=0.75` | Fixed mixture |
| `coupled_fixed` | One shared candidate coin, each `q=0.75` | Fixed mixture |
| `independent_adaptive` | Independent coins, each `q=0.75` | Fixed mixture plus predictable stake |
| `coupled_adaptive` | Shared coin, each `q=0.75` | Fixed mixture plus predictable stake |
| `coupled_allocation` | Shared coin; past residual root-mean-square sets candidate/stratum propensities with `q>=0.25` and history-estimated mean candidate propensity `0.75` | Fixed mixture plus predictable stake |

The candidates' predictions are separate smoothed historical score means
for the observed reference-score strata. Both prediction and the **whole
table** of query probabilities are frozen *before drawing* the current
item/rater pair or reading its reference outcome. Only then do we read the
reference and draw query coins. The independence and coupled variants use
the same marginal fixed propensity, while the adaptive allocation variant
may change it using earlier purchased labels. The algorithm never reads an
unqueried candidate potential score. The simulator reads the full potential
outcome matrix only at the end to audit the true population signs.

## Estimator and validity

For candidates 1 and 2, let `m_j(A)` and `q_j(A)` be pre-draw tables,
`Z_j` the query indicator, and `B_j` a candidate score. Define

`T_j = m_j(A) + Z_j/q_j(A) * (B_j-m_j(A))`.

The three corrected signals are `G_01=A-T_1`, `G_02=A-T_2`,
and `G_12=T_1-T_2`. For each fixed drawn pair and all its potential
scores, `E[T_j | pair, historical state] = B_j`, regardless of the
dependence between `Z_1` and `Z_2`. The iid pair draw then gives
`E[G_ab | previous complete rounds] = Delta_ab`.

Before the current pair draw, the program computes finite lower and upper
bounds `-c^-_ab <= G_ab <= c^+_ab` by considering **both possible reference
scores**, all possible candidate scores in `[0,1]`, and query outcomes.
For a positive declaration, fixed stakes are `rho/c^-` with
`rho in {0.10,0.25,0.50,0.85}`; the reverse uses `rho/c^+`.
The adaptive component's stake is the positive historical signed sum divided
by historical squared outcomes plus `8*c^2`, clipped at `0.95/c`.
Each stake is computed before the pair draw, so under its directional null
`1+stake*(+/-G)` is a nonnegative conditional supermartingale factor.
Each component is a product of factors; the e-process is the equally
weighted **mixture of component products**. Ville's inequality and a union
bound over six directions yield familywise error at most 0.05, irrespective
of dependence between system scores on the same pair or between query coins
on the same round. This proof requires iid prospective pair draws, known
positive query probabilities and bounded binary scores. It does not apply
to an unrandomized fixed rater panel.

For equal candidate propensity `q`, the conditional contribution of query
randomness to the candidate–candidate signal has variance
`(1/q-1)*(r_1-r_2)^2` for a common coin versus
`(1/q-1)*(r_1^2+r_2^2)` for independent coins, where `r_j=B_j-m_j(A)`.
Coupling is beneficial for same-sign residuals and harmful for opposing
residuals. It does not change either query's marginal expected cost.

## Predeclared experiment and gate

The scenarios are aligned, weak, reversed, opposing candidate residuals,
and exact ties. We run 100 independent seeded ledgers per scenario. This
pilot passes its **cost gate** only if one joint method completes at least
as often as both paired controls in *every* non-tie scenario and is cheaper
in mean label cost to stopping in at least three of four non-tie scenarios.
Even that would only warrant comparison against stronger published methods
and validation under an actual prospective annotation protocol; it would
not establish novelty.

The exact audit enumerates 5,392 score, prediction, probability and coin
settings and checks the correction and pre-draw bounds. It also checks a
tied population and the two residual covariance cases. See
[the findings](FINDINGS.md), [saved replicates](results_reference/REPLICATES.csv),
and [audit summary](results_reference/SUMMARY.json).

From the repository root:

```bash
python -m unittest discover -s experiments/stage28 -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage28/audit_stage28.py \
  --repeats 100 --rounds 1600 --output results/stage28_local
python experiments/stage28/analyze_stage28.py --input results/stage28_local
```

## Closest comparisons

- [Anytime-valid off-policy inference](https://arxiv.org/abs/2210.10768)
  already supplies variance-adaptive doubly robust confidence sequences.
- [Dynamically Allocating Evaluation Effort for Model Ranking](https://arxiv.org/abs/2608.03437)
  already studies correlated models and adaptive human evaluation.
- [Rank Confidence Sequences](https://arxiv.org/abs/2609.32211)
  and [BB-EDGE](https://arxiv.org/abs/2609.32248) already provide anytime
  rankings or pairwise edge guarantees under shared observations.

This pilot uses none of their full algorithms. Even if its own controls
were beaten, it could not establish superiority to the published methods.
