# Stage 13 calculations and limits

## Categorical paired evidence

Fix a population of N paired outcomes D in {-1,0,1}. Write (a,b,c) for observed
counts of +1,-1,0 after t draws and (A,B,C) for population counts. The null for
claiming A-system superiority is A <= B. For each fixed population count vector,
the PPR likelihood ratio from a Dirichlet(1,1,1) mixture has exact value

    E_t(A,B,C) = 2 choose(N,t) /
                ((t+1)(t+2) choose(A,a) choose(B,b) choose(C,c)).

At the true count vector this is a nonnegative (super)martingale under uniform
sampling without replacement. Zero-probability histories may have infinite
evidence. Thus infimum over the composite null is dominated by the evidence at
the true null vector. Ville's inequality controls an arbitrary-time crossing.
Use the analogous null with signs exchanged to claim B-system superiority.

If a > b and B >= A+2, replacing (A,B) by (A+1,B-1) increases the likelihood:
the ratio exceeds one precisely when B*a > (A+1)*b. A maximizer under A <= B
therefore has B-A in {0,1}. For each d in {0,1}, maximize

    F_d(k) = choose(k,a) choose(k+d,b) choose(N-2k-d,c)

over feasible integer k. Its adjacent ratio is nonincreasing and is compared
using exact integer products:

    F_d(k+1)/F_d(k) =
      (k+1)(k+d+1)(z-c)(z-c-1) /
      ((k+1-a)(k+d+1-b)z(z-1)),  z=N-2k-d.

Binary search gives an integer maximizer; exact binomial products choose between
the two parities. No floating likelihood comparison controls rejection. If a<=b,
the implementation uses zero raw evidence for this direction. The unrestricted
likelihood maximum can be attained in the null in this case, so standalone raw
evidence could not reach a threshold greater than one; zero is conservative for
the reserve mixtures as well. Empty null support also has a deterministic sign
certificate, treated separately.

## Historical corrected draw

Before the next uniform draw, let r items remain, S be the observed sum of D,
and m_i be any predictions fixed from history and strictly earlier target labels.

    Z = (S + sum_remaining m_i)/N + (r/N)(D_I - m_I).

Its conditional expectation is the complete fixed-benchmark mean Delta. This
holds for arbitrarily poor predictions, including the two stress banks.
Predictable bounds are obtained with D_I in [-1,1] and the largest/smallest
remaining prediction. For the null Delta<=0, a nonnegative predictable lambda
gives conditional expected factor E[1+lambda Z | past] <=1. Cap lambda to keep
every possible factor at least 1/2. Use 1-lambda Z for the opposite null.

Predictions are integers q_i/1024. If C=1024*S+sum q_i, then Z has integer
numerator C+r*(1024*D_I-q_I), denominator 1024*N. Base stakes are integer
multiples of 1/8; either retain that rational stake or use its exact rational cap.
Round next capital downward, cap and absorb at threshold 9480, and average the
eight expert capitals downward. Each operation preserves domination by a valid
nonnegative test process. The rounding guarantee concerns fixed chosen
predictions; ridge/SVD floating variation can change efficiency across machines
without changing the conditional budget.

## Reserve mixture and two error settings

For either null and its true fixed count vector, the 75/25 mixture of that
vector's PPR process and the corrected-draw process is valid. Our computed
mixture (using the infimum raw evidence and downward rounding) is no larger.
An early sole directional crossing at 40 therefore has wrong-direction
probability at most 1/40 for each direction. A union bound gives at most .05
for a pair. The threshold 9480=40*237 gives at most .05 for any wrong directional
claim among the 237 predeclared pairs, separately for a chosen method. Dependence
between pairs does not invalidate the union bound. Results of multiple methods
are not licensed for unadjusted post-hoc selection.

Independent deterministic certificates, |S| > N-t, cannot be wrong. At full
evaluation the sign is exact. This does not erase any earlier wrong decision.
Finite-population claims concern these fixed recorded labels only: document
dependence does not change design validity for this estimand, but uncertainty
over new documents and human raters is absent.

The exact-arithmetic optimization and reserve implementation are a specialization
of existing inference principles. No new theorem of minimal label cost or
universal ranking preservation is claimed.
