# Stage 24 feasibility result

**NO-GO for the tested construction as a novel ICML contribution.** This is not a proof that all joint finite-pool methods fail.

| Method | Mean unique labels | Change vs Stage 22 |
|---|---:|---:|
| stage22 | 37.860 | +0.00% |
| per_system | 38.330 | +1.24% |
| joint_diagonal | 42.160 | +11.36% |
| joint_covariance | 42.182 | +11.42% |
| joint_adaptive | 42.447 | +12.11% |

Lower is better. These averages equally weight the 60 fixed cells and their 20 paths; uniform-method results repeat across histories and are not extra independent data. See per-shape and per-cell results rather than interpreting the pooled average as population performance.

- joint_covariance vs stage22: 0 cells improve, 15 tie, 45 worsen (history-duplicated cells included).
- joint_covariance vs per_system: 0 cells improve, 15 tie, 45 worsen (history-duplicated cells included).
- joint_covariance vs joint_diagonal: 6 cells improve, 48 tie, 6 worsen (history-duplicated cells included).
- joint_adaptive vs stage22: 0 cells improve, 15 tie, 45 worsen (history-duplicated cells included).
- joint_adaptive vs per_system: 0 cells improve, 15 tie, 45 worsen (history-duplicated cells included).
- joint_adaptive vs joint_diagonal: 7 cells improve, 38 tie, 15 worsen (history-duplicated cells included).

Observed wrong declarations: 0; joint anytime-coverage failures: 18. Small synthetic observations do not prove the 95% guarantee. The explicit conditional-expectation proof and exact arithmetic checks are the justification.

## Proven versus empirical versus open

- Proven in THEORY.md: design-unbiased vector correction, valid nonnegative joint wealth, simultaneous all-time pairwise projections at 95%, under positive known predictable inclusion probabilities. The prototype uses conservative arithmetic on the full binary-total grid.
- Empirical: results above apply to two small binary shapes, four fixed matrix families and the frozen path seeds. They do not establish continuous-score WMT performance or an optimal joint method. The inverse-covariance sign heuristic has no efficiency guarantee.
- Novelty: the ingredients are direct combinations of existing adaptive finite-pool inverse-probability betting and vector CS inversion. No new theorem/complexity advantage survived this audit. AnyRank is related but targets different i.i.d. outcomes; no surrogate AnyRank benchmark was used.
- Open: a scalable continuous-score joint method using partially observed cached cells with a provable unique-label efficiency advantage. General partial-cell unbiasedness is proved and tested one step, but only whole-row acquisition is evaluated end-to-end.

## Recommendation

Do not run WMT or prepare an ICML claim from this candidate. The most promising next theoretical question is an instance-dependent efficiency bound for joint adaptive partial-cell inference, compared with existing joint gambling constructions and strong coordinate/pair procedures. Require a concrete separation or useful computational theorem before another benchmark. Avoid further tuning this pilot against the same synthetic fixtures.
