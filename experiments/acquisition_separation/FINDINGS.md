# A certified tiny acquisition advantage, with a direct prior-work boundary

Completed 26 October 2026. **The prespecified separation diagnostic passes;
ICML novelty remains unestablished.** This is an exact synthetic calculation
over three systems and two binary items, not a human-judgment experiment.

## What changed

The previous [joint-order candidate](../joint_order_controls/FINDINGS.md)
lost its efficiency claim to stronger inference using the same acquisitions.
This study allows every comparator to use **any valid stopping and reporting
rule**. It asks whether choosing the individual item can add value beyond
choosing a system and beyond buying common-item blocks.

All 64 hidden score matrices are included, including ties and unlikely
matrices. A policy must report the correct entire requested sign vector with
probability at least 95% **for each fixed matrix separately**. Only the
expected cost is averaged over the supplied synthetic prior. Each purchased
cell costs one judgment and is reusable across comparisons.

The [protocol](PROTOCOL.md) was committed before optimization at
`71605934154d0f89b61c64105de97805e9c63835`. The implementation and theory
were committed before the full run at
`f7a928f73df399ef55bb1c2d9de6e67e66cbb9a6`.

## Primary results: maximum 5% error on each matrix

Numbers are expected unique judgments, out of six. Lower is better.
The feasible policy upper bounds and class-wide lower bounds agree within
6.3e-15; displayed costs are rounded to six decimals.

| Synthetic structure | Comparisons | Optimal individual cells | Optimal row-uniform | Optimal common-item retirement | Certified saving vs row-uniform |
|---|---|---:|---:|---:|---:|
| Independent | Reference star | 4.807733 | 4.807733 | 5.658118 | 0% |
| Independent | All pairs | 5.383880 | 5.383880 | 5.673000 | 0% |
| Monotone | Reference star | 4.933617 | 4.976472 | 5.658006 | 0.861% |
| Monotone | All pairs | 5.382505 | 5.382505 | 5.672379 | 0% |
| Opposed | Reference star | 4.385691 | 4.395591 | 5.625917 | 0.225% |
| Opposed | All pairs | 5.078268 | 5.078268 | 5.655550 | 0% |
| One-hot | Reference star | 4.760669 | 4.906135 | 5.657938 | **2.965%** |
| One-hot | All pairs | 5.257068 | 5.257068 | 5.666350 | 0% |

`row_uniform` chooses any system adaptively, then draws uniformly among that
system's unjudged items. `common_retirement` chooses a subset of still-active
systems, buys all their scores on the next uniformly drawn unopened item,
and permanently retires omitted systems. Both classes permit randomized
decisions and unrestricted inference. The common class includes Stage 22's
acquisition rule; this is not a new WMT25 rerun or a numerical comparison
against Stage 22's saved costs.

All three dependent reference-star cases have a strict certified advantage
over **every policy in both specified comparator classes**. For one-hot,
the saving is 2.965% against the stronger row-uniform class and 15.859%
against common-item retirement. The larger common-item saving should not
replace the stronger-control comparison in a contribution claim.

Independent rows have equal cell and row-uniform optima, as predicted by
the general permutation-symmetry proposition in [THEORY.md](THEORY.md).
Every all-pairs case also has equal optima here, without a general theorem
asserting that equality. At zero allowed error, the same three dependent
star cases separate; all other cases do not. Complete results for both
error levels are in [the summary](results_reference/summary.json).

## Why item choice can help

The following is a post-result mechanism example from a reachable state
of the zero-error optimal one-hot/star policy. It does not define another
confirmatory experiment. `?` means a score has not been purchased.

| System | Item 0 | Item 1 |
|---|---:|---:|
| Reference A | 0 | 0 |
| B | 1 | ? |
| C | ? | ? |

A is already worse than B. To compare A and C, finding either C score equal
to one suffices; if both are zero, they tie. Under the one-hot cost prior,
the observed B=1 makes C=1 unlikely on item 0. Item 1 is a better place to
look. Querying C/item 1 first requires **231/172 = 1.343** expected remaining
judgments; querying C/item 0 first requires **231/118 = 1.958**. These costs
include the second C judgment whenever the first is zero. Both strategies
always give the correct answer, including when the prior is wrong.

This illustrates the proposed useful information: a purchased peer-system
score changes *where to look next*. It does not authorize guessing an
unobserved score. A general advantage still depends on the task and structure.

## Published EC2 control: substantial overlap already exists

