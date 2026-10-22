# Stage 27: prospective item–rater estimand and two-stage baseline

This is a research gate, not an ICML contribution. No WMT24 observations
were used, and the existing Stage 17–26 results are unchanged. The
[Stage 26 rater audit](../stage26/FINDINGS.md) motivates an explicit distinction
between conclusions on the fixed WMT25 annotation bank and claims about new
items and annotators.

## Target and design

For predeclared systems `s`, let `Y_s(i,r) in [0,1]` be the score that rater
`r` would give system `s` on item `i` under a specified annotation protocol.
The target is the sign of

`Delta_ab = E_{I~P_I, R~P_R}[Y_a(I,R)-Y_b(I,R)]`.

This is a **prospective population** target. Each round independently draws
one item and one rater from the fixed, specified product distribution, before
seeing any score in that round. Both systems refer to the same drawn
item–rater pair. The simulated protocol requires a fresh, blinded judgment
in each round and charges it even if an item–rater index recurs; neither
method caches earlier judgments. That cost definition is a limitation of this
sanity experiment. Results may be monitored and annotation may stop at any
round. Familywise false directional conclusions must have
probability at most 0.05; ties may remain unresolved.

WMT25's existing human file records a fixed, nonprospective assignment of
annotators. Its 158 aligned-panel annotator IDs and common controls do not
certify that those IDs are an iid sample from a specified population of
future annotators. This script therefore uses **synthetic** item–rater
populations only. A WMT25 replay would answer a different question.

## Two-stage baseline and elementary proof

On each fresh item–rater draw, acquire the reference score `A`. For each
active comparison candidate with potential score `B`, choose a prediction
`m in [0,1]` and query probability `q >= epsilon = 0.25`, using earlier
rounds, the current item/rater identity, and the already observed `A`.
Neither choice may use the current `B`. Independently query the candidate
with `Z ~ Bernoulli(q)` and form

`G = A - m - (Z/q)(B-m)`.

Conditional on the entire drawn item–rater pair, its potential scores, and
the pre-query history, `E_Z[G] = A-B`. Averaging the **fresh iid pair draw**
then gives `E[G | previous completed rounds] = Delta_ab`. The distinction
between these two conditioning steps matters: a population-null bet must
be chosen before the current pair draw. It cannot be retuned after seeing
`A` merely because the query propensity is allowed to depend on `A`.

For `q >= epsilon`, `|G| <= 1/epsilon`. Under the positive-direction null
`Delta_ab <= 0`, each precommitted factor `1 + rho*epsilon*G` for
`0 <= rho < 1` is nonnegative with conditional mean at most one.
The opposite direction uses `-G`. A mixture of precommitted stakes,
multiplied over completed rounds, is an e-process. With `M` requested
undirected edges, each of its `2M` directions crosses at `2M/0.05`;
Ville's inequality and the union bound give familywise directional error
at most 0.05 under arbitrary within-round system dependence. This is a
direct application of established inverse-propensity and anytime-valid
off-policy ideas, not a new theorem.

The paired control sees both scores every active round and uses the **same**
mixture stakes, threshold, iid item/rater ledger, and requested star graph.
Its signal is `A-B in [-1,1]`; the two-stage process uses `G` with
normalization `1/epsilon`. The two-stage prediction is a smoothed running
candidate mean for the current reference-score stratum. Its propensity is
one after `A=1` and `epsilon` after `A=0`. This intentionally tests
current-score-dependent label selection with known full support.

## Audits and reproduction

`audit_stage27.py` enumerates 4,401 binary null/probability/prediction
settings to check conditional expectations and betting factors. On a tied
four-type population, filtering pairs using that propensity yields a **naive
selected-pair mean of +0.6**, while the corrected signal has mean zero.
The audit also records two future-rater populations that agree on every
observed rater but have opposite population signs; no new-rater sign is
identified by a fixed nonrandom rater panel alone.

The synthetic study fixes 32 items, 6 raters and 3 systems per scenario,
with 100 independent item/rater ledgers and a maximum of 800 rounds per
ledger. It compares aligned, weak, reversed and tied populations. An
unresolved run at the cap is reported as unresolved, never as a successful
low-cost conclusion. See [FINDINGS.md](FINDINGS.md) and
[RESULTS.json](results_reference/RESULTS.json).

From the repository root:

```bash
python -m unittest discover -s experiments/stage27 -p 'test_*.py' -v
python experiments/stage27/audit_stage27.py --repeats 100 --max-rounds 800 \
  --output results/stage27_local
```

This elementary construction is covered in spirit by
[anytime-valid off-policy inference](https://arxiv.org/abs/2210.10768).
The closest ranking comparisons also include
[rank confidence sequences](https://arxiv.org/abs/2609.32211),
[BB-EDGE](https://arxiv.org/abs/2609.32248), and
[hierarchical rank intervals](https://arxiv.org/abs/2606.08679).
Those papers have different data designs, but are comparison obligations
before claiming anything new. This pilot does not implement their stronger
procedures, so it cannot establish superiority to them.
