# Adaptive cell certification: theorem and novelty audit

Date: 2026-10-23. Status: research audit, **no new theorem or ICML novelty claim**.
This note audits the already implemented cell-level diagnostic against primary
papers. The existing WMT24 holdout remains untouched.

## Exact target and available actions

Fix a bounded score matrix `y[v,i] in [0,1]`, a set of systems `V`, `N`
benchmark items, and a requested comparison graph `G=(V,E)`, before target
judgments are revealed. For edge `e=(a,b)`, let

```text
T_e = sum_{i=1}^N (y[a,i] - y[b,i]).
```

One action purchases one as-yet-unobserved system--item score. It costs one
unique judgment and may update evidence for several incident edges. A strict
sign is reported only when justified; a tie or unresolved edge is reported
separately. The desired risk is the probability, *conditional on any fixed
score matrix*, that any reported strict sign is wrong at any time. Randomness
comes from the purchase mechanism. This does not cover stochastic changes in
human raters' scores unless those are included in a different estimand and
sampling model.

## Proposition: valid cell-level baseline, already in this repository

Let `F_t` include past purchases, revealed scores, predictions computed from
the past, and policy randomness. At round `t`, before revealing a new score,
draw a previously unbought cell `C_t` from an `F_t`-measurable probability
distribution `p_t`. For every still-active edge, give positive probability to
*every* unknown cell at either endpoint. The distribution cannot use any
unrevealed target score. Put `s_e(c)=+1` for a cell of `a`, `-1` for one of
`b`, and `0` otherwise; let `A_e,t` be the signed sum of purchased cells.
Then, for each active edge,

```text
X_e,t = A_e,t + s_e(C_t) y[C_t] / p_t(C_t),
E[X_e,t | F_t] = T_e.
```

The conditional equality holds for every fixed score matrix; it does not
require independence across systems or accurate predictions. Because
`y in [0,1]`, the predictable bounds

```text
L_e,t = A_e,t - max_{unknown cells of b} 1/p_t(c),
U_e,t = A_e,t + max_{unknown cells of a} 1/p_t(c)
```

contain `X_e,t`; use zero for an empty maximum. For any fixed `0<rho<1`,
the predictable stakes `lambda+ = rho/max(1,-L_e,t)` and
`lambda- = rho/max(1,U_e,t)` give positive factors
`1+lambda+*X_e,t` and `1-lambda-*X_e,t`. Under `T_e<=0` the product of
the former has conditional expected factor at most one; under `T_e>=0`
the product of the latter does too. Nonnegative mixtures over a fixed stake
grid preserve the property. Stop each directional process once its edge is
retired. Crossing `2|E|/alpha` to declare a strict sign, followed by Ville's
inequality and a union bound over the two directions of every requested
edge, gives

```text
P(any wrong strict sign is ever reported | fixed y) <= alpha.
```

The deterministic interval
`[A_e,t - #unknown_b, A_e,t + #unknown_a]` is another, zero-error way to
declare a strict sign when it excludes zero. At full exposure report the
exact contrast, including ties. The elementary result, its sanity checks,
and an inefficient uniform-purchase pilot were documented previously in
[`README.md`](README.md). It is a **baseline composition** of conditional
importance weighting, betting/e-processes, and multiplicity correction. We
must not introduce it as a new theorem without a substantive distinction.

## Definition-level related-work check