[Golovin, Krause and Ray (NeurIPS 2010), Section 3](https://papers.nips.cc/paper_files/paper/2010/file/1e6e0a04d20f50967c64dac2d639a577-Paper.pdf)
define equivalence-class determination. Our zero-error formulation maps
directly to it: complete matrices are hypotheses, cell purchases are tests,
and comparison sign vectors define the classes. Their EC2 method greedily
cuts prior-weighted edges between different classes and has an expected-cost
approximation guarantee. **The general problem formulation is therefore not
new.** Exhaustively computing an optimum is not itself a new scalable method.

After the original results, we committed a separate
[EC2 comparison protocol](PRIOR_WORK_CHECK.md) at
`75125098136950482bbc2489aaf1e216e61bd57a`. It uses the same eight designs,
with exact edge weights and fixed tie-breaking. At zero error it reproduces
EC2 acquisition and logical stopping. At 5% error, it keeps EC2's acquisition
choices but optimizes all stopping and report randomization under the same
per-matrix error constraints. The latter is **EC2 acquisition plus optimal
valid stopping**, not the unmodified published algorithm.

| Structure | Comparisons | EC2 cost, zero error | Optimal-cell saving | EC2 acquisition cost, 5% error | Optimal-cell saving |
|---|---|---:|---:|---:|---:|
| Independent | Reference star | 5.480000 | 6.204% | 5.171750 | 7.039% |
| Independent | All pairs | 5.744000 | 0.515% | 5.429600 | 0.842% |
| Monotone | Reference star | 5.410888 | 2.545% | 5.106525 | 3.386% |
| Monotone | All pairs | 5.994875 | 4.562% | 5.670153 | 5.073% |
| Opposed | Reference star | 4.747150 | 0% | 4.477819 | 2.057% |
| Opposed | All pairs | 5.999375 | 9.764% | 5.668628 | 10.415% |
| One-hot | Reference star | 5.573150 | 9.007% | 5.244137 | 9.219% |
| One-hot | All pairs | 5.904563 | 5.297% | 5.575470 | 5.711% |

The exact optimum beats the specified EC2 acquisition in 15 of 16 problems
and ties in one. This is a gap to a known greedy policy, not evidence that
our exhaustive optimizer is a new practical algorithm. In particular,
EC2 losses in all-pairs cases coexist with **no** cell advantage over the
optimal row-uniform class. Better planning and more flexible acquisition
are distinct effects in these results. The EC2 comparison was added after
seeing the main results and is not independent validation.

Related work also already covers adaptive test selection and dynamic-program
cost bounds ([Naghshvar and Javidi, 2013](https://arxiv.org/abs/1203.4626)),
and active learning with correlated tests
([Chen, Hassani and Krause, 2017](https://proceedings.mlr.press/v54/chen17b.html)).
A broad claim about adaptivity, correlation, or shared information is insufficient.

## Verification

The numerical solver only proposes policies and error penalties. Every
reported guarantee is checked using rational arithmetic. Feasible policies
give upper cost bounds; Bellman dual inequalities over every legal action
give lower bounds on all comparator policies. See [the derivation](THEORY.md).

- Five invariant tests passed.
- The frozen 48-problem audit checked **3,072 fixed-matrix policy cases**,
  48,768 action/world transitions, and 159,408 exact action bounds.
- Its largest allowed-error value was exactly 1/20; the largest cost
  certificate gap was approximately 6.25e-15.
- The 16-problem EC2 audit checked another **1,024 fixed-matrix policies**
  and **5,096 acquisition choices** against literal hypothesis-edge sums.
- No new human judgments were collected; no WMT data were used.

These are exhaustive finite checks, not Monte Carlo coverage estimates.
Costs are prior-weighted averages, not a cost guarantee on each individual
matrix. Validity belongs to the particular optimized policy, not to arbitrary
replacement acquisition or stopping rules. Exact binary fixed scores also
do not model annotator noise or continuous MQM scores.

## Research implication and next decision

The result supplies a concrete mechanism and an exact witness of room beyond
row-uniform acquisition. It does not establish a new problem, a new statistical
guarantee, or a scalable algorithm. The exact state space grows exponentially.

The next question is: **Can a tractable policy use observed peer scores to
choose individual cells, retain validity under a wrong predictive model,
and obtain a general cost guarantee or reproducible gain beyond the strongest
existing acquisition methods?** A useful next method must address that
scalability and prior-work gap. Neither another favorable six-cell example
nor a chosen percentage threshold establishes ICML novelty.

## Reproduce or audit

From the repository root, after installing `requirements.txt`:

```bash
python -m unittest discover -s experiments/acquisition_separation -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/acquisition_separation/run_exact.py --output results/acquisition_local
python experiments/acquisition_separation/audit_exact.py --input results/acquisition_local --output results/acquisition_local/audit.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/acquisition_separation/ec2_check.py --source results/acquisition_local --output results/acquisition_ec2_local
```

To audit committed certificates without rerunning optimization:

```bash
python experiments/acquisition_separation/audit_exact.py --input experiments/acquisition_separation/results_reference --output results/acquisition_reaudit.json
python experiments/acquisition_separation/ec2_check.py --source experiments/acquisition_separation/results_reference --output experiments/acquisition_separation/ec2_reference --audit-only
```

Use new directories for optimization runs. Saved rational policies, cost
bounds, per-matrix errors, summaries, and audits are included in
[results_reference](results_reference) and [ec2_reference](ec2_reference).
