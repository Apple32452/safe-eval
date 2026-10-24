# Fixed-pool cell permutation diagnostic (development)

Date: 2026-10-24. This is a prospective synthetic screen, **not** an ICML
novelty claim. WMT24 is untouched and WMT25 is not used in this screen.

## Question

For a reference star on five systems and 128 fixed binary-score items, does
buying one system--item judgment at a time with a globally precommitted random
cell permutation and a direct finite-pool e-process use fewer unique judgments
to resolve *every* comparison than the matched Stage 22 pair-prefix rule?
Previously tested single-cell importance weighting was inefficient. Here each
pair's 256 signed score cells form a uniform without-replacement permutation;
the process bets on the remaining finite-pool mean instead of a one-draw
inverse-probability estimate. The change in evidence, not scheduling alone,
is the object of the screen.

## Frozen design

- Five systems, 128 items, four requested reference edges, `alpha=0.05`.
- The four scenarios use Bernoulli rates: independent easy
  `[.9,.1,.2,.4,.6]`, independent weak `[.6,.5,.48,.45,.42]`, shared-uniform
  correlated easy with the easy rates, and independent close
  `[.50,.52,.48,.53,.47]`.
- Fifty independently generated fixed matrices per scenario. Derive seeds from
  master `20261024` and the scenario and repeat identifiers; for each matrix
  randomize a common item order for Stage 22 and a uniform global permutation
  of all system--item cells for the candidate. Pair outcomes are identical
  across methods; acquisition streams differ.
- Stage 22 uses its original six-stake directional finite-pool e-process and
  active-vertex pruning; candidate uses the same six stakes and threshold
  `2*|E|/alpha=160`. Both have exact, zero-error deterministic remaining-range
  certification and reveal the full matrix if needed. A cell is charged once.
- Evaluate **complete** correct reference-star conclusions, not early
  budget-only partial successes. Save every method/matrix cost and final
  decisions. Audit nonanticipation, unique charges, exact final signs, and
  small-pool conditional e-factor inequalities.
- Internal screen passes only if candidate mean cost is at least 10% lower
  than Stage 22 in at least three of four scenarios, without a lower
  completion rate or an incorrect final direction. Both methods must have
  their stated worst-case family error argument. A pass would motivate a
  stronger published-baseline and external confirmation study, not itself
  establish novelty. A failure closes this particular method.

## Candidate validity argument to verify in code

For edge `(a,b)`, restrict the outcome-independent uniform global cell order
to its `2N` endpoint cells, assigning signed values `z(a,i)=y[a,i]` and
`z(b,i)=-y[b,i]` in `[-1,1]`. Before its next draw, let `S` be their observed
sum and `R` their remaining count. Under `T_ab <= 0`, the conditional mean
of the next signed value is at most `c=-S/R`. For each fixed `rho` in
`(.02,.05,.1,.2,.4,.8)` and `c>-1`, the factor
`1+rho*(z-c)/(1+c)` is nonnegative and has conditional mean at most one.
Mixtures of the six products and the same construction for `-z` give both
directions. At any complete pair prefix, the deterministic interval
`[S-R,S+R]` contains the target. A decision on an adaptively selected prefix
is a subset of the complete random pair path's anytime crossing event; the
union bound over eight directional paths gives `alpha` family risk for every
fixed matrix. This is a direct application of established finite-pool betting
and is **not claimed as a new theorem**.

No additional score of an endpoint may be exposed ahead of the pair's current
global cell prefix while the edge is active. The implementation must assert
this path property. Results cannot be used to tune the frozen rates or gate.
