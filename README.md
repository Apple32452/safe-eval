# SAFE-EVAL

**Latest research:** [Stage 33](experiments/stage33/FINDINGS.md) checks real WMT11 five-way judgments. The matched reference-presence contrast is small and its descriptive interval includes zero; 40 public WMT25 documents are prepared for a prospective English-to-Chinese human pilot, but no new judgments have been collected. See the [pilot protocol and commands](experiments/stage33/README.md). [Stage 32](experiments/stage32/FINDINGS.md) is a synthetic context-shift diagnostic. ICML novelty remains unestablished.

SAFE-EVAL studies how to reach reliable conclusions about machine translation
systems while paying for fewer system-item judgments on a fixed test set. It
combines sequential confidence sequences with shared labels: one judged system
output can support several requested pairwise comparisons.

The [released Stage 7 snapshot](experiments/stage7/README.md) remains intact.
Subsequent experiments and audits are recorded in separate stage directories.

## Latest result and research boundary

[Stage 22](experiments/stage22/FINDINGS.md) evaluates a sparse reference-star
task on WMT25: compare each system with a designated reference, over all 255
possible references and 14 language directions. Pruning systems whose requested
comparisons have resolved reduced the equal-language mean completion cost from
3,557.61 to 2,250.62 unique labels (**37.083% fewer**; conditional Monte Carlo
standard error 0.032 percentage points). All 12,750 reference tasks improved,
and the final pairwise decisions matched the common-test-set control.

[Stage 23](experiments/stage23/README.md) audits the contribution. Its checked
claim is limited to synchronous common-prefix policies that advance every
unresolved requested comparison on the next item: acquiring exactly the vertices
incident to unresolved edges is itemwise label-minimal in that class. The
[independent audit](experiments/stage23/PRELIMINARY_AUDIT.md) enumerates 98,664
small resolution schedules and 443,238 per-edge dominance cases. Broad claims
about graph-aware ranking or global sample optimality are unsupported by this
result. The closest-work comparison and contribution gate remain open; WMT24
external confirmation has not been run. The 37.083% saving is development
evidence for the specified sparse task, not a universal ranking result.

## Set up on your Mac

From the repository root with Python 3.9 or 3.12 and an activated environment:

```bash
python -m pip install -r requirements.txt
python scripts/check_release.py
for stage in {7..23}; do
  python -m unittest discover -s "experiments/stage${stage}" -p 'test_*.py' -v
done
python experiments/stage23/audit_stage23.py
```

The test loop covers 122 invariant tests across Stages 7–23; the final command
runs the independent Stage 23 exhaustive audit. See the
[asynchronous boundary](experiments/stage23/ASYNC_PREFIX_BOUNDARY.md) for the
fixed-certificate cost formula and its separate exhaustive check. No GPU is required. GitHub
Actions runs the full test suite on Ubuntu (Python 3.9 and 3.12) and macOS
(Python 3.12), with additional saved-result audits and smoke checks. See the
[workflow](.github/workflows/checks.yml) for the exact automated checks.

## Reproduce the fixed Stage 7 comparison

Run each command after the previous one finishes:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage7/run_stage7.py --repeats 100 --workers 2 --output results/stage7_local
python experiments/stage7/analyze_stage7.py --input results/stage7_local
```

The complete run saves 117,000 method trajectories. Analysis checks 35,100
reserved stopping bounds and matches 11,700 Stage 6 raw stops. Full saved
curves and per-trial data are generated locally rather than committed.

For a smaller installation check:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage7/run_stage7.py --repeats 1 --workers 2 --output results/stage7_smoke
python experiments/stage7/analyze_stage7.py --input results/stage7_smoke
```

The one-repeat run is a software check. It does not reproduce the fixed
100-repeat Stage 6 pairing or supply new research evidence.

## Current research status

- Stage 6's primary extra-query policy increased paid query cost overall.
- Stage 7's unchanged 75% raw-capital reserve reduced aligned-history mean
  query cost by 7.428% with equal weighting of the three languages. German
  cost increased by 0.871%; Hebrew and Chinese costs fell by 9.121% and 8.577%.
- Stage 7/8's reserve stopping bound is against the stricter **96.25% raw
  control**. That reserve construction does not guarantee lower cost than
  the ordinary 95% raw control.
