# Conditional ordering factors: validity argument and novelty boundary

## Fixed target and filtration

Let Y be any fixed 3-by-N binary matrix. T[v]=sum_i Y[v,i]. The filtration
includes all earlier purchases and their values, including cells of other
systems on a partly observed item. At each history, s[v] successes are known
and m[v] cells remain. Choose any predictable q with q[v]>0 for every row
with m[v]>0, and q[v]=0 for exhausted rows; then sample an unseen item uniformly
within the chosen row. No independence between systems or items is assumed.
Uniformity **within** the chosen row is essential to the reduction below.

## Exact finite null reduction

For a hypothesized weak ordering W, let P_W contain all real vectors T with
`s[v]<=T[v]<=s[v]+m[v]`, ordered between W's groups and equal within groups.
These box and difference constraints form an integral polytope: its vertices
are integer vectors. Every integer vector in the polytope can be completed
to a binary matrix consistent with observed cells. For remaining rows define

```
r[v,T] = (T[v]-s[v])/m[v]
z[v,0;T] = q[v]*(1-r[v,T])
z[v,1;T] = q[v]*r[v,T].
```

For exhausted rows both event probabilities are zero. For a nonnegative
factor vector f on the six possible events (row v, observed value 0 or 1),
the exact conditional expectation is z(T) dot f. It is affine in T, so
checking all vertices of P_W is necessary and sufficient to bound it by one
over every compatible null completion. The same argument holds for a single
pair null T[a]<=T[b]. Empty null polytopes may be eliminated logically.

For predictable alternative event masses a[v,1]=q[v]*pred[v] and
a[v,0]=q[v]*(1-pred[v]), choose a feasible factor by solving

```
maximize sum_j a[j]*log(f[j])
subject to f>=0 and z(T) dot f <= 1 for every null vertex T.
```

Any feasible factor is valid; optimization accuracy affects efficiency only.
Multiplying the selected factors yields a nonnegative test supermartingale
under the corresponding fixed-matrix null. Poor predictions do not invalidate
the conditional inequality. This is an application of established
growth-optimal e-variable theory, not an originality claim.

## Individual signs and familywise error

There are 13 weak orders of three systems. Let W* be the actual weak order
of T, including ties. Its null polytope always contains the actual totals.
By Ville's inequality its evidence crosses 1/alpha with probability at most
alpha. The certifier retains every order not yet rejected or logically
excluded. A strict a>b conclusion is permitted only if the survivor set is
nonempty and **every** survivor places a strictly above b. Exact known-total
and bounded-completion conclusions may be added at zero risk. Therefore,
if W* has not been rejected, every strict conclusion is true simultaneously,
at all times; any wrong strict declaration implies rejection of W*. This
gives a fixed-matrix familywise anytime error bound alpha, without treating
an intersection rejection as an individual-edge rejection. Ties are not
certified statistically by the implementation; they require exact endpoints.

The matched pairwise control maintains one e-process for each T[a]<=T[b].
For any W, averaging the **current** pair wealths implied by W gives another
e-process under W. The same survivor rule is therefore valid. Replacing that
average by an optimized factor at every step is the mechanism under test.
It need not improve sample cost; expected log growth is not stopping cost.

## Limits of this result

The proposition does not permit arbitrary nonuniform sampling among items
within a row: then system totals alone no longer determine the event law.
It covers a genuine adaptive cell policy, with all past partial-item values
in the filtration, but does not exploit individual item features or paired
within-item correlation in its purchase rule. It gives no new lower bound,
sample-complexity guarantee, global numerical optimum certificate, or ICML
novelty result. The 13-order construction also does not by itself scale to
large leaderboards. Any observed gain must beat a strong matched certificate,
not just a weaker implementation or full evaluation.

## Closest prior work

- [Safe Testing](https://arxiv.org/abs/1906.07801) develops growth-rate-optimal
  e-variables for composite nulls; the constrained optimization is a finite
  conditional instance of those principles.
- [Rank Confidence Sequences](https://arxiv.org/html/2609.32211v1) gives the
  order-elimination principle, anytime ranks and model retirement. Its
  Appendix D excludes data-dependent item orders and points to importance
  correction as a repair.
- [CELEUS](https://arxiv.org/html/2606.20820v2) already combines adaptive
  finite-pool sampling, surrogate corrections and anytime inference. The
  centered cell control is a composition of those ideas with rank closure.
- [AnyRank](https://arxiv.org/html/2610.14603v2) already combines active
  multi-policy evaluation and graphical familywise testing in another
  sampling model.

These overlaps make it inappropriate to call the validity argument a novel
theorem. A distinct cost characterization or convincing matched efficiency
mechanism would be needed for a methodological paper.
