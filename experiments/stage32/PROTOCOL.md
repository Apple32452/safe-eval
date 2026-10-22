# Stage 32: companion-panel context stress test (frozen before simulation)

## Question and estimand

Can selecting which three translations accompany systems A and B change the
interpretation of an apparently confident A-versus-B conclusion? The estimand
is the expected signed preference for A over B under a **predeclared target
distribution of five-way panels**, not under the panels an adaptive policy
chooses to show. This simulation is a diagnostic; it is not evidence that
human judges exhibit the specified context effect.

There are two complete five-way panels: `G=(A,B,C,D,E)` and
`B=(A,B,F,G,H)`. Each fresh, independent simulated judge produces a complete
strict ranking, with A/B in the top two positions and companion systems in
their listed order underneath. In panel G, A beats B with probability 0.9;
in panel B, A beats B with probability 0.1. A single latent uniform random
number determines their order. The other three placements are deliberately
uninteresting; we only analyze the A/B sign `Y in {-1,+1}`.

The target panel distribution is `pi(G)=0.25`, `pi(B)=0.75`, so the target
mean is `Delta=0.25*(2*0.9-1)+0.75*(2*0.1-1)=-0.4`: **B is preferred**.

## Matched methods and fixed parameters

* `target_random`: draw panel G with probability 0.25 independently per
  round; use the unweighted observed sign.
* `adaptive_naive`: before each judgment, choose G with probability 0.9 if
  the preceding observed sign was +1, and 0.8 otherwise (initial preceding
  sign is +1); use the unweighted observed sign. This estimates a different,
  policy-dependent quantity, so treating its result as Delta is invalid.
* `adaptive_ipw`: replay exactly the `adaptive_naive` choices and judgments,
  but update with `X=pi(panel)*Y/q_t(panel)`, where `q_t` is the logged
  probability of that choice. The choice is made before the fresh judgment.

For each repeat, the three methods share independent uniform random-number
streams for panel choice and judge response at every round. Seeds are
`20261022 + repeat`. This couples methods for a comparison; it does not make
the outcomes independent across methods. There are 500 repeats, a maximum of
2,000 panel tasks per method, and no reuse of a judge within a trajectory.

Use the same four stakes `rho=(0.10,0.25,0.50,0.80)` as Stage 31. For each
direction and stake, accumulate a wealth factor `1 +/- rho*Z_t/M_t`, with
`Z_t=Y_t, M_t=1` for the target-random and naive methods, or `Z_t=X_t` and
`M_t=max_s pi(s)/q_t(s)` for IPW. Both choices keep factors positive. Average
the four wealths for each direction. Certify A or B on the first mixture
crossing of `2/0.05=40`; otherwise abstain at the cap. This is a two-null,
one-pair familywise threshold, intentionally distinct from Stage 31's 105
pair threshold. The costs are five-way tasks, including all abstentions.

Conditional on the past under the stipulated stable response probabilities,
`E[X_t|past]=sum_s pi(s) E[Y_t|s,past]=Delta`, because every panel with
positive pi has positive logged selection probability. Therefore the IPW
factors are nonnegative supermartingale factors under the respective
directional nulls. The same holds for unweighted Y under target randomization.
The naive method lacks that guarantee for Delta. The fixed bounds above
also imply `|X_t|<=M_t`. Dependence of multiple pair outcomes within a
five-way panel is irrelevant here because only A/B is used.

Report each method's numbers declaring A (wrong), declaring B (correct), and
abstaining, plus mean capped panel tasks and mean panels among correct
declarations. Do not compare the mean cost of a method with many abstentions
to a complete method as though it were an efficiency gain. Count any wrong
target-direction declaration, and do not present an empirical zero as a
proof of calibration.

## Boundaries of this experiment

The context effect is built into the synthetic model. Its magnitude, sign,
and real-world prevalence are unknown. A genuine human study must randomize
companions and display order on the same input and A/B outputs, recruit
independent raters, and record cost. The current simulation neither measures
human context effects nor establishes a new sequential-inference theorem.
