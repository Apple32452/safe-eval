# Conditional variance boundary for shared comparison acquisition

26 October 2026. This is a diagnostic theorem about a **one-query variance
proxy**, not a guarantee on the number of purchased judgments before a valid
comparison certificate stops. Variance-optimal importance sampling is
established in active testing and finite-population sampling; this algebra
alone is **not** an originality or ICML claim. Related primary papers:
[Active Testing](https://arxiv.org/abs/2103.05331),
[nonuniform finite-population confidence sequences](https://proceedings.mlr.press/v216/shekhar23a.html),
and [EC²](https://papers.nips.cc/paper_files/paper/2010/file/1e6e0a04d20f50967c64dac2d639a577-Paper.pdf).

## A fixed-history statement

At any history, let C_v be the still eligible cells in system v, n_v its
size, and m_v>0 the total next-query probability allocated to that system.
Let p_c be a predictable prediction and r_c=Y_c-p_c. For requested pair e,
s_{ec} is +1, -1, or 0 according to the cell's endpoint membership. A
one-draw residual estimator of the unresolved difference is
H_e=s_{eC}r_C/q_C for C drawn predictably from q. For each fixed target Y,
E_C H_e=sum_c s_ec r_c and E_C H_e²=sum_c s_ec² r_c²/q_c.

With nonnegative comparison weights lambda_e summing to one, and a
conditional second-moment model A_c=E[r_c² | history], put
a_c=A_c*sum_e lambda_e*s_ec². Under that model, the weighted sum of
conditional second moments is V(q)=sum_c a_c/q_c. The expectation over Y
here is a modeling assumption about unobserved scores; the fixed-matrix
identity above requires no model.

**Proposition.** Among all distributions q with row masses m_v, the
infimum of V is attained at

    q*_c = m_v sqrt(a_c) / sum_{j in C_v} sqrt(a_j),  c in C_v.

When every a_c>0 this is a strictly positive minimizer. If a_c can be zero,
the formula gives an infimum and a positive uniform floor can approximate it.
For a row-uniform comparator q^row_c=m_v/n_v, the exact difference is

    V(q^row) - V(q*)
      = sum_v [n_v sum_{c in C_v} a_c - (sum_{c in C_v} sqrt(a_c))²]/m_v
      = sum_v [sum_{c<d in C_v}(sqrt(a_c)-sqrt(a_d))²]/m_v >= 0.

**Proof.** Apply Cauchy-Schwarz within each row:
(sum sqrt(a_c))² <= (sum a_c/q_c)(sum q_c) = m_v sum a_c/q_c.
Equality requires q_c proportional to sqrt(a_c). Substitution and
expansion of the pairwise squares gives the displayed difference.

Thus heterogeneity **within** a system is necessary for item choice to
improve this proxy at fixed row mass. The result allows multiple comparisons
to share a cell through sum_e lambda_e*s_ec². It says nothing about the
optimal weights lambda, the exact e-factor growth, full trajectory cost,
annotation noise, model misspecification, or novelty relative to published
active sampling. In particular, an observed proxy improvement need not
translate into fewer purchased judgments.

## Empirical diagnostic, not a confirmatory trial

The script in this folder reconstructs the previous one-hot reference-star
histories. It sets A_c=p_c(1-p_c), lambda equal across unresolved edges,
and uses the row masses from the preserved `row_peer` proposal. It compares
V(q*) to V(q^row) at each candidate policy history. These are fitted model
variances, not hidden true residuals or measured end-to-end label costs.
The unconstrained optimum is optimistic relative to a positive exploration
floor. These outcomes were inspected before writing this analysis, so they
must not be used as independent evidence for a new algorithm.

From the repository root, first regenerate the two source case archives using
their frozen study commands if they are absent, then run:

```bash
python experiments/variance_boundary/audit_proxy.py \
  --old results/peer_cell_scale_full/cases.json.gz \
  --new results/certificate_acquisition_20261026/cases.json.gz
python -m unittest discover -s experiments/variance_boundary -p 'test_*.py' -v
```

The exact original six-cell separation and the earlier independent-row
permutation symmetry theorem remain distinct results. A true next step is
to derive a **stopping-cost** guarantee from predictable heterogeneity under
stated model assumptions, with a validity argument that still applies to
every fixed matrix. Any proposed bound must be compared with EC² and active
testing, and a new policy must beat matched same-inference acquisition on
fresh data before a novelty claim.
