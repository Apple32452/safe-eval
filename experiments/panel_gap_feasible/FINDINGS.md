# Feasible gap-aware panel screen: the oracle proxy did not transfer

The 100-repeat protocol was published on `main` at `403d4b81` before these
fresh outcome ledgers were generated. Three invariants passed, covering
finite-pool conditional unbiasedness after depletion, current-outcome
predictability, exact full evaluation, and original-control compatibility.
The independent result audit replayed **1,200** trajectories and checked
all summaries and the decision. All four methods completed every one of
the 100 paths per scenario, with no wrong sign observed. That observation
does not replace the mathematical familywise error argument.

| Synthetic scenario | Uniform raw | Uniform centered | Original adaptive all-pair | Feasible gap-aware | Candidate saving vs strongest control (paired bootstrap 95% descriptive interval) |
| --- | ---: | ---: | ---: | ---: | ---: |
| No context shift | **109.21** | 113.72 | 113.77 | 126.92 | −16.22% (−21.93% to −10.66%) |
| Context shift | 122.96 | 121.64 | **119.55** | 127.77 | −6.88% (−11.04% to −2.91%) |
| Context shift and unequal duration | 235.04 | 230.74 | **228.59** | 242.92 | −6.27% (−11.37% to −1.51%) |

Entries for the four methods are **mean capped simulated duration units to
the 11-pair completion rule**, not human minutes. The strongest original
control is chosen by the observed scenario mean, so the bootstrap intervals
are descriptive and do not adjust for that choice. In the unequal-duration
case, the candidate also used more purchased panel tasks on average than the
all-pair control: 123.20 versus 118.36. There were no infeasible numerical
updates; solver failure did not explain the cost increase.

The prespecified screen **failed** in both shifted scenarios. The earlier
`panel_oracle_gap` result found 21.26% and 18.80% mean paired *proxy*
headroom on different fresh matrices using full future outcomes. Learning a
gap-aware proposal from the 48-task pilot and refreshing it every 24 tasks
did not turn that proxy advantage into actual stopping savings. A likely
mechanism, offered as an interpretation rather than a tested causal finding,
is that optimizing a worst-pair asymptotic variance proxy can spend tasks
on difficult pairs that the 11-of-15 completion rule need not resolve;
finite-time score ranges and noisy pilot means also matter. The experiment
does not isolate those mechanisms.

This specific pilot-and-block allocation should be closed as an efficiency
claim. Changing its gap floor or update interval after seeing the result
would need a new declared development study and fresh held-out ledgers.
Neither the oracle proxy nor this failed feasible transfer supports an ICML
novelty claim. Published target-aware pooled allocation already addresses
related objectives; the remaining scientific question needs a different
guarantee or distinctive measured result, ideally with prospective human
panel judgments and recorded annotation time. No human data, WMT25, or
WMT24 were inspected for this screen.

Reproduce from the repository root:

```bash
python -m pip install -r experiments/panel_oracle_gap/requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest -v experiments/panel_gap_feasible/test_feasible.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/panel_gap_feasible/run_feasible.py --repeats 100 --output results/panel_gap_feasible_full
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/panel_gap_feasible/audit.py --input results/panel_gap_feasible_full
```
