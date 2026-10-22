# Stage 32: when five-way panel composition changes the pairwise target

Stage 31 followed [Koehn's 2012 five-way judgment setting](https://aclanthology.org/2012.iwslt-papers.5/)
and assumed that a particular system pair has the same fresh-judgment mean
regardless of the other translations in the panel. Here we deliberately
violate that assumption. A and B receive opposite preferences when shown
beside different triplets. The outcome of interest is the A/B preference
under a specified **target mixture** of companion panels. Selecting panels
adaptively changes the distribution of observations; raw wins from that
policy can answer the wrong question.

The [protocol](PROTOCOL.md) was written before the reference simulation.
It specifies three matched policies, the target and context probabilities,
the four stakes, a two-sided anytime threshold, 500 repeats, and a 2,000
panel-task cap. [Findings](FINDINGS.md) include all stopping outcomes and
costs. This is synthetic and exploratory, not a measurement of human
panel effects or a confirmed ICML contribution.

For an adaptively chosen panel `S_t` with logged probability `q_t(S_t)`, a
bounded target-mixture signal is

```
X_t = pi(S_t) * Y_t / q_t(S_t),
M_t = max_s pi(s) / q_t(s).
```

If choice probabilities are known, strictly positive for every target panel,
chosen before a fresh independent response, and the panel-specific means
remain stable conditional on the past, then `E[X_t | past] = Delta` and
`|X_t| <= M_t`. Factors `1 +/- rho*X_t/M_t` therefore support the same
elementary one-sided e-process construction for the target `Delta` that
Stage 31 used for a context-invariant pair. Here `M_t` is predictable,
as are the policy probabilities. Replacing X with raw Y after adaptive
selection generally does not test that target. This use of inverse
propensities and anytime-valid inference is **not new**; see
[Waudby-Smith et al.](https://arxiv.org/abs/2210.10768).

Likewise, choosing comparisons adaptively was studied in
[Sakaguchi et al. (2014)](https://aclanthology.org/W14-3301/) for MT human
evaluation and [Saha and Gopalan (2019)](https://proceedings.mlr.press/v89/saha19a.html)
for ranking from subset feedback. This experiment identifies a concrete
failure mode and the real human study needed to test whether it matters for
SAFE-EVAL. The [annotation protocol](ANNOTATION_PROTOCOL.md) separates that
future measurement from this synthetic diagnostic.

From the repository root:

```bash
python -m unittest discover -s experiments/stage32 -p 'test_*.py' -v
python experiments/stage32/run_context_panels.py --repeats 500 --cap 2000 \
  --output results/stage32_development
```

The committed `results_reference/` holds `summary.json` and all per-repeat
decisions. One five-way ranking is one annotation task even though it also
defines ten dependent pair outcomes; only the A/B comparison is analyzed
here. If the task's time differs by companion group or five-way panel,
number of tasks is an incomplete cost measure.
