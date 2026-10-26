# Peer-informed individual-cell acquisition: frozen scalability screen

Date: 26 October 2026. Freeze this protocol before generating the main target
matrices or computing the main comparison. This follows the six-cell exact
separation in `acquisition_separation`. The question is whether a tractable
policy retains an efficiency gain. This is development research, not an ICML
novelty claim or an independent real-data confirmation.

## Fixed target and validity

Scores form a fixed K-by-N binary matrix. Return all requested signs of
full-row-total differences, including exact ties. A cell is paid for once;
its observation enters the full history and can inform other comparisons.
All methods use taskwise error bound alpha=0.05. Wrong or incomplete output
is charged K*N in the primary cost measure; also report actual paid cost,
wrong decisions, and completion. Ties cannot be silently excluded.

The candidate constructs directional e-factors against each null T_a<=T_b
using the actual predictable probability of selecting each unseen cell.
Calibration maximizes the factor's expectation over every binary completion
consistent with the observed scores and that null. Sorting cell increments
reduces this maximization to prefix sums. Products plus a 2*|edges|/alpha
threshold give familywise validity under arbitrary fixed matrices, even if
historical predictions are wrong. This is an application of established
e-process and reverse-information-projection ideas, not a claimed new theorem.

## Predictor and cell proposals

Generate 2,048 separate historical columns for each case. Fit a categorical
column distribution with Jeffreys 1/2 pseudocount per binary pattern. For
the tested K=3 or 5, condition this distribution on already purchased scores
in the same item. Clip predicted Bernoulli probabilities to [.02,.98].
The target's unpurchased values are never supplied to fitting or selection.
This small categorical predictor is exponential in K; the calibration and
acquisition code accept arbitrary predictable probabilities and do not
enumerate full target matrices. No claim of unrestricted predictor scalability.

For each unresolved edge, calculate its predicted total gap divided by N.
The urgency of an endpoint is the sum over its unresolved edges of
1/max(abs(gap),.1). Give each active unseen cell weight
urgency * sqrt(prediction*(1-prediction)). The proposal is 20% uniform over
active unseen cells plus 80% proportional to those weights. These constants
are fixed. Predictions use the historical distribution and observed peer
scores, without refitting on the target.

## Required controls

1. `peer_cell`: the proposed cell weights and conditional peer predictions.
2. `row_peer`: exactly the same predictor, row masses, and calibrated factors;
   distribute each row's selection mass uniformly over its unseen items.
3. `no_peer`: use historical marginal probabilities in the same proposal and
   inference. This isolates peer information, not just cell selection.
4. `ec2_weighted`: draw 256 complete matrices from the historical model
   conditional on observed cells. Group them by unresolved comparison signs,
   compute empirical EC2 expected edge-cut gains for each eligible cell,
   and use 20% uniform plus 80% proportional to these gains. Use the same
   calibrated factors as the candidate. This is an explicitly approximate,
   randomized EC2-based acquisition control, not published exact EC2 or its
   original stopping rule. Stop decisions never rely on sampled hypotheses.
5. `paired_exact`: common uniform item order, active-system retirement,
   exact one-step null constraints on the remaining {-1,0,1} differences,
   historical joint pair probabilities plus four-pseudocount online updating,
   and the same directional familywise threshold.
6. `stage22`: the preserved Stage 22 common-prefix/pruning certificate.
7. For K=3 also run the previous `paired_exact_closure` and
   `rebalanced_pair_order` controls from `joint_order_controls`, using the
   fitted historical marginals. Preserve their stronger ordering closure.

All controls see the same target matrix and historical data. They get a
shared case-level acquisition seed; the EC2 particle RNG is separate.
Common-item controls share one precommitted random item permutation.

## Synthetic designs and locked sample sizes

The four aligned column distributions extend the exact study:

- Independent: product Bernoulli probabilities evenly spaced from .2 to .8.
- Monotone: 90% common-uniform threshold columns at those probabilities,
  plus 10% uniform binary columns.
- Opposed: 90% mixture of 100...0 with probability .2 and 011...1 with
  probability .8, plus 10% uniform binary columns.
- One-hot: 90% one-hot columns, weights (1,3,6) for K=3 or (1,2,3,4,5)
  for K=5, normalized; plus 10% uniform binary columns.
- Reversed history: one-hot target; bit-complement every historical column.
- Near/exact ties: independent fair-bit history and target; on even repeat
  indices replace target row 1 by row 0 to create an exact requested tie.

Primary: K=3, N=64, reference star, one-hot, 50 independent matrix/order
cases. Diagnostics: the other five distributions at this size, 10 cases
each; all six distributions with K=3,N=64,all pairs,10 cases each; and all
six with K=5,N=128,reference star,5 cases each. Total 190 matrices and 1,460
method trajectories. No WMT or prospective human data are used.

Seeds are SHA256-derived from the literal
`20261026|peer_cell_scale|scenario|K|N|graph|repeat|purpose`, taking the first
eight bytes as an unsigned little-endian integer. Primary and diagnostic
cases are distinct, including across graphs. Smoke tests use purpose `smoke`.

## Analysis and decision

Publish all case-level costs, prediction inputs, query ledgers, and summaries.
The primary comparison is the ratio of mean penalized costs in the one-hot
star case against every required control. Also report paired cost differences.
Use 20,000 paired bootstrap resamples and Bonferroni-adjusted percentile
intervals across the seven primary controls. These are approximate sampling
intervals, not the source of the mathematical validity guarantee.

Continue this particular policy to an external-data efficiency study only
if audits pass and every primary adjusted interval for savings is strictly
positive. All diagnostic outcomes remain visible; a positive primary alone
does not establish generality. No particular percentage constitutes novelty.
If the gate fails, preserve the result and do not tune on these outcomes.

Before the main run, verify support maximization against exhaustive small
completions, selected-cell predictability, row-uniform proposal identities,
the ternary paired constraints, no repeated purchases, and full-pool/tie
completion. Independently replay saved results and calibration bounds.
