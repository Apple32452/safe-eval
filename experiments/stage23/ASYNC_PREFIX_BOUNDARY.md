# An asynchronous boundary for fixed pair certificates

This is a follow-up to the frozen Stage 23 contribution audit. It changes no
benchmark outcome, threshold, stopping rule, or WMT25 result. WMT24 has not
been inspected. The argument below strengthens the *scope of the
label-accounting result*, not the claim of paper-level novelty.

## Setup and exact minimum

Fix a finite system-by-item score matrix, a requested undirected graph
`G=(V,E)`, one random item permutation shared by all edges, and the existing
pairwise stopping certificates with fixed error allocations. On a fixed
outcome path, let `n_e` be the first prefix length at which edge `e` obtains
its certificate under the complete common stream. An edge that needs the whole
pool has `n_e=N`. These lengths are defined by the fixed pairwise evidence
paths, rather than by an acquisition schedule.

Consider *any* acquisition schedule, including adaptive asynchronous
interleavings, that must finish every requested edge using the **same
certificate at the same prefix**. The next observation for an edge is the
pair's two scores on the next item of the common permutation. An acquired
system-item score is cached and charged once, regardless of how many edges
subsequently use it. The schedule may inspect previously acquired scores when
choosing which edge to advance.

For every vertex `v`, set

```text
m_v = max { n_e : e is incident to v }, with max(empty set) = 0.
C*  = sum over v of m_v.
```

**Pathwise footprint theorem.** Every such schedule must purchase
`(v,item_j)` for each `j <= m_v`: an incident edge with `n_e >= j` needs
that score for its `j`-th paired observation. Conversely, these labels
suffice for all requested edge certificates. Thus `C*` is the exact minimum
number of distinct system-item labels for the fixed certificate paths. Stage
22's active-vertex rule purchases exactly this set. Asynchronous reordering
cannot improve its *total graph-completion label cost* under these premises,
though it can change which edge resolves earlier at an intermediate budget.

For a reference star, with center `r` and one edge `e_v=(r,v)` per leaf,
this identity is `max_v n_{e_v} + sum_v n_{e_v}`. This explains why the
Stage 22 effect can be substantial for sparse requested graphs. The formula
is a pathwise accounting identity; it is not an expected-cost optimality claim
over other tests or estimands.

## Validity under exposure from other edges

Let `I_{e,k}` be the *original* confidence set for edge `e` after the first
`k` paired observations in the precommitted common random permutation. If
it covers the true fixed-pool difference simultaneously for all `k` with
failure probability at most `alpha_e`, then any asynchronous policy that
reports a sign only when the corresponding `I_{e,k}` excludes zero obeys

```text
P(any wrong reported edge sign)
  <= P(some e,k has a noncovering original confidence set)
  <= sum over e of alpha_e.
```

This event inclusion holds even if other edges reveal later item scores before
the scheduled edge reaches that item. It does **not** say that the original
pairwise e-process remains a supermartingale in the enlarged acquisition
filtration. It relies on a precommitted uniform permutation, unchanged
per-edge prefix statistics and thresholds, and the original time-uniform
coverage event. Selecting new item orders based on revealed outcomes, or
retuning bets with information from future positions, needs a new proof.

## Independent falsification check

`audit_async_prefix.py` independently enumerates all 8 nonempty graphs on
two or three vertices, all 66 assignments of stopping rounds 1–3, and all
5,250 distinct asynchronous interleavings for those assignments. It checks
set equality of the asynchronous and synchronous acquired labels and the
vertex-maximum cost formula. `test_async_prefix.py` also compares a star
case to the existing Stage 23 synchronous enumerator, including different
within-item system orders. These checks exercise accounting; they do not
establish novelty or validate a new statistical procedure.

Run from the repository root:

```bash
python -m unittest discover -s experiments/stage23 -p 'test_*.py' -v
python experiments/stage23/audit_async_prefix.py
```

## Implication for the research decision

Simply scheduling the current edge tests asynchronously cannot improve Stage
22's total completion cost under common prefixes and fixed certificates. A
candidate method must change at least one premise, for example by constructing
a joint certificate that learns about several differences from shared labels,
or by allowing outcome-adaptive item acquisition with new design-valid
finite-pool inference. These are **research questions**, not established
contributions. A synthetic, predeclared falsification study and a matched
comparison against Stage 22 should precede any external benchmark run.

The broad goal overlaps with [AnyRank](https://arxiv.org/abs/2610.14603),
which uses active policy allocation and graphical multiple testing for i.i.d.
evaluation, and [Active Testing](https://proceedings.mlr.press/v139/kossen21a.html),
which selects test labels for efficient model evaluation. The finite-pool
confidence-sequence ingredient is covered by
[Waudby-Smith and Ramdas (2020)](https://proceedings.neurips.cc/paper/2020/hash/e96c7de8f6390b1e6c71556e4e0a4959-Abstract.html).
Further, [Wu, Nair, and Candès (2026)](https://arxiv.org/abs/2601.20251)
already give adaptive question selection with frequentist coverage for
finite-bank model accuracy, and
[Zouhar et al. (2026)](https://arxiv.org/abs/2608.03437) study dynamic
model-evaluation allocation on WMT. The joint target of anytime-valid,
multi-system fixed-pool signs with shared system-item label costs is a
candidate distinction that still needs a definition-level comparison; the
individual ingredients are not new.
The max-prefix identity must be checked against closer source-level
formulations before it is called novel; it may be an elementary corollary of
existing sample-reuse results. No ICML-level claim follows from this note.
