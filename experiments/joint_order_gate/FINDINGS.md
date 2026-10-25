# Joint finite-pool ordering tests: a local gain, failed expansion gate

**Subsequent qualification (2026-10-25):** The [stronger control audit](../joint_order_controls/FINDINGS.md)
matches these completion costs in 197 of 200 tasks by rebalancing existing
pair factors each step. Both independent strong-gap savings become 0%
against that control. The original measurements below are preserved, but
their interpretation as a distinct joint-calibration efficiency mechanism
is superseded by that audit.

Date: 2026-10-25. **Status: promising restricted mechanism; no ICML novelty
claim.** The protocol (`3098b2fe`) and validity note were published on `main`
before generating this study's matrices. The implementation and five tests
were published before the full 20-repeat run. All frozen scenarios and both
graphs are reported below; neither the seed nor the gate was revised.

## What changed

The candidate calibrates each next evidence factor against a whole possible
ordering of three binary-score systems. It eliminates orderings and reports
an individual sign only when every surviving ordering agrees. This avoids
the earlier cancellation problem: evidence that *some* comparison is false
does not identify a particular edge. The matched exact-pair control uses the
same optimizer, predictions and adaptive purchased cells, then applies order
closure to separate directional pair processes. The comparison isolates the
joint null constraints rather than different acquisition paths.

The sampler chooses a system adaptively from past outcomes, then an unseen
item uniformly within that system. It admits partial-item observations in
its history but does not exploit individual item features or arbitrary
nonuniform within-system selection. Every purchased cell costs one label
and is reused across all relevant comparisons.

## Frozen results

Mean unique purchased judgments, out of 48 available per fixed matrix.
Each setting has 20 matrices. A star requests two reference comparisons;
a triangle requests all three pairs. Every method completed every case
correctly, so raw and error-penalized costs coincide.

| Scenario | Graph | Joint ordering | Exact pair closure | Centered pair closure | Stage 22 | Joint saving vs exact pair closure |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Independent, strong gaps | Star | **29.65** | 32.45 | 35.25 | 33.50 | 8.63% |
| Independent, strong gaps | Triangle | **35.05** | 37.35 | 38.45 | 38.65 | 6.16% |
| Independent, moderate gaps | Star | **39.30** | 40.85 | 41.05 | 41.10 | 3.79% |
| Independent, moderate gaps | Triangle | **41.60** | 43.10 | 42.75 | 43.55 | 3.48% |
| Correlated, strong gaps | Star | **28.40** | 31.90 | 35.75 | 34.25 | 10.97% |
| Correlated, strong gaps | Triangle | **34.90** | 36.25 | 37.75 | 38.70 | 3.72% |
| Reversed predictions | Star | 37.90 | 37.20 | 38.10 | **34.65** | −1.88% |
| Reversed predictions | Triangle | 41.40 | 41.25 | 41.30 | **39.70** | −0.36% |
| Near ties | Star | 44.90 | 45.10 | 45.45 | **44.00** | 0.44% |
| Near ties | Triangle | 45.80 | 45.85 | 46.00 | **45.75** | 0.11% |

For independent strong gaps, the paired bootstrap descriptive 95% saving
intervals against exact pair closure are **4.26%–15.05%** (star) and
**2.29%–11.10%** (triangle). Savings against Stage 22 are 11.49% and 9.31%,
respectively. Those are measured simulated purchased-cell savings, unlike
the earlier panel-oracle proxy; they still are not observed human-time savings.

The prespecified expansion gate nevertheless **failed**. In the moderate-gap
star the Stage 22 saving is 4.38%, but its paired interval is
**−0.61% to 10.08%**, crossing zero. The rule required a positive lower
endpoint against both exact pair closure and Stage 22 in both primary
scenarios and graphs. Reversed predictions also cost 9.38% more than Stage
22 for the star and 4.28% more for the triangle. Near-tie gains essentially
vanish. These outcomes remain in the record; more repeats are not added to
move the moderate-star interval above zero.

## Sharper requested-edge control: explicitly post-result

The [additional control audit](CONTROL_CHECK.md) was declared after the
frozen run, before computing its outputs. It checks whether including the
nonrequested leaf pair diluted the star's pairwise baseline. Its requested-
edge closure is stronger in several star cases. It uses exactly the same
cell path, extending the saved prefix only if needed. Full-triangle closure
reproduces the frozen exact pair control.

| Scenario, star | Joint cost | Requested-edge exact closure | Joint saving | Descriptive paired 95% interval |
| --- | ---: | ---: | ---: | ---: |
| Independent strong | 29.65 | 32.30 | 8.20% | 3.87%–14.74% |
| Independent moderate | 39.30 | 40.80 | 3.68% | 1.23%–6.82% |
| Correlated strong | 28.40 | 31.55 | 9.98% | 4.25%–18.64% |
| Reversed | 37.90 | 36.65 | −3.41% | −6.53% to −1.28% |
| Near ties | 44.90 | 45.10 | 0.44% | 0%–1.13% |

The local aligned gain survives this stronger control, while the reversed
regression is larger. Exact-pair Bonferroni controls are also saved in
`results_reference/control_check.json`. This post-result analysis does not
turn the failed frozen gate into a pass or constitute independent validation.

## Verification and theoretical limits

- Five tests passed, covering current-outcome predictability, nonvacuous
  decisions, the reference-cancellation counterexample, exact ties, and
  Stage 22 purchase-footprint compatibility.
- The independent small-pool audit checked **216 exposure states, 4,104
  null polytopes and 7,561 factor expectations**, and enumerated **5,760**
  complete adaptive paths for all 27 total triples. These cover all 64
  three-system/two-item binary matrices. Maximum enumerated familywise
  error was zero for each cell method; this tiny check does not replace
  the conditional-supermartingale proof.
- The full result audit replayed **100 fixed matrices / 800 graph-method
  outcomes** and independently enumerated **150,768,808** null conditional
  expectations, counting repeated states encountered on different replays.
  The largest numerical value was 1.0000000000000018 (floating-point
  rounding). There were no optimizer unit fallbacks or failed solver statuses.
- A conditional validity argument is provided in [THEORY.md](THEORY.md),
  but no distinct sample-complexity, lower-bound or optimal-cost theorem
  has been obtained. Growth-optimal e-factors and order closure are existing
  ideas; the tested finite-pool construction is not automatically novel.
- Only three systems and 16 binary items were tested. Priors are synthetic,
  with favorable aligned settings. No learned historical predictor, measured
  human judgment, WMT25 outcome or WMT24 holdout was used. A prediction-aware
  complete-item control is still missing, so no claim of superiority over
  all strong block methods is supported.

## Decision

This establishes a concrete, restricted efficiency mechanism: joint null
calibration can reduce paid labels relative to separate exact pair evidence
on the same adaptive cell stream. It does **not** establish uniform cost
improvement or an ICML contribution. Keep the failed expansion gate and the
reversed-history regression visible. Before any larger performance study,
the open work is a distinct cost characterization and the missing strong
complete-item comparator, not another tuned allocation heuristic.

## Reproduce

Run from the repository root; output directories for runs must be new.

```bash
python -m pip install -r experiments/joint_order_gate/requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest -v experiments/joint_order_gate/test_joint_order.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/joint_order_gate/audit_small.py --output results/joint_order_small_audit.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/joint_order_gate/run_study.py --repeats 20 --output results/joint_order_full
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/joint_order_gate/audit_results.py --input results/joint_order_full --output results/joint_order_full/audit.json
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/joint_order_gate/check_controls.py --input results/joint_order_full --output results/joint_order_full/control_check.json
```
