# Final research decision: NO-GO for this candidate

This decision applies to the frozen prototype, not to every possible joint finite-pool method. No WMT experiment was run. The branch is `research/stage24-joint-finite-pool`; method and protocol were committed at `048863f` before synthetic execution.

## Verified theoretical result

THEORY.md proves that positive known predictable inclusion probabilities produce a design-unbiased mean-vector innovation, even with correlated system scores and randomized system subsets. A predictable support-safe vector bet produces a nonnegative martingale; inversion at threshold 20 gives one 95% all-time vector coverage event. Every requested pair projection inherits the same familywise event. Optional stopping, auxiliary prediction errors and covariance-based bet selection do not invalidate that proof under its stated assumptions.

The implemented experiment is narrower: all-system row batches, binary scores, full integer-total-grid inversion, and conservative factor/capital arithmetic. The abstract partial-cell theorem has a one-step exact check but no end-to-end partial-cell acquisition experiment. Continuous MT score inversion, scalable computation, and an efficiency bound are not established.

## Results

60 fixed matrix/graph/history cells x 20 paths x 5 methods = 6,000 recorded rows. There are only eight independently generated outcome matrices (two shapes x four families); histories do not create new datasets. Uniform methods repeat the same 400 paths across histories; adaptive methods have 1,200 coupled paths. These are fixed-fixture development results.

| Method | Mean labels | Change vs Stage 22 |
|---|---:|---:|
| Stage 22 | 37.860 | reference |
| Per-system CS with pruning | 38.330 | +1.24% |
| Joint diagonal | 42.160 | +11.36% |
| Joint covariance | 42.182 | +11.42% |
| Joint covariance + adaptive acquisition | 42.447 | +12.11% |

The covariance arm costs 4.3225 more labels than Stage 22 (conditional paired Monte Carlo SE 0.0765) and 3.8525 more than per-system CS (SE 0.0864). These SEs average histories within each matrix/graph/repeat block before aggregating, avoiding false independence from repeated histories. They quantify sampling Monte Carlo noise conditional on the eight matrices, not new-benchmark uncertainty.

Neither joint covariance arm improves the mean in any of the 60 history-weighted cells versus either baseline: 15 tie and 45 worsen. On the 20 distinct uniform matrix/graph cells this is 5 ties and 15 losses. Compared with the diagonal joint ablation, covariance improves two distinct cells, ties sixteen, and worsens two. Aggregate covariance cost is slightly higher, not lower. This is evidence against this heuristic, not a theorem that correlation cannot help.

Failure persists on both shapes: mean Stage 22/joint-covariance costs are 29.746/31.167 for 4x8 and 50.031/58.706 for 3x24. Whole-row batches cannot exploit all pruning opportunities; sign-discretized bets and nuisance-vector projection may also lose efficiency. The study does not causally decompose those mechanisms. About 50.5% of joint covariance paths require the full population. No post-result parameter tuning was performed.

## Coverage and reproducibility

- Six new tests pass, including 7,020 exact rational one-step expectation probes across all {-1,0,1} directions on the recorded states.
- All 64 binary 2x3 populations, six possible adaptive row orders and two bet variants are checked: 768 complete branch executions with exact rational branch probabilities and a separate conditional-expectation proof. These tiny populations have limited power to stress a 0.05 crossing boundary; the proof is essential.
- Nine unchanged Stage 22 tests and eight Stage 23 tests pass. Stage 22 temporary-directory tests initially hit a sandbox permission issue and passed when rerun with the necessary execution permission.
- 60 representative joint traces were recomputed with identical hashes; all experiment source locks and previous-stage file hashes match.
- No wrong requested pair declaration was observed. Joint covariance had 2/400 distinct uniform paths exclude the true vector (99.5% observed anytime coverage); adaptive covariance had 3/1,200 (99.75%). The diagonal arm had 3/400 (99.25%). Pooled coverage is not a proof or a per-cell guarantee; the minimum observed 20-path cell coverage was 90% for diagonal and 95% for each covariance arm.
- `EXACT_FAILURE_AUDIT.json` independently checks the exact rational capital crossing on all eight distinct method/path exclusion events (18 history-weighted rows). These were genuine >=20 crossings, not a claim of perfect coverage or a numerical-exclusion artifact. A 95% guarantee permits occasional failures.

## Novelty decision

The source audit found directly relevant earlier results: vector gambling CSs and finite-population categorical inference (Ryu & Wornell, ICML 2024), adaptive importance-weighted finite-population betting (Shekhar et al., UAI 2023), and covariance-sensitive vector confidence spheres. Our proof combines known ingredients and adds no demonstrated regret, complexity, or unique-label efficiency theorem. The requested broad novelty claim is not established. A faithful Ryu/Wornell universal-portfolio implementation was not benchmarked; no superiority to that stronger joint baseline is claimed.

The predeclared gate fails on both novelty and materiality. Neither tested covariance arm saves 5% over the two required baselines, and there is no matrix family with a cell-average advantage over Stage 22. The current evidence does not support an ICML submission or a larger WMT run for this construction.

## Most promising next question

Seek an instance-dependent unique-label efficiency theorem for joint partial-cell acquisition under exact finite-pool coverage, together with a scalable continuous-score solver. Compare the prospective theorem with existing vector gambling and adaptive financial-auditing results before implementation. A concrete separation from strong coordinate/pair methods or a meaningful computation theorem is required; merely removing a union-bound factor or changing acquisition order is insufficient. This remains an unresolved research proposal, not an established contribution.
