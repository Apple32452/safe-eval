# Guarantee for the reserved-raw fallback

This is an application of standard e-process mixtures and confidence-set
inclusion. It is not a claim of a new statistical principle.

## Setting and component validity

There are N fixed binary target outcomes. We query uniformly without replacement.
The parameter is Q=K/N, where K is the unknown total number of successes. Historical
data and past queried outcomes can determine the next predictor and stakes;
unqueried target outcomes cannot. Candidate counts are 0,...,N.

Let R_t(K) be the binary prior-posterior-ratio (PPR) process with a uniform
working prior on K. At the true K it is a nonnegative supermartingale starting
at one, including degenerate boundary states. The construction is the binary
CS in [Waudby-Smith & Ramdas, Theorem 2.1](https://arxiv.org/html/2006.04347v4).

The prediction component uses the unchanged Stage 2 corrected draw Z_t. Its
conditional expectation is Q even with a misspecified predictable predictor.
Each directional factor has conditional expectation one at Q and remains
positive. Let K_t^+(Q) and K_t^-(Q) be their capital processes. The process

P_t(Q) = (K_t^+(Q) + K_t^-(Q))/2

is also a nonnegative martingale starting at one. Use the integer count grid
because these target outcomes are binary. Intersect all confidence sets with
the success counts compatible with the already observed outcomes.

## Fixed mixture and reserve

For a predetermined weight 0<w<1, define

M_t(K) = w R_t(K) + (1-w) P_t(K/N).

The mixture is a nonnegative supermartingale at the true K, with initial value
one. Ville's inequality gives a nominal 1-delta anytime confidence set by
retaining candidates for which M_s(K)<1/delta at every s<=t.

For every candidate and path, M_t(K)>=w R_t(K). Thus the mixture's running
accepted set C_M(t) is contained in C_R^w(t), the raw PPR accepted set with
error level delta*w. Taking interval hulls preserves this inclusion. The
implementation also intersects the mixture mask with the reserved-raw mask,
a redundant constraint in exact arithmetic that stabilizes numerical inclusion.

## Empty-set repair and all-path stopping bound

Return the hull of C_M(t) when it is nonempty. Otherwise return the hull of
C_R^w(t). This output always contains C_M(t), including when C_M(t) is empty.
Therefore a simultaneous coverage failure of the output can occur only on a
mixture failure path, whose probability is at most delta. The repair uses no
true-mean information. It can widen an interval; coverage does not require
intervals to be nested.

The output remains a subset of the reserved-raw interval and is nonempty
whenever that raw interval is nonempty. Hence, for the first nonempty interval
of width <=2*epsilon,

tau_output(w) <= tau_PPR(delta*w)

on **every realized query path**, including mixture-failure paths. At N queries
the exact observed mean is available and every method returns it, while earlier
coverage failures remain counted in diagnostics.

## What the bound does and does not give

For the primary w=0.75 and delta=0.05, the reserved raw control has error level
0.0375, i.e. nominal confidence at least 96.25%. Its extra evidence threshold
relative to 95% PPR is log(1/w)=0.287682 log-capital units.

This is **not** a noninferiority guarantee against raw PPR at 95%, and not a
fixed additive bound on extra queries. Translating a log-threshold change into
query counts requires further assumptions about evidence growth. We compare
actual query costs to the equally nominal 95% raw control empirically, and
report the stricter control separately to verify the guarantee.

The construction here requires binary outcomes and uniform WoR sampling for
the PPR component. It cannot be transferred unchanged to adaptive nonuniform
acquisition, fractional rater averages, continuous MQM scores, or population
means on future sentences. Such extensions need new component-validity work.

Prediction-powered optional-stopping validity and predictable mixtures already
exist; see [Prediction-Powered E-Values](https://arxiv.org/html/2502.04294v2)
and [betting confidence sequences](https://arxiv.org/html/2010.09686v7).
Any ICML novelty claim remains a separate unresolved research task.
