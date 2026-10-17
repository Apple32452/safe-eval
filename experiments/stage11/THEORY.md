# Exact integer implementation of a known boosting algorithm

Reference: Lasse Fischer and Aaditya Ramdas, *Improving Wald's (approximate)
sequential probability ratio test by avoiding overshoot*,
https://arxiv.org/html/2410.16076v4, Algorithm 1, Theorem 1, Sections 4.1–4.2.
Sequential boosting and inversion into confidence sets are established prior
work. The derivation below specializes that algorithm and accounts for our
conservative finite-precision implementation; it is not a novelty claim.

Before draw t let r=N-t+1, a=K-s, d=t+1 and u=s+1. Under candidate K,
P(Y=1|past)=a/r. The existing PPR process has possible factors
L1=u*r/(d*a) and L0=(d-u)*r/(d*(r-a)) when 0<a<r. Their conditional mean is
one. At a=0 or a=r the possible factor is a prior predictive probability,
at most one, so the PPR is a supermartingale on those null boundaries.

Represent wealth by nonnegative integer w divided by Q=2^39; rejection is
w=B=20Q. For interior nulls let h be the outcome with larger L and let c be
its null numerator (a if h=1, r-a otherwise). If w*Lh<B, no truncation is
needed: the unrounded update is w*Ly. Otherwise the boosted possible wealths
are B on h and (r*w-c*B)/(r-c) on the other outcome. The latter is nonnegative:
crossing implies w>=B*c/qh/r>=B*c/r because the predictive probability is at
most one. Their null weighted average equals w. Round each possible wealth
down to an integer. The conditional average can only decrease. The unboosted
control uses floor(min(B,w*Ly)). At deterministic nulls the boosted wealth
stays w on the possible outcome; the unboosted wealth is floor(w*qy). The
impossible outcome is rejected and has conditional probability zero.

Thus the stored process, divided by Q, is a nonnegative test supermartingale
starting at one. Rejection wealth 20 and Ville's inequality give full-path
error at most .05 for the true K. Impossible-candidate rejection is null-zero.
This concerns each fixed recorded binary pool over uniform queries without
replacement, not familywise validity across all targets or latent quality.

For either outcome, the unrounded boosted wealth is continuous and
nondecreasing in w: its pieces are w*Ly, B, and (r*w-c*B)/(r-c).
It is at least min(B,w*Ly). Flooring preserves both properties on the integer
grid. Induction therefore shows that the boosted first rejection of each K
is no later than the matched grid first rejection. Hulls preserve containment.
Once the boosted set is empty, replacing it by the grid output preserves
containment; if both are empty both return raw95. At full N both return K/N.
Consequently the returned boosted interval is contained in the grid output
on every path, so its first nonempty width-.1 stop is never later. A final
singleton does not erase earlier exclusions when reporting simultaneous coverage.

Every empty-set replacement contains the underlying empty confidence set, so
it cannot create an exclusion of the true K on a path that the unmodified
set covered. No union-error allocation is needed for this expansion.

For N<=820, all nonnegative product intermediates are bounded by
20*2^39*(821)^2 < 2^63-1. Differences used in the capped low branch have
magnitude at most 20*2^39*820; denominators are positive on their relevant
branches. Enforce this bound and binary input validation before using int64.
The auditor uses an independently arranged observed-branch calculation; small
synthetic tests additionally compare arbitrary-precision rational arithmetic.
Floating division is used only for reporting endpoints and percentages.

The grid baseline can retain candidates the ideal PPR rejects because it
rounds downward. We measure differences from the frozen floating PPR rather
than silently equating these processes. The ideal published theorem alone
does not certify their bitwise equivalence. Returning a hull may lose power
if accepted candidates have holes; all first rejection times and hole counts
are retained for audit. No claim of optimal inference or a new confidence
sequence is made.
