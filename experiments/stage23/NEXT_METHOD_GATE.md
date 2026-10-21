# Candidate beyond fixed pair certificates: joint finite-pool evidence

This is a research design, not a proved method or an ICML claim. Stage 22's
WMT25 result and Stage 23's original protocol remain frozen. No WMT24 outcome
has been used. The [asynchronous boundary](ASYNC_PREFIX_BOUNDARY.md) shows
that a new query order alone cannot improve total graph-completion cost while
every edge retains its old certificate and common-item prefix.

## One precise problem

Given a fixed matrix of bounded system-item scores, a predeclared requested
comparison graph, and a family error target, choose which item and which
systems to judge next. Cache every system-item score so it is charged once.
At *every* acquisition time, report only pairwise signs that are certified
against the **complete fixed item pool**. The target is fewer unique labels
to finish all requested conclusions, with finite-sample familywise error
control under optional stopping. A method may use historical predictions for
query selection, but the statistical guarantee must survive arbitrary
prediction error.

The candidate contribution would be a **joint** finite-pool confidence
construction that uses partially observed system scores for several requested
differences, plus an acquisition rule that exploits the common label cache.
It must permit genuine changes to evidence or safe allocation beyond the
existing independent pair-prefix certificates; a new scheduling heuristic
with those certificates is ruled out by the max-prefix identity.

A separate confidence sequence for each system followed by a union bound
over systems is a necessary baseline, not a contribution: it follows by
applying existing finite-population inference repeatedly. The project's
earlier [finite-pool adaptive prototype](../stage7/safe_eval_v1.py) also
covers a one-target nonuniform without-replacement e-process. A joint
construction must demonstrate
something that these direct combinations cannot obtain at the same
familywise error and unique-label cost.

## Non-negotiable proof and comparison gates

1. Specify the exact acquisition filtration, randomization and exposure of
   cached scores. Prove time-uniform coverage for the fixed finite matrix
   under outcome-adaptive choice of item and system subset. Exact enumeration
   on small matrices must include adversarially correlated system outcomes.
2. Prove familywise validity for all requested graph edges and exact full-pool
   signs, including ties and the final finite-pool step. If the guarantee is
   only asymptotic, call it a different result and do not compare it as
   equivalent to Stage 22.
3. Count unique system-item labels, not pairs or item batches. Demonstrate a
   synthetic instance with strict savings over Stage 22 at the same error
   target, and report cases where the method costs more. Show exactly which
   old premise is relaxed and why the Stage 23 lower bound does not apply.
4. Compare against Stage 22 and the strongest applicable finite-pool joint
   and adaptive testing procedures with matched estimand, error guarantee,
   item bank, and cost. [AnyRank](https://arxiv.org/abs/2610.14603) has
   i.i.d. policy outcomes; [FAQ](https://arxiv.org/abs/2601.20251) has
   fixed-budget asymptotic accuracy intervals and with-replacement sampling;
   [Zouhar et al.](https://arxiv.org/abs/2608.03437) optimize dynamic WMT
   ranking allocation. These differences are comparison obligations, not
   automatic novelty.
5. Write a counterexample to every weaker claim that fails (for example,
   ignoring score exposure, treating sampled-with-replacement proofs as
   without-replacement, or selecting the best result after observing WMT25).

## Order of work

First solve or disprove the joint validity theorem on synthetic finite
matrices. Then predeclare a synthetic study with stars, rings and complete
graphs, low and high system correlation, weak and strong gaps, and
uninformative or reversed predictions. Use exact permutation enumeration
where feasible and held-out random seeds otherwise. Freeze its decision
thresholds before computing method results.

Only if the theorem and a material matched-baseline improvement survive
should a new WMT25 analysis be proposed. WMT24 remains reserved for one
external confirmation after the Stage 23 contribution gate passes. If the
construction reduces to existing active testing or has no clear gain over
Stage 22, stop this line rather than adding benchmark variants.
