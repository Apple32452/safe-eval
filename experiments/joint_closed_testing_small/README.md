# Exact small-case closed-testing baseline for two directional comparisons

This is a **standard closed-testing baseline**, not a novel joint confidence
construction. It tests one way to share family error across the two nulls
`H1: T0 <= T1` and `H2: T0 <= T2` on a fixed three-system, two-item binary
matrix. It does not decide reverse directions or exact ties and is therefore
not a direct Stage 22 completion-cost comparison. No WMT data are used.

## Construction and validity

Before each query, choose uniformly from all unobserved cells. For each null
`Hj`, choose a positive raw factor `h_j(c,y)` that rewards `T0 > Tj`. Divide
by the **maximum** conditional expected raw factor over every full binary
matrix compatible with observations and `Hj`:

    D_j(history) = max_{M compatible with history and Hj}
                   average_{c unseen} h_j(c, M[c]);
    f_j(c,y) = h_j(c,y) / D_j(history).

For every fixed matrix in `Hj`, the selected factor has conditional mean at
most one in the full query history. Thus its wealth `E_j` is a nonnegative
supermartingale; this proof allows the query distribution and raw factors to
be chosen predictably from the full observed history if the maximum uses the
actual next-query probabilities. The implementation fixes a uniform query
distribution and `h=4` for a favorable bit, `h=1` otherwise. It uses exact
rational arithmetic. Logical rejection when *every* compatible completion
violates a null is error-free.

Under `H1` and `H2` together, `E12 = (E1+E2)/2` is a nonnegative
supermartingale. Closed testing rejects `Hj` only when `E_j >= 1/alpha`
and the intersection has been rejected (`E12 >= 1/alpha` or logical
impossibility). Bonferroni rejects `Hj` when `E_j >= 2/alpha` or logically
impossible. Standard closed-testing logic and Ville's inequality give
familywise probability at most `alpha` of any false directional rejection,
at any stopping time, on each fixed matrix. With these same `E_j` paths,
closed testing contains every Bonferroni rejection, so it cannot be slower
for this directional completion target.

This is an established multiple-testing construction. Its validity does not
prove a new statistical method, and the exact enumeration is an implementation
check rather than a substitute for the argument above.

## Exhaustive audit and observed boundary

```bash
python experiments/joint_closed_testing_small/audit.py
python experiments/joint_closed_testing_small/audit.py --alpha-denominator 4
```

For each of 64 fixed binary matrices and 720 complete query orders, the script
checks every sequential decision (46,080 matrix/order paths). It separately
checks 5,544 conditional factor expectations under compatible true nulls and
asserts the exact family error rate does not exceed `alpha` for **every**
matrix. The largest observed erroneous-family count at `alpha=1/4` is 48 of
720 orders (6.67%); at `alpha=1/20` it is zero. These empirical counts are
not the proof of the guarantee.

For the illustrative matrix `T0=2, T1=T2=0`, exact mean cells to reject both
directions are:

| Family target | Closed testing | Bonferroni | Strictly cheaper orders |
| --- | ---: | ---: | ---: |
| `alpha=0.05` | 4.7333 | 4.7333 | 0 / 720 |
| `alpha=0.25` diagnostic | 4.4889 | 4.7333 | 112 / 720 |

The diagnostic 25% family error is intentionally far above the project's 5%
target. The 5% case has **no observed cost gain** on this example. This result
does not establish a cost advantage over Stage 22, a scalable policy, or ICML
novelty. It says a genuine new joint certificate must beat **at least** this
standard closed-testing combination of the same per-edge e-processes.
