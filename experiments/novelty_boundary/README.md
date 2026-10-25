# Novelty boundary after the Stage 33 collection handoff

Date: 2026-10-24. This is a definition-level audit of already published
research and the existing SAFE-EVAL protocols. It uses no new human responses,
does not modify the frozen Stage 22 or Stage 33 studies, and does not claim an
ICML contribution. WMT24 remains uninspected.

## Fix the primary question

The primary method target remains simultaneous, optionally stopped signs of
requested **fixed-test-set** score-mean differences. An acquisition purchases
one system–item score once, and a purchased score may inform every requested
edge incident to that system. Count unique purchased scores and unfinished
comparisons, at the same taskwise familywise error level `alpha=.05` as the
matched control. This is different from inference for *new* items or raters,
and from five-way relative-preference judgments. Changing the target or paid
unit between methods cannot establish an efficiency gain.

## The Stage 22 saving does not isolate a new method

Stage 22 saved 37.083% unique labels against evaluating every system on every
common item of reference-star tasks on WMT25 development data. It buys every
system incident to at least one unresolved requested edge before opening the
next common item. The Stage 23 footprint proof says that if each edge retains
its fixed paired-prefix certificate and needs `n_e` common items, every valid
schedule in that class must buy precisely the label footprint bounded below by

```text
sum_v max{n_e : e is a requested edge incident to v}.
```

Stage 22 attains this footprint. Reordering these same paired-prefix tests
cannot lower their total completion cost; the independent Stage 23 enumerator
rechecked 5,250 asynchronous schedules over eight small graph cases.

Khosravi and Huo's [Rank Confidence Sequences](https://arxiv.org/html/2609.32211v1)
already allow a model to be retired after any past-score-based rule, with no
reactivation, on one precommitted common item order. In particular, one may
retire it once all comparisons of interest incident to it have finished.
**Conditional on applying the same pair certificates and the same requested
graph**, that retirement rule purchases the exact active set Stage 22 calls
`V(U_j)` on item `j`. This is an acquisition-rule equivalence; the published
paper uses its own betting and rank-closure procedures. It does not imply
identical numerical decisions for different certificates. Therefore the
37.083% full-evaluation comparison is development evidence for the retirement
mechanism, not a distinct ICML method claim.

## What the 160-task human pilot can identify

Stage 33's two prespecified panels are `ABCDE` and `ABFGH`. Their union has
eight systems, giving 28 unordered pair types. Within-panel full rankings
directly expose 19 types; the nine pairs joining `CDE` to `FGH` never appear
in either panel. The pilot randomizes two different raters per panel on each
of 40 fixed documents. It directly addresses one controlled contrast:
whether the A/B preference changes between **these two companion panels**.
It also supplies observed time for these tasks.

The pilot cannot identify potential outcomes for other five-way companion
panels under arbitrary panel effects, nor evaluate the stopping cost of an
adaptive multi-panel policy over the full panel space. Its 40-document size
is planned to detect only relatively large context effects; an inconclusive
result would not rule out a small one. It is useful for the problem statement
and cost calibration, not by itself a method or efficiency contribution.

## Existing ingredients the next method must exceed