- All Stage 7 queries are uniform without replacement. Prediction changes
  inference, not acquisition. ICML novelty remains unresolved.
- Stage 8's matched zero-trust ablation is complete: enabling aligned history
  reduces reserve query cost by 6.815% versus the otherwise matched control.
  The reversed-history primary instead adds 0.075% on average. See the
  [Stage 8 findings](experiments/stage8/FINDINGS.md) and fixed
  [protocol](experiments/stage8/PROTOCOL.md).
- Stage 9 supplies a separate ordinary-raw95 stopping safeguard using exact
  finite-state calibration and error allocation. Its fixed aligned comparison
  saves 2.801% versus raw95, 2.798% versus matched zero, and 1.141% versus
  integer-grid calibrated raw95. German and both adverse-history conditions
  lose to calibration. See the [Stage 9 findings](experiments/stage9/FINDINGS.md).
- Stage 10's finer calibrated control reduces the aligned prediction advantage
  to 0.666%, or 1.813 labels per benchmark. Prediction improves 18 target means
  and worsens 21; both adverse histories favor calibration. Larger-pool exact
  repair calibration remains unfinished. Stage 11 checks the remaining gain
  against published sequential boosting. See the [Stage 10 findings](experiments/stage10/FINDINGS.md).
- Stage 11 completes that published boosting comparison on the same PPR
  process. The aligned prediction gain shrinks to 0.341% (0.925 labels), with
  15 target mean wins and 24 losses. Both adverse histories favor boosting;
  the worst extra cost is 260 labels. See the [audited Stage 11 findings](experiments/stage11/FINDINGS.md).
- Stage 12 reviews the closest prior work and checks a finite-assignment
  boosting calculation with exact arithmetic. Substantial overlap blocks the
  broad novelty claims; the checked extension is not an established new
  method. A finite-pool label-cost guarantee remains an unresolved research
  target. See the [contribution audit](experiments/stage12/NOVELTY_AUDIT.md).
- Stage 13 studies a separate MT-facing objective: recovering fixed-benchmark
  pairwise system conclusions using fewer paired target judgments. All 237
  system pairs are included, with both targets excluded from history and
  separate per-pair and family-wide error settings. See the
  [locked protocol and reproduction commands](experiments/stage13/README.md).
  Its audited paired-PPR baseline uses 68.8614% of each pair's full budget on
  average under the family-wide setting, with no observed wrong decisions in
  11,850 query-order trials. Historical added value remains unestablished, and
  the reserve's family-wide component cap needs correction before efficiency
  conclusions. See the [Stage 13 findings](experiments/stage13/FINDINGS.md).
- Stage 14 is an exploratory shared-annotation scheduling pilot on the same
  WMT23 binary outcomes. At half of the unique-label budget, evidence priority
  certifies 28.25/237 pairs on average over 12 order blocks, versus 23.08 for
  fixed pair focus and 16.33 for random pair focus. Most pairs remain
  unresolved; the two concentration controls were added after the initial
  pilot. See the [Stage 14 findings and reproduction](experiments/stage14/README.md).
- Stage 15 tests a locked annotation-level frontier utility over 50 matched
  WMT23 order blocks. Its primary 50% gain over evidence-first is only 0.82
  certified pairs (conditional MC SE 0.664); at 75% the gain is 10.80 pairs.
  This is a development candidate, not an ICML contribution. See the
  [Stage 15 findings](experiments/stage15/FINDINGS.md).
- Stage 16 externally validates that unchanged scheduler on 14 WMT25 language
  directions and 2,197 system pairs. At the frozen 75% label budget it gains
  76.76 correctly certified pairs over evidence-first (conditional MCSE 5.44),
  wins 49/50 matched blocks, has positive means in all 14 languages, and has
  zero observed wrong declarations. The external gate passes. This supports
  the scheduling effect but does not yet supply the needed theorem, practical
  score margin, or matched active-ranking baselines. See the
  [Stage 16 findings](experiments/stage16/FINDINGS.md).
