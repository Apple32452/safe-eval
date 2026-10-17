# Scope and justification of the Stage 9 safeguard

## Exact raw risk certificate

Let L(t,s),U(t,s) be the raw implementation's pointwise accepted integer-count
interval after t labels and s successes. Its full acceptance mask is checked
to equal this interval at every state. Running interval intersection and
running candidate-mask intersection consequently agree.

For a fixed total K, define A(t,s) as the number of binary prefixes which have
stayed accepted. Initialize A(0,0)=1. At feasible states s<=K and t-s<=N-K,

    A(t,s) = 1{L(t,s)<=K<=U(t,s)} * (A(t-1,s)+A(t-1,s-1)).

Then [comb(N,K)-A(N,K)]/comb(N,K) is the exact probability of ever rejecting the
true count. Counting candidate rejection is sufficient for interval failure;
contiguity supplies equality for these raw intervals. Final exact-mean
recovery does not erase an earlier failure.

An independent backward recurrence counts rejected completions: at an
already-rejected state return comb(N-t,K-s), otherwise add the success and
failure successors. It must match every saved forward count, including any
checked symmetric counterparts. The certificate refers to the actual finite
floating gate table on the runtime. Another runtime must reproduce this table
or regenerate and audit its own certificates before using the error budget.

## Prediction correction and conservative arithmetic

For predictable m_ti and uniform I_t on the remaining r_t items,

    Z_t = [S_(t-1)+sum_remaining m_ti]/N
          + (r_t/N)*(Y_(I_t)-m_t,I_t)

has exact conditional mean K/N. Predictions, stakes and supports may depend
on history and previously queried labels, never the current or future labels.
The exact positive factors 1+lambda_plus*(Z-q) and
1-lambda_minus*(Z-q), evaluated at the true q=K/N, have conditional mean one.

Predictable binary64 predictions and stakes are interpreted as exact dyadic
values. The true count fraction q and corrected draw are enclosed outward.
Each stored factor is a lower bound on its corresponding exact factor.
Each stored scaled product is a lower bound on the exact capital product.
Rejecting only when the lower average capital exceeds an upward-rounded
1/alpha is therefore conservative for the valid exact process.

The nonnegative prediction sum uses the standard gamma_(N-1) rounding bound
under at most N-1 round-to-nearest additions. Outward elementary operations
use nextafter; positive products are scaled by exact powers of two via
frexp/ldexp. Underflowed aligned capital is rounded down to zero. Capital
logarithms and assumptions about libm logarithm rounding are avoided.
This argument assumes conforming IEEE-754 binary64 elementary operations
without unsafe fast-math reassociation or flush-to-zero. It is a justified
arithmetic model and tested implementation, not a proof of every hardware or
NumPy installation. Full formal verification is outside this prototype.

## Coverage and ordinary raw95 stopping cost

Let C_R be unchanged raw95, with certified error u(N), and C_P have error alpha
<= .05-u(N). If their intersection is nonempty, return its count hull.
Otherwise return C_R. On the event that both cover at every time, the
intersection contains the truth and cannot be empty. A union bound therefore
gives simultaneous coverage at least .95. This is an application of standard
error allocation; neither the union bound nor the intersection is new.

The returned interval is always a subset of C_R, including fallback equality.
Whenever C_R reaches a nonempty precision interval, the returned interval is
nonempty and no wider (or falls back to C_R). The first precision stop is
therefore no later than ordinary raw95 on EVERY shared query path. The same
argument holds for calibrated_raw95, whose own full-path error is certified.

This does not guarantee savings, does not bound prediction cost against the
calibrated raw control, and does not apply unchanged to nonuniform acquisition,
continuous outcomes, annotation uncertainty or future populations.

## Prior work

- Waudby-Smith and Ramdas, finite-population PPR confidence sequences:
  https://arxiv.org/abs/2006.04347
- Waudby-Smith and Ramdas, betting confidence sequences:
  https://arxiv.org/abs/2010.09686
- Csillag et al., Prediction-Powered E-Values, ICML 2025:
  https://proceedings.mlr.press/v267/csillag25a.html
- Li et al., Robust Sampling for Active Statistical Inference:
  https://arxiv.org/abs/2511.08991
- Ashouritaklimi et al., Prediction-Powered Active Testing:
  https://arxiv.org/abs/2607.08347

Any novelty assessment must compare the exact guarantee and calibration with
these and other sequential calibration/forecast-assisted procedures. The
current construction is not claimed as a new ICML method.
