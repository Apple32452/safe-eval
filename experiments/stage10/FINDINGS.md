# Stage 10: what survives finer calibration?

The independent benchmark and certificate audit passed.

Finer model-free calibration reduces the aligned-history prediction advantage
from 1.141% to 0.666%, or about 1.81 target labels per benchmark. Roughly 42%
of the previous absolute mean-label advantage disappears when the comparison
control is improved. The remaining gain is heterogeneous: 18 target means
improve and 21 worsen; German and both adverse histories favor calibration.
This is useful development evidence about a limited effect, not an
established publication contribution.

## Fixed comparison and source reuse

Implementation, protocol and the canonical source-trace manifest were frozen
at f163038f4fadc00d50609a565b4952429671f751 before examining the new paired
benchmark comparisons. The parent main commit is
90b44f3175568704f37a3703d086f27b26437a19. All prior stage files are preserved.

The comparison retains all 117 Stage 9 cases, 100 repeats, unchanged predictors,
trust, stakes, alpha allocations, precision and query paths. The 46,800 source
method trajectories are reused after verifying their completed capital audit,
full file hashes, query ledgers, all saved decisions and all 2,340 metric
values. Two controls add 23,400 trajectories, for 70,200 compared trajectories.
The new study does not collect new labels or repeat the unchanged historical
prediction-capital experiment. WMT23 remains development data.

All overall means weight languages equally, then systems equally within each
language. They condition on the same recorded binary outcomes and historical
matrices; they do not measure transfer to new benchmarks or annotators.

| History | Ordinary raw95 | Stage 9 integer calibration | Fine/selected repaired calibration | Unchanged prediction |
| --- | ---: | ---: | ---: | ---: |
| Aligned | 278.006 | 273.337 | 272.031 | 270.218 |
| Permuted | 278.006 | 273.337 | 272.031 | 277.991 |
| Reversed | 278.006 | 273.337 | 272.031 | 277.999 |

The selected repaired control equals the fine control at all three pool sizes.
It is not globally optimized repaired calibration: the larger exact counts
were capped, and only the fixed small grid was examined in the completed pool.

| Aligned language | Prediction minus selected control: labels | Relative change | Conditional MCSE: labels |
| --- | ---: | ---: | ---: |
| en-de | +1.987 | +1.610% | .110 |
| he-en | -3.803 | -0.935% | .635 |
| zh-en | -3.622 | -1.267% | .435 |
| Equal-language overall | -1.813 | -0.666% | .273 |

Negative changes mean fewer labels. The mean advantage exceeds its conditional
query-randomization Monte Carlo uncertainty on these fixed pools. That is not
evidence of new-data generalization. Historical annotation, human time and
computation costs are excluded from the label-cost endpoint.

Prediction improves nine of twelve Hebrew target means and nine of fifteen
Chinese means. It worsens all twelve German means, three Hebrew means and six
Chinese means. There are no target mean ties against the selected control.
Under permuted and reversed histories, prediction adds 2.191% and 2.194%,
respectively, and loses on all 39 target means in each condition.

The largest observed extra cost of prediction versus the selected calibrated
control is 188 labels. The ordinary-raw95 pathwise bound remains the same
Stage 9 bound; it does not imply a bound against the stronger calibrated
controls. Neither a better average nor nominal coverage licenses omitting
these unfavorable paths.

## Mathematical calibration and repair investigation

| N | Earlier integer threshold | Fine safe threshold | Fine worst-case error | Unsafe endpoint error |
| --- | ---: | ---: | ---: | ---: |
| 154 | 16 | 15.390380859375 | .049255909796 | .050800841499 |
| 589 | 17 | 16.828125000000 | .049579861350 | .050512848543 |
| 820 | 18 | 17.011962890625 | .049773096332 | .050075150205 |

Every unsafe endpoint is exactly 1/4096 below the safe endpoint. Twelve
predetermined dyadic bisections use only N and the implemented PPR rule.
Risks are exact integer fractions over all totals K; the displayed decimals
are rounded. This is a refined threshold in one family, not the strongest
possible model-free confidence sequence or a continuous global optimum.

