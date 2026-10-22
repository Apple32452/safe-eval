# Stage 30: prospectively sampled reference-star cost gate

This synthetic pilot is frozen before its 100-repeat run. It tests whether
the Stage 29 local variance advantage survives **paid online prediction,
anytime evidence, and edge retirement**. It is not an ICML contribution or
an inference claim about the nonrandom WMT25 rater panel. WMT24 is untouched.

The population contains 18 fixed binary-score systems, 64 items, and eight
rater types. Each round draws an item/rater index uniformly and independently
with replacement. The target for each of 17 predeclared reference-star edges
is the sign of the population mean difference under this index distribution.
Each blinded system/item/rater judgment costs one label, even if an index
reappears; we do not cache repeated ratings. This is a prospective repeat-
judgment cost model, not the fixed-label cache used in Stage 22. One current
reference judgment is shared by all active star edges. The candidate score
is purchased only when its edge remains active. All methods share an
item/rater ledger. Their query coins are independent of unobserved scores.

The methods are `paired` (all active candidates), `partial` (each active
candidate independently with probability `0.75`), and `degree_switch`
(`0.75` while more than four candidate edges are unresolved, otherwise
full paired). Partial methods learn separate smoothed candidate score
predictions conditional on the current binary reference score, solely from
their previously purchased candidate labels. All training judgments are
included in cost. The degree threshold and probability were selected from
Stage 29's WMT25 development diagnostic; they are frozen before this
synthetic evaluation. These are simple known propensity-correction and
fixed-mixture betting ingredients, not a claim of new inference.

For candidate `j` and round `t`, prediction `m_j(a)` and probability `q_j`
are fixed from past rounds. After observing the current reference score `a`,
the corrected signal is `G_j=a-m_j(a)-Z_j(B_j-m_j(a))/q_j`. The query coin
has conditional expectation `E[G_j | item,rater,reference,past]=a-B_j`.
The prospective iid item/rater draw then gives conditional mean equal to
the target difference. Pre-draw lower and upper signal bounds make each
predictable positive or negative betting factor nonnegative. A mixture of
four predeclared stake processes is an e-process. Each of the 34 edge
directions gets threshold `34/0.05=680`; a union bound gives familywise
false directional probability at most 0.05 under this sampling and cost
design. An unresolved edge at the 2,000-round cap stays unresolved; it is
never counted as an inexpensive conclusion.

Scenarios are shared-latent easy, shared-latent weak, independent-latent,
long-tail star, and an exact-tie control. Each receives 100 seeded ledgers;
all methods have the same 2,000-round cap. A non-tie scenario passes only
if the partial or degree-switch method completes at least as many runs as
paired, makes no excess false declarations in these replications, and
saves at least 10% mean paid judgments **to complete**. The overall pilot
gate requires three of four non-tie scenarios to pass. Even a pass only
licenses a comparison with strong published off-policy and rank-confidence
procedures; it does not establish novelty or worst-case error empirically.

Run from the repository root:

```bash
python -m unittest discover -s experiments/stage30 -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage30/run_star_gate.py \
  --repeats 100 --rounds 2000 --output results/stage30_local
python experiments/stage30/analyze_star_gate.py --input results/stage30_local
```
