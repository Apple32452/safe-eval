# Certificate-guided cell acquisition: independent follow-up

Frozen before generating target matrices on 26 October 2026. The previous
peer-cell 3-system by 64-item one-hot study is development data and is not
reused in the primary result. This is an empirical screening study, not a
new theorem or a claim of ICML novelty.

## Fixed task

Scores are fixed binary K-by-N matrices. Report the signs of two comparisons
between system 0 and systems 1 and 2, including exact ties, at familywise
error alpha=0.05. A purchased cell is charged once and shared across the
comparison histories. Each method gets the same synthetic target, separate
2048-column historical bank, and seeded acquisition stream. Wrong or
unfinished output is charged K*N. Report paid and charged cells separately.

## Acquisition rule

Use the existing categorical historical column predictor and the existing
conditional null-calibrated e-factors from `peer_cell_scale` without changing
their null or stopping threshold. Given a current history, first construct
the original `row_peer` distribution q0. For every unresolved comparison,
calculate both directional e-factors using q0. At every eligible unobserved
cell c, calculate its predicted expected log factor

    u(c) = sum_direction max(0, p_c log f_c(1) + (1-p_c) log f_c(0)).

Multiply each comparison's contribution by the established urgency
1/max(predicted absolute total gap / N, 0.1), and sum across comparisons.
Draw the next cell from 0.2*uniform + 0.8*normalized(u), reverting to
uniform if all utilities vanish. Recompute the certified factors with this
actual draw distribution before observing the cell; the q0 factors are used
only to define the predictable acquisition score. Never use a current
unobserved target outcome to set its own score or selection probability.

## Independent screen and fixed gate

Primary: 60 new one-hot reference-star matrices with K=3,N=128 using a
distinct SHA256 seed prefix `20261026|certificate_acquisition|` and repeats
0..59. Historical bank and target sampled independently from the one-hot
distribution defined in peer_cell_scale/study.py. Diagnostics: 20 independent,
20 opposed, 20 reversed-history cases at K=3,N=128; these are all reported.

Run `certificate` versus `row_peer`, original `peer_cell`,
`paired_exact_closure`, and `stage22` on each identical case. Original methods
retain their prior implementations and seeds. Use 20,000 paired bootstrap
resamples, Bonferroni-adjusted percentile intervals across the four primary
controls (two-sided family level .05). The empirical gate passes only when
the lower adjusted saving bound is strictly above zero against *each* of
the four controls, with audits passing. This gate is deliberately more
stringent than merely beating Stage22. Diagnostic effects are not a gate and
cannot be substituted for a failed primary.

The reverse history is misspecified intentionally. No human judgments or
WMT labels are used. Bootstrap intervals express variation across synthetic
cases, not the anytime error guarantee. Do not retune this policy after
inspecting outcomes from this locked screen.

## Checks

Before the main run, test predictable probabilities under hidden-current-bit
changes, positive overlap, exact null calibration, paired-seed controls,
unique purchases, ties and final completion. Replay each saved paid ledger
and conditional factor against its true fixed-matrix null. Publish every
method and diagnostic, including any failed gate.