- Stage 17 tests a continuous WMT25 mean-score target and supplies the
  scheduler-independent validity and allocation formulation. At 75% labels,
  frontier evidence gains 12.82 correctly certified pairs over evidence first
  (MCSE 1.68), with zero observed wrong declarations and positive mean gains in
  11 of 14 languages. The frozen gate passes. The random-label control is
  structurally weak, so a common random test-set baseline is required before
  claiming an ICML contribution. See the
  [Stage 17 findings](experiments/stage17/FINDINGS.md).
- Stage 18 adds the missing common random test-set baseline. At 75% labels,
  the frontier scheduler certifies 1,122.80 correct pairs versus 1,275.70 for
  the common test set: a deficit of 152.90 (MCSE 2.07), with losses in all 50
  repeat blocks and zero observed wrong declarations for both methods. The
  frozen gate fails, rejecting the current scheduler as the ICML candidate.
  See the [Stage 18 findings](experiments/stage18/FINDINGS.md).
- Stage 19 retains a 50% common core before adaptively scheduling separate pair
  tails. It gains 7.92 conclusions at the 50% checkpoint but loses 104.76 at
  75% (MCSE 1.57), with losses in all 50 repeats and zero observed wrong
  declarations for both methods. The gate fails, ruling out further WMT25
  tuning of common/pair-specific mixtures. See the
  [Stage 19 findings](experiments/stage19/FINDINGS.md).
- Stage 20 stays on the common stream and removes systems only after all their
  incident comparisons resolve. It pathwise weakly dominates the unpruned
  control and gains 8.48 correct conclusions at 75% labels (MCSE 0.32), winning
  all 50 repeats with zero observed wrong declarations. Only six of 14 language
  means improve, so the frozen breadth gate fails and the 0.665% effect is not
  an ICML empirical contribution. See the
  [Stage 20 findings](experiments/stage20/FINDINGS.md).
- Stage 21 uses a disjoint 25% pilot to select an adjacent comparison chain,
  tests it with a conditionally valid finite-pool e-process, and applies
  transitive closure. At 75% labels it produces only 37.04 correct conclusions
  versus 1,275.70 for the all-pair common baseline, losing all 50 repeats and
  every language mean. The gate fails and closes this WMT25 candidate. See the
  [Stage 21 findings](experiments/stage21/FINDINGS.md).
- Stage 22 tests the Stage 20 theorem on a practical sparse objective: compare
  every candidate system with a designated reference, averaged over all 255
  possible WMT25 reference systems. Active-vertex pruning reduces the
  equal-language mean completion cost from 3,557.61 to 2,250.62 unique labels,
  a **37.083% saving** (conditional MCSE 0.032 percentage points). All 12,750
  reference tasks and all 14 language means improve, final decisions agree
  exactly, and the audit finds zero edge-level dominance violations. The graph
  density diagnostic falls from 37.083% for stars to 3.004% for complete
  graphs, matching the theorem's mechanism. This is strong development
  evidence, but closest-work novelty and untouched WMT24 confirmation remain
  open. See the [Stage 22 findings](experiments/stage22/FINDINGS.md).
- Stage 23 freezes the paper-level contribution audit before any WMT24 access.
  The current defensible theorem candidate is restricted: Stage 22 pruning is
  itemwise label-minimal among synchronous common-prefix policies that advance
  every unresolved requested edge. An independent enumerator verifies 98,664
  small resolution schedules and 443,238 per-edge dominance cases. AnyRank and
  classical common-random-number ranking block a broad graph-ranking novelty
  claim, so the contribution audit remains open. See the
  [Stage 23 protocol](experiments/stage23/PROTOCOL.md) and
  [preliminary audit](experiments/stage23/PRELIMINARY_AUDIT.md).

See the complete [Stage 7 findings](experiments/stage7/FINDINGS.md),
[Stage 6 findings](experiments/stage7/STAGE6_FINDINGS.md),
[theory](experiments/stage7/STAGE5_THEORY.md) and
[next research question](experiments/stage7/NEXT_RESEARCH_QUESTION.md).

## Data and reference results

The bundled public WMT23 extracts contain recorded binary error-free scores
for three fixed annotated pools. This derived outcome is distinct from the
official severity-weighted MQM score. Synthetic permuted and reversed histories
are stress tests. The detailed filtering, upstream commit, hashes and source
license are in [data provenance](experiments/stage7/data/DATA_PROVENANCE.json)
and [the upstream license](experiments/stage7/UPSTREAM_LICENSE.txt).

