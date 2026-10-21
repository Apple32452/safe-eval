# Stage 23 frozen protocol: paper-level contribution audit

## Decision question

Stage 22 established a large development effect for a sparse reference-star
objective: 37.083% fewer unique system-item labels with exact agreement on the
complete-benchmark conclusions. Stage 23 asks a different question:

> Does exact finite-pool, shared-label graph pruning support a contribution
> that is definitionally and technically distinct from the closest sequential
> evaluation and ranking procedures?

This is a contribution-audit phase, not a search for a larger WMT25 number.
The Stage 22 method, thresholds, data, paths, and results are frozen. WMT24
must remain untouched.

## Candidate paper-level statement

The candidate contribution is deliberately narrow:

1. the estimand is the sign of each requested difference on one fixed finite
   benchmark, not an i.i.d. population mean;
2. paired observations follow a precommitted uniform without-replacement item
   order;
3. one acquired system-item score is shared by every requested edge incident
   to that system on that item;
4. the unresolved comparison graph determines exactly which system labels are
   still needed on the next common item; and
5. pruning those labels is pathwise never later, in cumulative unique-label
   cost, than scoring every system on the common item stream.

The stronger candidate theorem to audit is conditional optimality: among
synchronous prefix-preserving policies that advance every unresolved requested
edge on the next common item, a policy must acquire every vertex incident to
the unresolved graph. Stage 22 acquires exactly that set. This is not a claim
of global optimality over asynchronous, model-based, i.i.d., or
indifference-zone ranking procedures.

## Required closest-work comparison

The audit must compare definitions, assumptions, guarantees, actions, and cost
units against primary sources in all of these families:

- active testing and adaptive test-point selection;
- confidence sequences for sampling without replacement;
- sequential stopping for model evaluation;
- sequential model confidence sets;
- AnyRank and its N-SCORE pairwise subroutine;
- target-aware adaptive allocation and familywise best-system identification;
- multiple comparisons with a control and ranking-and-selection under common
  random numbers; and
- fixed-benchmark MT evaluation and test-set reduction.

A paper title, abstract, keyword match, or absence of identical code is not
evidence of novelty. The comparison must state whether the Stage 23 theorem is
already explicit, an immediate corollary, or genuinely different.

## Required technical checks

1. State the filtration, finite population, requested graph, label cache,
   stopping rule, and family error event.
2. Prove taskwise validity without treating empirical zero errors as proof.
3. Prove the existing per-edge pathwise dominance result with the final
   possibly partial item block handled explicitly.
4. Prove or reject synchronous-class label minimality.
5. Give counterexamples showing why the result does not imply global sample
   optimality or validity for outcome-dependent item selection.
6. Exhaustively enumerate small graphs, item orders, and bounded score grids
   with an implementation independent of the Stage 22 scheduler.
7. Separate graph topology savings from confidence-bound conservatism.

## Baseline rule

No method may be labeled an AnyRank, model-confidence-set, active-testing, or
ranking-and-selection baseline unless its estimand and guarantee are matched
or the mismatch is displayed prominently. If public author code cannot be
faithfully adapted, report the comparison as a definition-level boundary and
do not invent a surrogate under the published name.

The guaranteed common-prefix control and Stage 22 pruning method remain the
minimum reproducible baselines. Any added empirical baseline must use the same
requested edges, family error target, outcome matrix, and unique system-item
cost whenever those quantities are meaningful for that method.

## Go/no-go gate

Stage 23 passes only if all conditions hold:

1. a precise theorem or problem formulation survives the primary-source audit
   as more than a direct corollary;
2. the claim remains nontrivial after restricting it to its honest policy
   class and cost model;
3. a strongest applicable baseline is identified and either implemented
   faithfully or documented as incommensurable for a precise reason;
4. exhaustive small-case checks support every pathwise and accounting claim;
5. Stage 22's 37.083% effect remains correctly described as development
   evidence for the reference-star objective, not universal ranking savings;
   and
6. no WMT24 outcome has been inspected.

If the gate fails, stop this method line and choose a new research question.
If it passes, freeze the paper method and external-validation protocol before
one WMT24 run. A pass would justify validation; it would not guarantee ICML
acceptance.

