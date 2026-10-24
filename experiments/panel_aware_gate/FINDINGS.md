# Panel-aware correction: frozen synthetic screen

Date: 2026-10-24. The protocol and implementation were recorded on `main`
before the 100-repeat run. Run `python -m unittest -v
experiments/panel_aware_gate/test_screen.py`, then `python
experiments/panel_aware_gate/run_screen.py`, then `python
experiments/panel_aware_gate/audit_screen.py`. The four algebraic and path
tests passed. The independent scalar replayer verified all 1,500 saved
trajectories and the saved summaries against the frozen protocol checksum.

## Prespecified results

Each cell is mean **simulated duration units to a correct completed**
conclusion, with the number of correct conclusions out of 100 in parentheses.
All three methods completed all 100 non-tie repeats correctly; durations
equal capped mean durations in these rows.

| Scenario | Target random | Adaptive IPW | Adaptive augmented | Internal gate |
| --- | ---: | ---: | ---: | --- |
| Unequal variance | 44.00 (100) | 45.58 (100) | **39.31 (100)** | Pass |
| Unequal duration | **53.70 (100)** | 54.86 (100) | 55.89 (100) | Fail |
| Mixed variance | 36.09 (100) | 35.82 (100) | **32.23 (100)** | Pass |
| Homogeneous | 27.71 (100) | 27.71 (100) | 28.09 (100) | Control check |

The candidate saves 10.66% and 13.76% against target random and IPW,
respectively, in unequal variance; 10.70% and 10.02% in mixed variance.
It costs 4.08% more than target random and 1.88% more than IPW in unequal
duration. The prespecified two-of-three internal gate **passed**, narrowly
in the mixed-variance comparison with IPW.

Using 10,000 paired repeat-level bootstrap resamples per comparison, the
descriptive 95% percentile ranges for the *relative* saving are:

| Scenario | Versus target random | Versus adaptive IPW |
| --- | ---: | ---: |
| Unequal variance | 3.81% to 17.07% | 7.25% to 20.11% |
| Unequal duration | -6.91% to -1.50% | -3.99% to -0.13% |
| Mixed variance | 6.01% to 15.20% | 5.62% to 14.27% |

Every favorable range crosses the 10% screening threshold; **the data do
not establish a 10% population gain**. The bootstrap is descriptive and
the scenarios were screened jointly. For the exact-tie case, positive or
negative declarations are errors: target random made 5, IPW 6, and
augmented 5 erroneous declarations out of 100, with the remaining repeats
abstaining at the task cap. These frequencies are compatible with noisy
sampling under the prespecified two-sided .05 bound; they do not validate
that bound by themselves.

## Interpretation and research boundary

The corrected signal has target conditional mean as long as each fresh
judgment's conditional context mean remains fixed, the proposal is chosen
before observing that judgment, and every target context has positive
sampling probability. The bounded betting factors then give an anytime
directional error guarantee for this **one stochastic pairwise target**.
The cost advantage here is produced with simulated duration units, not
observed annotation time. This experiment does **not** establish a
fixed-test-set finite-population guarantee, multi-pair reuse of a purchased
judgment, a comparison with Stage 22 at the same target and error budget,
or a human context effect. It leaves WMT24 untouched.

Off-policy doubly robust anytime inference and target-aware adaptive
allocation already appear in the primary literature:

- Waudby-Smith et al., *Anytime-valid off-policy inference for contextual
  bandits* (2022/2024), https://arxiv.org/abs/2210.10768.
- Hait, *Target-Aware Sequential Inference: Pooled versus Stratified
  Anytime-Valid Designs* (2026), https://arxiv.org/abs/2609.37873.

Thus the screen's passing result is **feasibility evidence, not an ICML
novelty claim**. The substantive open question remains simultaneous valid
comparisons on a fixed shared item pool, with adaptive purchases of
individual system-item judgments and measured panel-context effects. The
next honest discriminator is prospective randomized panel annotation (the
Stage 33/34 protocol), followed by a matched multi-pair comparison against
strong target-aware pooled controls with the same estimand, error budget,
and paid human minutes. Do not interpret these simulated units as minutes
or reuse already-inspected WMT25 outcomes as an independent confirmation.
