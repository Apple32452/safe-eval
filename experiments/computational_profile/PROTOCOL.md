# Frozen computational profiling protocol

Base: ecdd7e6 (remote main, 2026-10-25). No optimization or statistical changes.
Only synthetic inputs; no WMT data accessed. Existing implementations are imported
unaltered. Stage 31 system-count globals are rebuilt using their original formulas.

Three fresh subprocess repetitions per workload, one BLAS thread, fixed input and
sampling seed 731. Repetitions measure timing noise, not statistical uncertainty.
Plain runs supply authoritative wall time, process CPU time and OS peak working set.
Separate instrumented runs wrap original statement blocks in timers, preserving
outputs (JSON digest equality required). Their fractions are diagnostic: timer
overhead especially affects very short selection blocks. No subtractive correction.

Stage 22: star/complete graphs; 5/15/30 systems; 128/512/2048 items;
strong separated scores and exact ties. Offline make_paths is timed separately
from graph acquisition. Original budget snapshots and stopping rules retained.
Stage 31: uniform and unresolved selection; 5/15/30 systems; 256/1024/6000
available rounds; 16/256/1024 candidate panels. Five-way panels, original 70%
target and 95% threshold. Exhausting rounds is a capped run, not successful stopping.
Exact sequential: two binary systems only, 8/16/32/64 items, q=1/.5;
aligned strong, moderate and adverse priors. Original alpha=.05, solver and
termination rules. No extrapolation to unsupported multi-system inference.

Per-child timeout 120 seconds; timeout is retained as censored. Setup/imports are
separate from algorithm wall time. Peak working set includes imports, fixture and
instrumented pass, so is process-level, not incremental algorithm memory.
Phase definitions and individual repetitions are saved with the implementation.
Selection p50/p95 are across actual decisions within an instrumented run.
CPU utilization = process CPU / wall (one fully occupied logical core =100%).

Human latency sensitivity: 10/30/60 seconds per cell; 30/104/180 seconds per
five-way panel. Historical WMT17 DA ~17 seconds/translation and WMT16 relative
ranking ~104 seconds/five translations are anchors, not new measured user times.
Serial model = computation + queries * latency; ideal parallel sensitivity uses
10/100 workers, ignores interaction/network/training and assumes perfect load balance.
Report limitations, bottlenecks and conditional GO/NO-GO; no new optimizations.
