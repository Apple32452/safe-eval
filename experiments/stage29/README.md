# Stage 29: a cost boundary for shared-reference partial labeling

This is a **feasibility diagnostic**, not a sequential method or an ICML
novelty claim. It explains why a partial-query experiment with only three
systems can fail even when partial queries might be useful for a larger
reference-star comparison task. It does not inspect WMT24.

## Exact local calculation

For one prospectively drawn item and rater, let `A` be the reference score,
`B` a candidate score, and `D=A-B`. Let `m(A)` be fixed using information
available before that draw. We buy `A`, then independently buy `B` with
probability `q` conditional on `A`. With known probability `q>0`, the
corrected signal is

`G = A - m(A) - Z * (B-m(A))/q`.

Conditional on the item, rater, `A`, and `B`, the query coin makes
`E[G]=D`. Therefore, writing `V=Var(D)` over the prospective item/rater
distribution and `R=E[(B-m(A))^2]`, the law of total variance gives the
**exact identity** `Var(G)=V+(1/q-1)R`. It holds for a fixed finite matrix
sampled with replacement as well as a genuinely prospective population,
provided the query coin follows the specified rule. It says nothing about
coverage on a previously collected, nonrandom rater panel.

Suppose one reference score is charged once and shared among `k` simultaneously
active reference-versus-candidate edges. At a *fixed active set and round
count*, its amortized cost per edge is `r=1/k` and the candidate's expected
cost is `q`. The ratio of local variance times expected labels to full paired
scoring is

`((r+q)/(r+1)) * (1+(1/q-1)*R/V)` for `V>0`.

For `q<1`, this ratio is below one **exactly when** `R/V < q/(q+r)`.
At `q=0.75`, the threshold is `0.42857` when one edge bears the whole
reference cost, but `0.92727` when a reference score supports 17 active
edges. As edges resolve, `k` decreases and the threshold tightens. This
local variance identity is not a theorem about stopping time, overall label
cost, or statistical power of bounded betting factors. It does not account
for candidate training scores or rater payment overhead.

## WMT25 development diagnostic

The script loads Stage 17's verified, aligned WMT25 *recorded two-rater mean*
score matrices. For each ordered reference/candidate pair, it learns a
clipped linear `B~A` predictor on four of five item folds and predicts the
held-out fold. The same seeded item partition is used across pairs within
each language. It calculates `V` and `R` over that fixed recorded matrix;
these are descriptive properties, not a new-rater inferential target.

**Critical cost caveat:** each predictor is trained on approximately 80% of
the target candidate's item labels. This diagnostic charges none of those
training labels. Its cost ratios are optimistic screening quantities, not
deployable savings. The folds also use outcomes already seen in prior WMT25
research; WMT25 remains development data.

Run from the repository root after preparing `results/stage17_data` using
the Stage 17 instructions:

```bash
python -m unittest discover -s experiments/stage29 -p 'test_*.py' -v
python experiments/stage29/analyze_feasibility.py \
  --data results/stage17_data --output results/stage29_feasibility
```

The three tests include an independent enumeration of the query coin and
item distribution, plus a case where sharing the reference changes the
local cost decision. See [the results and decision](FINDINGS.md).

## What would count as a contribution

The cost identity is elementary; propensity correction and adaptive
allocation are prior work. A new result would need a **joint, adaptive
system-label acquisition rule** for a requested comparison graph that:

1. pays for training, reference and candidate scores exactly once;
2. remains simultaneously valid under its explicit item and rater sampling
   design, including after reference-conditioned query decisions;
3. proves a graph-dependent efficiency or regret guarantee beyond applying
   single-comparison off-policy inference edge by edge; and
4. beats full paired shared-item scoring, rank confidence sequences with
   model retirement, and an appropriate strong off-policy baseline at the
   same family error target and human-label cost.

The next experimental gate should be frozen on synthetic 18-system stars
with aligned, weak, reversed and heterogeneous candidate predictions. Count
**paid** training labels, wrong and unresolved conclusions, and label cost
to complete conclusions separately. Use the same item/rater ledgers and a
matched full paired control. A successful variance proxy alone does not
pass this gate. WMT24 remains a held-out confirmation resource until a
method and its strong baselines survive that gate.

Closest relevant work includes [Rank Confidence Sequences](https://arxiv.org/abs/2609.32211),
[CELEUS](https://arxiv.org/abs/2606.20820),
[AnyRank](https://arxiv.org/abs/2610.14603),
[variance-adaptive off-policy confidence sequences](https://arxiv.org/abs/2210.10768),
and [adaptive correlated-model ranking](https://arxiv.org/abs/2608.03437).
