# Stage 25: shared-label novelty and adaptive-exposure gate

Date: 2026-10-21. This is a post-feedback literature and exact-enumeration
audit. It changes no Stage 22--24 results, reads neither WMT25 nor WMT24, and
does not claim a new paper method.

## Decision

We have **not** established an ICML-level novelty claim. The new closest
source is Khosravi and Huo, [Rank Confidence Sequences: Anytime-Valid
Leaderboards](https://arxiv.org/abs/2609.32211) (2026). It explicitly covers
the exact mean ranking of a fixed system-by-item matrix revealed in one
precommitted uniform random item order. Scores are shared across models; the
pairwise processes permit arbitrary dependence among systems; it obtains
simultaneous, anytime-valid rank and dominance statements; it also permits
retiring models under rules based on past observations. It already uses
logical relations among comparisons, including transitivity, to gain power.
These are substantive overlaps with the proposed Stage 23 joint method gate.

Zhou et al., [CELEUS](https://arxiv.org/abs/2606.20820) (2026), already
derive conditionally unbiased, surrogate-assisted signals for one finite-pool
score under adaptive unequal-probability sampling without replacement, then
construct anytime-valid e-process intervals. The basic adaptive-item
correction and surrogate control are therefore also prior work. Any proposed
combination with rank-confidence closed testing requires a distinct technical
result and a strong matched comparison; merely assembling the ingredients is
not a novelty claim.

| Candidate claim | Decision |
| --- | --- |
| Shared-item, without-replacement anytime ranks or optional stopping | Covered by rank confidence sequences. |
| Retire systems after their requested comparisons resolve | Their paper allows past-dependent model retirement; Stage 22's graph-dependent rule is a special case of this broad permission, though its footprint accounting has a different focus. |
| Transitivity or order-constrained pooling | Already covered by their exact and shortcut tests. |
| Adaptive selection of finite-pool items with a surrogate | Already in CELEUS for a single target score. |
| Joint optimization of **which system-item label** to buy next, with post-reference exposure and a graph-wide error guarantee | A possible narrower question; no distinct theorem or gain has been shown. |

The older Stage 23 and 24 notes did not include the rank-confidence paper.
Their candidate distinction should now be read with this tighter boundary.

## Exact failure of an attractive shortcut

Consider 10 fixed items: five have `(reference, candidate)=(1,0)` and five
have `(0,1)`. The complete-pool mean difference is exactly zero. The ten
items are exposed in a uniformly random order. Suppose a human scores the
reference on each item, but scores the candidate only when the current
reference score is 1. Every observed pair difference is then +1. The
candidate's score is never observed on the five unfavorable items.

`audit_adaptive_exposure.py` enumerates all `C(10,5)=252` equally likely
distinct orderings. It applies the same one-sided finite-pool betting factor
with stake `1/2` and threshold `1/0.05=20` in two ways:

| Acquisition | False directional rejections | System-item labels |
| --- | ---: | ---: |
| Full paired uniform sequence | 1 / 252 | 20 |
| Filter candidate after seeing reference, then **naively** treat retained pairs as uniform | 252 / 252 | 15 |

The latter rule has **100% false rejection probability under this fixed-pool
null**. The conditional-mean calculation for a uniformly random next pair
does not survive selection from the current reference score. Its apparent
five-label saving is invalid. This is a synthetic falsification example, not
a claim that the published methods make this error: they exclude or correct
this selection mechanism.

## Elementary safe signal, and why it is not enough

Index all system-item labels by `j`. A requested contrast has fixed
coefficients `a_j`, target `D = sum_j a_j x_j`, and unknown bounded labels
`x_j in [0,1]`. At an acquisition step, let `O` be the already observed
cells and `U` the unobserved cells. Choose predictions `m_j in [0,1]` and
full-support probabilities `q_j>0` for `j in U` using only information
already revealed. Draw `J` according to `q`, acquire `x_J`, and set

```text
B = sum_{j in O} a_j x_j + sum_{j in U} a_j m_j
G = B + a_J (x_J - m_J) / q_J.
```

Conditioning on the available information **before this draw**,
`E[G] = D` exactly, for every fixed score matrix and every predictable
choice of `m` and `q`. If `K=|B|+max_{j in U}|a_j|/q_j>0`, then `G>=-K`.
For the directional null `D<=0`, the factor `1+lambda G/K` is nonnegative
and has conditional expectation at most 1 whenever `lambda in [0,1]` is
predictable. An e-process follows by multiplication; pairwise family
control may use a conservative union bound. The script checks the exact
conditional expectation for uniform and nonuniform acquisitions after some
reference scores have already been revealed. It is an implementation sanity
check, not a proof by enumeration.

This signal is a direct linear-contrast adaptation of the strategy already
used for a single finite-pool target in CELEUS. It does not solve the
acquisition problem, the statistical power problem caused by small `q_j`, or
the comparison against existing order-constrained rank tests. In particular,
it does **not** turn Stage 24's illustrative normal-approximation findings
into significant conclusions about new items or raters.

## Next contribution gate

1. Specify whether the primary scientific target is exact conclusions on a
   fixed benchmark, or inference for new items and raters. Professor Koehn's
   significance question points toward the latter; the existing WMT25 mean
   matrices alone do not represent repeat-rater uncertainty.
2. For a fixed-pool candidate, prove a genuinely new **joint label-acquisition
   or evidence** result that uses the shared-label graph and changes the
   premises of Stage 23's max-prefix bound. A CELEUS signal applied to each
   pair plus existing rank closure is a baseline, not a contribution.
3. Compare against rank confidence sequences with model retirement, Stage 22
   pruning, and per-pair CELEUS-style acquisition under the same estimand,
   error target, and unique-label cost. Predeclare synthetic correlated,
   anti-correlated, tied, and near-tied matrices before seeing method results.
   Test weak and reversed surrogate predictions, and report unresolved
   outcomes and failures separately.
4. Inspect WMT24 only after a new theorem and meaningful matched-baseline
   savings survive this gate. Do not continue tuning the already used WMT25
   matrices to manufacture a novelty claim.

Reproduce the exact audit from the repository root:

```bash
python experiments/stage25/audit_adaptive_exposure.py
```
