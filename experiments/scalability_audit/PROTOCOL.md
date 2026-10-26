# Pairwise scalability audit

Base 5d991e7. Synthetic inputs only; no previous sources changed, no optimization.
Stage17 continuous finite-pool six-component pair betting is the scalable existing
kernel; Stage22 is its requested-graph acquisition replay. Exact DP/grid solvers
are not silently generalized beyond their supported system counts.

Systems 32,100,200,400; items 64,256,1024; star/ring/complete graph as enumerated
by audit.py. Complete 400x1024 is excluded by a preflight allocation estimate
of 48 bytes per pair-item exceeding 1.5 GiB. Exclusions are not measurements.
Fixed seed 731, bounded continuous separated scores or exact ties. All pairs
share a full outcome-independent uniform permutation; alpha=.05 per graph.
Three fresh processes per case, single-thread BLAS. Every process measures
original make_paths wall/CPU and OS peak working set. A second pass uses AST
timers around original update and threshold/deterministic stopping blocks,
requiring exact array equality. This is attribution, not a new implementation.
Phase quantiles concern pair batches per common item, not one queried cell.

Repetition zero additionally times Stage22 star_pruned replay with original
snapshots and stopping rules. Instrument only its global unresolved checks and
close_free. Full replay is allowed 45 seconds after evidence profiling completes;
parent timeout checkpoints retain all completed phases. Instrumented replay is
reported as such, not an uninstrumented production latency. Other repetitions
measure evidence only. A 180-second deadline covers each precomputation worker.
No result is dropped because it is slow. Peak memory includes imports, fixtures,
temporary arrays, full traces and retained plain/instrumented outputs.

The original engine stores complete future-score paths for OFFLINE simulation.
Neither future-label access nor replay's evidence lookup is an online deployment
procedure. No confidence-interval inversion or full rank-closure timing is inferred
from these sign-test kernels. Original statistical factors and decisions unchanged.
No new coverage claim follows from parity; preserve nominal anytime FWER under
the original common-prefix sampling and support assumptions.
