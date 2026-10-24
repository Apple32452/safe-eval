# A stronger human-study design, not a novelty result

Date: 2026-10-24. Stage 34 creates an **exact design-based analysis** for
the existing Stage 33 randomized five-way panel pilot. It does not add
human judgments, demonstrate panel effects, beat an active-ranking baseline,
or establish ICML novelty. WMT24 remains untouched.

## What we learned before collecting responses

Philipp Koehn's 2012 WMT-style model explicitly left open whether showing
five translations together changes their relative judgments. Stage 31's
synthetic active panel policy used 32.96% fewer five-way tasks than its
uniform-panel control, but this saving assumes the pairwise preference
target stays fixed across companion panels. Stage 32 showed a model in
which that assumption fails, and Stage 33 found no causal answer in WMT11's
historical ranking logs. Thus a randomized, fresh human experiment is the
necessary next data step; replaying completed ratings cannot reveal their
counterfactual companion-panel judgments.

For the planned 40-document, 160-task pilot, the new test conditions on
which four judges saw each document and on A/B display positions. It
enumerates the six ways to assign two of those judges to each companion
panel, then convolves the per-document distributions. The two-sided tail is
exact under the **sharp null of no companion effect on A/B preferences**,
assuming the specified randomization and no cross-task interference. It
allows the same judge to assess several different documents. This is a
standard randomization test, not a new theorem; the six unit tests check
its exact small-state error bound, balanced assignments, response integrity,
position handling, and a finite-population variance correction.

## Judgment scale

The calculation below is a **normal-approximation planning scale**, using
the conservative per-document randomization variance upper bound `4/3`
for four fixed judges and bounded preference scores. It is not measured
power, and it assumes independent document assignments and no carryover.

| Mean signed P1−P0 effect | Approx. documents for 80% power | Five-way tasks |
| ---: | ---: | ---: |
| 0.20 | 262 | 1,048 |
| 0.40 | 66 | 264 |
| 0.60 | 30 | 120 |

At **40 documents / 160 tasks**, the corresponding approximate detectable
mean effect is **0.5115** on the signed outcome scale `[-1,1]`. The pilot
can check task feasibility and possibly reveal a large effect. It cannot
reliably settle a modest 0.20 effect. A first protocol commit used an
optimistic variance bound of 1; the [pre-outcome correction](AMENDMENT.md)
records why the right worst-case bound is `4/3`. No human outcomes have been
observed for this analysis.

## Paper decision

If a controlled companion effect is measurable, the next methodological
question is whether adaptive five-way selection can preserve a predeclared
target-panel comparison at lower **measured human time** while keeping
simultaneous error control. The matched comparators must include uniform
five-way panels, direct pairs, and published active subset-ranking methods.
Simple inverse-propensity correction and Fisher testing already exist; a
paper needs a new cost/validity result or a convincing matched real-judgment
gain. If the pilot is negative or ambiguous, report it and reassess the
setting. Neither branch licenses a current ICML novelty claim.

## Reproduce

```bash
python -m unittest discover -s experiments/stage34_panel_randomization \
  -p 'test_*.py' -v
python experiments/stage34_panel_randomization/power_plan.py
```

After **all** randomized human judgments have been collected, the additional
sharp-null analysis can read the Stage 33 private key and completed response
CSV (keep both out of the public repository):

```bash
python experiments/stage34_panel_randomization/exact_test.py \
  --key results/stage33_tasks/private_key.csv \
  --responses results/stage33_tasks/responses_template.csv \
  --output results/stage34_randomization.json
```

Do not run the last command on an empty template or treat its p-value as an
average-effect interval. The Stage 33 descriptive document-level interval
remains a separate analysis.