Initial resource checks used 100,000 states and five million transitions.
Before the benchmark comparison, their capped attempts were preserved and the
final fixed limits increased to one million states and twenty million
transitions for all three pool sizes. No benchmark costs informed that change.

For N=154, all four exact repaired counts completed. The repaired worst error
at the fine threshold is .049255528036, only about 0.000000382 below the
unrepaired error. The three lower thresholds, fine minus 1/2, 1/8 and 1/64,
have repaired worst errors .051180244375, .050910110467 and .050800413270.
All exceed .05, so none can replace the certified fine threshold.

For N=589 the count exhausted twenty million transitions after 73 layers with
522,272 peak states. For N=820 it stopped after 69 layers with 666,724 peak
states. These are incomplete computations, not repaired error certificates.
The lower probes were skipped as specified in the protocol. Both controls
therefore retain their valid unrepaired fine threshold. No unknown repair
slack was spent. The larger-pool repair-calibration question remains open.

The full-control construction retains the ordinary-raw95 stopping safeguard:
its output is a subset of raw95 or fallback equality, and its certified
full-path error is at most .05. Simply replacing raw95 by fine_raw95 inside
the prediction intersection would require a new error allocation or joint
proof; the old prediction allowance was certified relative to ordinary raw95.

## Coverage and validation

Equal-language full-path empirical coverage is 95.639% for both new controls,
versus 96.483% for unchanged prediction. Stopped midpoint error exceeds .05
in 4.028% of new-control paths and 3.261% of prediction paths. Empty-ever rate
is 3.150% for both, and no output fallback occurs before its reported precision
stop in this run. All conditions retain these full-path failures; exact final
means do not erase earlier exclusions. These empirical frequencies are not
the proof of validity.

The independent audit checked all 70,200 saved decisions, including 46,800
reconstructed source decisions, all 2,340 preserved Stage 9 metric values,
3,510 total target metric values, 1,568 backward fine-risk counts, four complete
repaired-risk certificates, 23,400 ordinary-raw95 stopping bounds, and
12,313,800 new-control query replay steps. The canonical source manifest
matched. The original prediction-capital audit was reused, not repeated.
Audit runtime was 243.3 seconds. All twelve primary language/history contrasts
were independently reconstructed from per-trial costs and matched the frozen
analyzer, including MCSEs, target wins/losses and worst-path extra labels.

The new comparison took 34.1 seconds using the audited source run. All six
new tests passed, including exhaustive small-string repaired-risk counts,
independent explicit-state counts, capped-count rejection, exact dyadic
brackets, nested-set fallback behavior and control replay/containment.
The 49-test repository suite also passes on GitHub's Ubuntu 3.9/3.12 and
macOS 3.12 checks for the frozen implementation.

The compact result package includes these findings, calibration certificates,
comparison tables, a figure, source fingerprints and the completed audit.
Full curves and per-trial outputs are generated locally using the documented
commands; they are omitted from the committed reference package.

## Research decision

The previous positive effect partly reflected coarse model-free calibration.
A smaller aligned benefit survives this specific refinement, while most
target means and both adverse histories favor the control. The result does
not justify scaling a claim of broadly superior annotation efficiency.

The focused NOVELTY_REVIEW.md identifies substantial prior work: prediction-
powered anytime inference, finite-population betting, distribution-specific
boundary calibration, and sequential boosting that already supplies
never-later tests with without-replacement extensions. Those sources do not
automatically settle equivalence of our full implementation, but prevent
treating its ingredients or a generic never-later statement as new.

The next technical comparison should assess the applicable sequential-
boosting baseline, including numerical validity and confidence-set inversion,
and resolve whether there is a substantial distinct contribution with
Professor Philipp Koehn. Larger repaired calibration remains computationally
unfinished. Lock a genuinely uninspected confirmation pool only after the
methodological case survives; do not relabel inspected WMT24 as untouched or
keep tuning this benchmark until its outcome looks better.
