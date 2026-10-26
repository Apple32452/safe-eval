# Shared-comparison variance allocation: frozen screen

Frozen 26 October 2026, before the primary synthetic target matrices were
generated. This is a follow-up to the negative `certificate_acquisition`
screen and the variance-proxy boundary. It tests a new allocation against
same-inference row-uniform and earlier cell-selection controls. A gain in a
one-step proxy is not a cost theorem and this screen cannot alone establish
ICML novelty; prior active testing and EC² overlap with the design.

## Task, guarantees, methods

Fixed binary scores for K=3 systems and N=128 items. Certify the two signs
of comparisons from system 0 to 1 and 2, including exact ties. A cell is
purchased once, shared across comparisons, and counted once. The actual
conditional e-factors and Bonferroni threshold are identical to the audited
`peer_cell_scale` implementation. No predictive-model assumption is needed
for the fixed-matrix error bound alpha=.05. Wrong or unfinished output is
charged K*N, with actual paid cells reported separately.

For every available cell c predict p_c conditional on its known item stratum
and any already observed system scores in that item. For each unresolved
comparison e, define a_e,c = 1{c belongs to e}*p_c*(1-p_c). Choose lambda
on the unresolved comparison simplex to maximize

    G(lambda) = [sum_c sqrt(sum_e lambda_e*a_e,c)]².

There are at most two comparisons, so optimize this one-dimensional concave
dual over [0,1], checking endpoints. Let q*(c) be proportional to the
corresponding square root. Purchase from 20% uniform over eligible cells
plus 80% q*. Recompute every full null-calibrated e-factor with the **actual**
selection distribution before reading the score. Use separate RNG seeds for
targets, histories, strata, acquisition, particle control and item order.

Required controls on the identical matrices, history and item strata:

1. `row_peer`: existing peer predictor and calibrated inference, with its
   within-row acquisition uniformly distributed over unpurchased items.
2. `peer_cell`: earlier urgency times Bernoulli standard-deviation weights,
   exactly the same predictor and inference.
3. `ec2_weighted`: earlier 256-particle approximate edge-cut acquisition,
   exactly the same predictor and inference. This is not exact EC².
4. `paired_exact_closure`: existing shared-item retirement and ordering
   closure, given fitted global historical system marginals.
5. `stage22`: existing common-item certificate.

No parameter is tuned using the primary target scores. The new policy uses
the same 20% overlap floor as the peer-cell and EC² controls.

## Synthetic strata and independent cases

Known item stratum (one quarter high, three quarters low), drawn by a seeded
permutation. Targets in the high stratum use the existing 3-system one-hot
distribution (90% weighted one-hot 1:3:6 plus 10% uniform patterns).
Low-stratum target patterns are 95% all-zero plus 5% uniform patterns. The
2048-column historical bank has 512 high and 1536 low columns, generated
independently of the target. Every method knows each target item's stratum.

Primary: 60 aligned-history matrices, repetitions 1000..1059. Diagnostics:
20 homogeneous cases with every target and historical stratum drawn from
the high one-hot distribution, repetitions 1000..1019; and 20 reversed
cases where historical high and low generators are exchanged but targets
retain the primary design. All diagnostics are displayed even when adverse.

SHA256 seeds use literal prefix `20261026|dual_shared_acquisition|` plus
scenario, repeat and purpose. Development smoke cases have negative repeat
indices. No WMT or newly collected human labels enter this screen.

## Gate and audit

Use 20,000 paired case bootstraps. In the 60-case primary, report charged
cost ratios and Bonferroni-adjusted two-sided percentile intervals across
all five required controls; gate passes only if every lower saving bound is
strictly positive. Also publish actual costs, wrong declarations, and all
diagnostics. This is an empirical gate, not a proof of comparative expected
cost on each fixed matrix. Reconstruct every candidate query and every
true-null conditional factor, check unique cells and exact final decisions,
and rerun all controls. Run focused tests of factor validity and predictable
selection before generating primary targets.
