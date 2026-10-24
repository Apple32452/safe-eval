# Cell permutation screen: no efficiency gain

Date: 2026-10-24. Decision: **0/4 scenarios pass the precommitted gate;
this method is not an ICML contribution.** The protocol was committed to
`main` as `6278d71` before the full experiment. The four code invariants and
the independent saved-row audit pass. WMT24 and WMT25 were not used.

The exact fixed 50-repeat simulation has five systems, 128 items, four
reference comparisons, taskwise `alpha=0.05`, and the same Stage 17 six-stake
mixture and `2|E|/alpha` family threshold. Both methods return all four exact
full-pool signs on every matrix, and both charge each purchased system--item
score once. Means are unique judgments **to complete all four comparisons**.

| Scenario | Stage 22 paired-prefix/pruned | Global cell permutation | Change in cost |
| --- | ---: | ---: | ---: |
| Independent easy | 143.44 | 244.22 | +70.26% |
| Independent weak | 476.18 | 533.04 | +11.94% |
| Shared-uniform easy | 114.72 | 233.60 | +103.63% |
| Independent close | 604.38 | 622.14 | +2.94% |

The frozen pass criterion was a **10% or greater cost reduction in at least
three of four scenarios**. None passed. The audit verified all 200 saved
matrix/method pairs, 800 recorded reference-edge signs, protocol digest,
matrix identifiers, label bounds, and aggregate gate; it found no wrong final
signs. Theoretical family risk follows from the precommitted uniform cell
permutation, fixed finite-pool betting factors, Ville's inequality, and a
union bound. Zero observed errors are not a substitute for that proof.

There is a concrete reason the uncentered cell path loses information. For
the uniform signed-cell population `Z` of `A_i` and `-B_i`, its variance is

```text
Var(Z) = (Var(A) + Var(B))/2 + (mean(A) + mean(B))^2/4.
```

The paired item differences `D_i=A_i-B_i` instead have
`Var(D)=Var(A)+Var(B)-2Cov(A,B)`. Even if both systems are constant at `0.5`,
the signed cells have variance `0.25`, while paired differences have zero
variance. Positive within-item correlation makes pairing especially valuable.
The candidate does gain the ability to buy one cell at a time but does not
compensate for this loss in these four matched tasks.

This is a test of the **uncentered** global-cell rule. Centering with learned
predictions, adaptive cell proposals, and joint closure are different methods;
none is validated by these results, and those ingredients already appear in
earlier SAFE-EVAL stages and current literature. Reusing these four scenarios
to retune another cell rule would be exploratory. In particular, existing
work on finite-pool active evaluation and closed multiple testing prevents a
new-theorem claim from the elementary validity argument here.

Reproduce the four invariant checks, frozen run, and saved-row audit from the
repository root:

```bash
python -m unittest discover -s experiments/cell_permutation_probe -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python \
  experiments/cell_permutation_probe/run_screen.py --repeats 50 \
  --output experiments/cell_permutation_probe/results_reference
python experiments/cell_permutation_probe/analyze_screen.py \
  --input experiments/cell_permutation_probe/results_reference
```

The full [replicates](results_reference/replicates.csv),
[protocol digest and seeds](results_reference/metadata.json), and
[aggregates](results_reference/summary.json) are retained. The negative
decision does not revise Stage 22's separate 37.083% development saving
against a full common-item control, nor does it establish that Stage 22 is
optimal among different evidence rules.