The compact [reference results](experiments/stage7/results_reference) include
tables, figures and the completed audit. They omit full per-trial curves and
cannot be passed directly to the analyzer. No private Hayden/Carey data are
included.

## Working on GitHub

Follow [the setup instructions](docs/GITHUB_SETUP.md) to clone the working
repository and continue development. The workflow runs on pull requests and
pushes to `main`; it checks release integrity, invariant tests, saved-result
audits and smoke runs. Its configuration follows
[GitHub's Python workflow documentation](https://docs.github.com/en/actions/tutorials/build-and-test-code/python).

Keep the released experiment intact. Put new research stages in a new
directory and record their own protocol and evidence before comparing results.
The default working branch is `main`; future changes can use branches and pull
requests. The working repository is [Apple32452/safe-eval](https://github.com/Apple32452/safe-eval).
The submitted Mac reproductions are documented for
[Stage 7](docs/MAC_VERIFICATION.md) and
[Stage 8](docs/STAGE8_MAC_VERIFICATION.md).

## Reproduce Stage 8

From the repository root:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage8/run_stage8.py --repeats 100 --workers 2 --output results/stage8_local
python experiments/stage8/analyze_stage8.py --input results/stage8_local
python experiments/stage8/report_details.py --input results/stage8_local
```

Use a new output directory for each run. Stage 8 imports the frozen Stage 7
modules and public data. Its reference tables and figure are included, while
large per-trial files and full curves are generated locally.

## Stage 9 ordinary raw95 safeguard

Stage 9 uses exact finite-state calibration to allocate spare raw error
probability to a prediction confidence sequence. The returned interval is
contained in unchanged raw95, with fallback equality when needed. This
supplies an ordinary-raw95 stopping bound under the stated uniform-sampling
and arithmetic assumptions. The fixed development comparison includes matched
zero-trust and calibrated raw controls. The aligned mean gain versus calibrated
raw is modest and uneven; no ICML novelty is established.

See the [instructions](experiments/stage9/README.md),
[protocol](experiments/stage9/PROTOCOL.md), [theory](experiments/stage9/THEORY.md)
and [findings](experiments/stage9/FINDINGS.md). Generate fresh certificates for
the runtime before reproducing the fixed comparison:

    python experiments/stage9/certify_stage9.py --output results/stage9_certificates
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage9/run_stage9.py --certificates results/stage9_certificates --repeats 100 --workers 2 --output results/stage9_local
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage9/analyze_stage9.py --certificates results/stage9_certificates --input results/stage9_local

The audit can take substantially longer than the run because it rebuilds
capital and raw PPR intervals from every query. It prints an `Audited ...`
line for each completed case. The committed compact reference package omits
the full curves required by the analyzer; see
[reference file details](experiments/stage9/REFERENCE_FILES.md).

## Stage 10 stronger-calibration and novelty study

Stage 10 preserves all Stage 9 prediction paths and adds a finer calibrated
PPR control, with an exact repaired-control investigation and a focused
primary-source novelty review. It reuses a complete audited 100-repeat Stage 9
run. Read the [Stage 10 instructions](experiments/stage10/README.md),
[protocol](experiments/stage10/PROTOCOL.md), [theory](experiments/stage10/THEORY.md)
and [novelty review](experiments/stage10/NOVELTY_REVIEW.md). Full source curves
are required; the compact archived summaries cannot replace them.
The [audited findings](experiments/stage10/FINDINGS.md) and
[reference package](experiments/stage10/results_reference) report the completed
comparison and its limits.

## Stage 11 published sequential-boosting baseline

Stage 11 applies Fischer and Ramdas's published sequential-boosting algorithm
to the same PPR process, with conservative integer updates and inversion of
every candidate total. It preserves the complete audited Stage 9/10 outputs.
See the [instructions](experiments/stage11/README.md),
[fixed protocol](experiments/stage11/PROTOCOL.md) and
[numerical argument](experiments/stage11/THEORY.md). This is a baseline study,
not a new method or an established novelty claim.
The [findings](experiments/stage11/FINDINGS.md) and
[reference results](experiments/stage11/results_reference) include the completed
audit, all paired comparisons, diagnostics and a figure.
