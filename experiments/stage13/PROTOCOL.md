# Stage 13: preserving fixed-benchmark pairwise conclusions

## Question and scope

Can sequentially revealing fewer paired target-system annotations recover the
direction of the complete fixed-benchmark difference? Does historical assistance
improve label cost beyond the same procedure with zero historical prediction?

This is a development experiment prompted by a question about useful MT findings.
It does not demonstrate a novel method, preserve official MQM significance
clusters, infer quality on future sentences, or construct one reusable small test
set for every system. No hyperparameter or pair selection will be changed to
obtain favorable WMT results. The previously proposed predictor-component ablation
remains separate, unrun work.

## Data and complete reference conclusion

Use the unchanged, checksummed Stage 7 WMT23 binary recorded-annotation matrices:
en-de (154 items, 12 systems), he-en (820, 12), zh-en (589, 15).
Include every unordered pair in sorted system-name order: 66 + 66 + 105 = 237.
For pair (A,B), D_i = Y_Ai - Y_Bi is in {-1,0,1}; positive means A has
a higher recorded error-free proportion. The reference conclusion is sign(sum D).
An exact zero is a tie. This reference is not a population-significance test.
Both A and B must be excluded from the historical bank (leave TWO systems out).
Do not filter pairs using the complete-label difference.

Full labels are available only to the simulation oracle and post-run analysis.
Sampling is uniform without replacement, jointly revealing both target labels on
each sentence. One paired query costs two system-item labels. Historical labels
and computation are not included in that cost. Pool size remains the fixed common
annotated intersection; no missing labels are imputed.

## Locked experiment

- 50 query permutations per pair; master seed 20261021.
- The same ledger is shared by every method/history for a pair.
- Seeds use SHA256 of master seed, language pair, A, B; NumPy PCG64.
- Fixed budget diagnostics at floor(25%, 50%, 75%) of the pool.
- Two-sided per-pair error level 0.05: directional threshold 40.
- Secondary simultaneous setting: Bonferroni over all 237 comparisons,
  directional threshold 40 * 237 = 9480. This controls any wrong directional
  claim in one complete 237-pair evaluation, separately for each method.
- The two settings and the several methods do not share a joint 95% guarantee.
  They are predeclared separate comparisons; no post-hoc method selection rule.
- Exact ties are reported only at complete evaluation. Undecided is not a tie.
- A method stops at the first sole directional threshold crossing or a
  deterministic finite-pool sign certificate. Conflicting simultaneous crossings
  defer the decision. At full evaluation the exact sign/tie is reported.
- No numerical wealth threshold or stopping precision is tuned on these data.

## Six methods

1. `deterministic`: declare sign only when the observed difference exceeds the
   remaining item count in magnitude; exact conclusion at the full budget.
2. `paired_ppr`: categorical prior-posterior-ratio evidence on paired outcomes
   (A wins, B wins, equal), with the uniform Dirichlet(1,1,1) count prior.
   Maximize the hypergeometric likelihood over each composite sign null.
3. `reserve_zero`: 75% paired-PPR evidence + 25% corrected-draw betting evidence
   with prediction identically zero.
4. `reserve_aligned`: identical mixture, with leave-two-out historical features
   and sequentially fitted target predictions.
5. `reserve_permuted`: identical to aligned, with one fixed permutation of
   historical item columns, shared across target pairs within a language.
6. `reserve_reversed`: identical to aligned, replacing historical labels H by 1-H.

The 75% reserve is inherited as a design choice from the earlier project; it is
not optimized here. Categorical PPR is a direct paired statistical baseline, not
a claim that every stronger categorical boosting method has been exhausted.
Raw evidence is conservatively zero on a sample contrast opposing its
alternative; this cannot change its standalone threshold crossing. Both mixtures
use that same conservative evidence.

Historical predictor: Stage 7 item means plus intercept and three centered
right-singular-vector features, computed only from the remaining systems.
Two ridge regressions are updated only after each paired query; initial ridge
diagonal (0.25,1,1,1), zero right-hand sides. Clip each predicted outcome to [0,1]
and shrink toward 0.5 by a fixed strength 0.5. Subtract the two predictions and
round to integer multiples of 1/1024. This is a new paired adaptation with fixed
trust, not a reproduction of the Stage 7 or Stage 9 statistical engines.

Corrected-draw evidence uses eight equal-capital betting experts, with fixed
base stakes 1/8, 1/4, 1/2, 1, 2, 4, 8, 16. Stakes are predictably capped so every
possible next factor is at least 1/2. Use the same rules with zero prediction.
Wealth arithmetic rounds downward on a 2^-20 grid and caps/absorbs at 9480.
All rejection decisions use integers. See THEORY.md for the design calculation.

## Outcomes and reporting

Primary feasibility: correct early-decision fraction, wrong-direction fraction,
mean labels / full labels, and unresolved fraction at each smaller budget.
Primary historical comparison: aligned reserve minus matched zero reserve in
mean paired queries. Also compare both to categorical PPR, retaining all losses.
Report all languages and pair-level results. Overall values weight languages
equally, then pairs equally within language, then query permutations equally.
Report conditional Monte Carlo standard errors over repeat blocks; these do not
measure uncertainty over new benchmarks, systems, or annotators.

Descriptive post-run strata: exact ties; nonzero absolute full-benchmark gap at
most 0.02; (0.02,0.05]; greater than 0.05. Strata are not used for selecting
methods, training, querying, or tuning. Report fixed-budget naive sample-winner
agreement as an explicitly uncertified diagnostic, with sample ties separate.

The claim of smaller evaluation must name the fraction decided and the error
setting. We will not describe undecided pairs as successfully preserved, or
claim a universally minimal test set. The latest advisor email supports the goal
but does not approve this particular objective or implementation.

## Validation and publication

Before the complete run: freeze this protocol in GitHub; test null likelihood
optimization against complete enumeration; test exact rational betting budgets,
integer overflow bounds, current-outcome exclusion, leave-two-out exclusion,
ledger uniqueness, ties, and exhaustive small-pool anytime decision errors.
Then freeze code/data hashes and commit before examining complete WMT results.

Save query ledgers, wealth curves, and predictor audit states outside the compact
release. Independently reconstruct saved decisions, exact raw evidence, and
betting updates. Commit compact per-pair results, all stopping decisions, source
hashes and audits, with reproduction commands. Prepare an email update after
the analysis; do not send it automatically.

## Primary sources

- Waudby-Smith and Ramdas (2020), categorical PPR confidence sequences:
  https://proceedings.neurips.cc/paper/2020/file/e96c7de8f6390b1e6c71556e4e0a4959-Paper.pdf
- Gao, Sicilia and Shi (2026), prediction-powered MT system comparisons:
  https://arxiv.org/html/2608.26638
- Lo and Knowles (2023), sampling and MT ranking stability:
  https://aclanthology.org/2023.findings-acl.826/
- The unchanged Stage 12 contribution audit remains applicable. Pairwise
  comparisons, PPR, control variates and fixed mixtures are existing principles.