| Work | Target and acquisition | Inference and boundary relative to this task |
| --- | --- | --- |
| SAFE-EVAL Stage 20/22 | Fixed system--item matrix; a common random item order; all endpoints of active edges at each item | Pathwise label-cost dominance over scoring all systems and an anytime family guarantee. It does not adaptively buy individual cells. [Theory](../stage20/THEORY.md), [findings](../stage22/FINDINGS.md). |
| SAFE-EVAL cell baseline | Fixed matrix; adaptive purchases of *individual* unused cells with positive support | The proposition above already gives per-edge anytime evidence and a union-bound family guarantee. Its tested uniform policy **cost more** than Stage 22. [Diagnostic](README.md). |
| [Wu, Nair & Candès, FAQ (2026)](https://arxiv.org/html/2601.20251v3) | Fixed question pool; adaptively selects questions for a new model using historical factor predictions | Importance-corrected finite-pool accuracy estimator with **asymptotic** confidence intervals; its stated inference draws questions **with replacement**. No simultaneous fixed-graph pairwise sign claim. One cannot claim that adaptive finite-pool queries or imperfect predictive models alone are new. |
| [Zhou et al., CELEUS (2026)](https://arxiv.org/html/2606.20820v2) | Fixed pool; adaptively selects remaining items and uses surrogate predictions for one target model | Finite-pool, anytime-valid e-process intervals already handle adaptive sampling **without replacement**. A mere single-edge adaptation is not an original contribution. |
| [Khosravi & Huo, Rank Confidence Sequences (2026)](https://arxiv.org/abs/2609.32211) | Fixed multi-model score matrix; random **shared item order** exposes the row of scores | Simultaneous anytime rank statements and order-aware closure; the authors explicitly exclude adaptive item selection. Simply applying their closure to cell-level e-values may be useful but is a combination requiring a stronger originality argument. |
| [Badithela et al., AnyRank (2026)](https://arxiv.org/abs/2610.14603) | Adaptively allocates evaluations among robot policies for means over i.i.d. tasks | Anytime family control with graphical multiplicity and prior-guided allocation. Different estimand and acquisition model, yet adaptive allocation plus graphical testing is already studied. |
| [Gu et al., SERPANT (ICML 2026)](https://proceedings.mlr.press/v306/gu26l.html) | Online pairwise preference battles | Anytime family control for ranking with adaptive comparisons, rather than cached per-system judgments over one fixed matrix. |

These are targeted comparisons of the specific guarantees described in the
papers, not a claim that no other work covers the combination. In particular,
the missing *combination* of fixed-pool cell purchases and simultaneous
comparisons does not automatically make the elementary proposition novel.

## Result of this audit and the actual open problem

**No-go for the basic theorem as the paper contribution.** The proposition
above is already in the repository, and its validity proof uses standard
conditional means and family correction. The 2026 papers cover its major
ingredients. The Stage 22 development result (37.083% fewer unique labels
than common item blocks for reference stars) is a real gain but is not a
matched win for the adaptive cell rule. The exact three-system lookahead
diagnostic improves on one-step cell greedy by just 0.016% in its easy star
and 0% in its moderate star. Its logical completion certificate is different
from Stage 22's statistical certificate, so the lookahead's block comparison
is not a direct Stage 22 cost comparison.

A candidate worth testing would need **one clearly separate result**:

1. A nontrivial joint certificate or graph-specific cost/optimality theorem
   for *adaptive individual cells* that is not a direct reuse of existing
   importance-weighted e-processes, closed testing, or graphical testing;
   state exactly which assumption or bound it improves; **or**
2. A substantial, reproducible *matched* cost gain on independent fixed
   score matrices over Stage 22 **and** a strong cell-level baseline at the
   same requested edges, family risk, stopping objective, and judgment cost,
   with a concrete mechanism explaining where the gain arises.

For a proposed method, first write down its observable action, null, risk
event, and proof of a valid conditional increment. Then test a small fixed
pool exhaustively, including hard ties and correlated systems. Compare
*completed requested conclusions* and unique bought cells with identical
`alpha`, and report the outcomes across language pairs, shifts, and close
systems on development data. Reserve WMT24 for a frozen confirmation study
only after the method and baselines survive those checks. A 10% savings rule
may be set in advance as an internal go/no-go gate; ICML has no percentage
novelty threshold.

If the only theorem remains the proposition above and a matched gain does
not appear, close this line rather than tune it until one setting looks good.
