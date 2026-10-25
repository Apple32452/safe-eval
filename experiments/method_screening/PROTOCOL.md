# Evaluation method screening before acceleration

Base a9c2f50, branch research/method-screening-before-acceleration. Reuse archived
results; no WMT data, new optimizer, statistical method or parameter tuning.

Keep distinct tasks separate: (A) fixed binary finite-pool requested signs,
three systems/N=16, star and triangle, 95% taskwise anytime familywise error;
(B) two-system/N=32 fixed-pool signs under the same nominal guarantee;
(C) fresh-input five-way panel preferences, 70% pair certification;
(D) individual system mean precision. No pooled leaderboard across these tasks.

Primary strong controls for A: pair-factor rebalancing on the candidate's same
cell path; prediction-aware exact paired-difference closure and Bonferroni on
the archived common-item order; Stage 22 pruning. Use all 100 archived matrices,
including correlated, reversed-history and near-tie scenarios. Recover actual
paid cost, error-penalized charged cost and taskwise decisions, not just narrative
claims. Reproduce archive summary calculations. No new efficacy gate is invented.

Only surviving alternative needing additional computation evidence: existing
paired_exact_closure. Time it against Stage 22 on each scenario's first archived
matrix (repeat=0, fixed without inspecting costs), both graphs; supplement only
the strong scenario at N=64/128, seed 731+N. Three cold-cache, fresh-process
repetitions each. Identical scores, priors, item order, requested signs, alpha=.05
and cost unit within each comparison. Acquisition may differ only through each
existing method's justified retirement/stopping rule. Larger fixtures are scale
probes, not new efficacy validation. No additional matrices after outcomes.

Measure wall, CPU, OS process peak working set and paired_update inference time;
clear existing caches before each timing. Original implementations unchanged.
Trace storage is disabled using the existing keep_trace=False option for paired
controls; paid cost/decisions must still match archives. Stage 22 times full-path
offline evidence plus analytic footprint pricing: not live online inference.
Timeout 90 seconds/child; retain timeouts. No optimization and no large WMT study.

Reuse earlier computational_profile only within its stated workload scope.
Do not transfer timing for the two-system cutting-plane DP to the different
three-system histogram solver. A slow rejected method is not an acceleration
target merely because it is slow. A competitive method needs both a meaningful
computational limiting regime and a distinct theoretical contribution before GO.

Reassess end-to-end value using 10/30/60 seconds per cell, serial and ideal
aggregate parallelism. These are scenarios, not measured human latency or a
valid parallel adaptive schedule. No claim of novelty from implementing faster
SLSQP, caching, or applying existing e-process constructions.