| Source | Direct overlap with candidate claims |
| --- | --- |
| [Rank Confidence Sequences](https://arxiv.org/html/2609.32211v1) | Fixed matrix, common random item order, simultaneous anytime ranks, pair dependence, rank closure, past-based model retirement. |
| [CELEUS](https://arxiv.org/abs/2606.20820) | Surrogate-assisted, adaptively selected finite-pool samples without replacement; conditionally unbiased off-policy score and e-process intervals for one evaluation target. |
| [Anytime-valid off-policy inference](https://arxiv.org/abs/2210.10768) | Doubly robust and variance-adaptive time-uniform inference under changing logging policies. |
| [Target-Aware Sequential Inference](https://arxiv.org/html/2609.37873v2) | Shared proposals for several targets, gap awareness, range control and best-system identification. |
| [SERPANT](https://proceedings.mlr.press/v306/gu26l.html) | Anytime-valid pairwise ranking, familywise testing, tournament allocation. |
| [Saha and Gopalan](https://proceedings.mlr.press/v89/saha19a.html) | Active subset-wise ranking under Plackett–Luce feedback; their feedback model differs from arbitrary context-dependent panel outcomes. |
| [Zouhar et al.](https://arxiv.org/abs/2608.03437) | Dynamic human evaluation allocation for MT ranking, including correlated systems and annotation-cost concerns. |

This table identifies overlap and a **candidate gap**, not a proof that the
combination is new. A per-contrast CELEUS-type corrected signal followed by
pairwise multiplicity correction or rank closure is a mandatory baseline.

## One falsifiable next contribution gate

Seek a **joint** fixed-pool, cell-level acquisition and evidence construction
that buys individual system–item scores adaptively, shares each score across
requested comparisons, and certifies the same fixed-pool signs under optional
stopping at the same `alpha`. The guarantee must hold in the filtration that
includes scores revealed through *other* edges and the current item's partial
scores. The Stage 25 counterexample shows that treating filtered pairs as a
fresh uniform prefix can reject a true null with probability one.

Before another WMT25 performance run, require all of the following:

1. State the exact acquisition filtration and prove simultaneous finite-pool
   validity, including adversarial cross-system dependence, ties and full
   exhaustion. A formal counterexample to a weaker rule counts as progress.
2. Show a strict attainable cost improvement over Stage 22 **and** the
   per-contrast CELEUS-style plus rank-closure control at the same target,
   error guarantee, completion requirement and unique-label charge. A
   retirement-only variant cannot pass this gate.
3. Freeze synthetic correlated, anticorrelated, close-gap and tie cases,
   requested star/ring/complete graphs, budgets and controls before running
   the new method. Report costs to correct completion and unfinished cases;
   preserve negative results.
4. Use new randomized human evidence to motivate or test the annotation cost
   model. The Stage 33 pilot alone cannot measure multi-policy savings.
   Leave WMT24 for one independent confirmation after the theorem and matched
   synthetic gate pass.

At this date the gap is an open research question. No theorem or matched
efficiency result meeting this gate has been obtained.

## Subsequent panel-allocation diagnostics (2026-10-24)

The separate five-way-panel setting was screened on fresh synthetic
matrices. A [full-population oracle proxy](../panel_oracle_gap/FINDINGS.md)
found 21.26% and 18.80% mean paired variance-and-duration proxy headroom in
the shifted scenarios. A [predictable pilot-based implementation](../panel_gap_feasible/FINDINGS.md)
then used **6.88% and 6.27% more** mean simulated stopping duration than the
strongest matched original controls in those scenarios. Both full-result
audits passed. This rules out that particular feasible proposal as an
efficiency claim. The proxy does not establish purchased-judgment savings,
and these panel results do not resolve the fixed-score cell-level contribution
gate above. No prospective human panel judgments have yet been collected.


## Joint ordering prototype (2026-10-25)

The [joint finite-pool ordering study](../joint_order_gate/FINDINGS.md)
implements a restricted next step: three binary-score systems, adaptive
system selection and uniform sampling among unseen items within the chosen
system. It calibrates evidence against complete ordering nulls and shares
each purchased cell across comparisons. The conditional validity argument
uses existing e-variable and order-elimination principles; it is not a
distinct theorem claim.

Across 100 small synthetic matrices, a local efficiency signal survived
the explicitly post-result requested-edge exact-pair control: 8.20% fewer
labels for independent strong-gap stars and 6.16% fewer for triangles.
The frozen broader expansion gate nevertheless failed because the moderate-gap
star comparison against Stage 22 remained uncertain. Reversed predictions
cost 9.38% more than Stage 22 for stars. Full ledgers, five tests, small exact
enumeration and independent full-result audits are published.

This supplies a restricted matched mechanism, not a result satisfying the
full contribution gate above. A distinct cost characterization, scalability
beyond three systems, and a strong prediction-aware complete-item comparator
remain open. No WMT24 outcomes or prospective human judgments were used.
