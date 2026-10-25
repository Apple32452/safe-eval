# SAFE-EVAL computational efficiency study

Read `REPORT.md` for findings. This directory benchmarks original algorithms;
it introduces no optimization or new statistical method. Synthetic inputs only;
no WMT dataset is read.

## Reproduce

From repository root, with Python 3.12, NumPy, SciPy, psutil and matplotlib:

```powershell
python -u experiments/computational_profile/benchmark.py
python experiments/computational_profile/hotspot.py
python experiments/computational_profile/preprocessing.py
python experiments/computational_profile/analyze.py
python experiments/computational_profile/verify.py
```

The benchmark overwrites this directory's results; archive them before comparing
machines. Three fresh children run sequentially per case, each with a 120-second
deadline including both timing passes. Errors/timeouts remain in `raw.jsonl`.
No timing outlier is removed. BLAS/OpenMP thread counts are fixed to one.

## Outputs and interpretation

- `manifest.json`: matrix, source hashes, versions and machine.
- `raw.jsonl`: all repetitions, wall/CPU, process memory, timed phases and selection
  p50/p95/max. Plain versus instrumented full output digests must match.
- `summary.csv` / `summary.json`: medians and observed wall-time ranges. These
  are timing repetitions of fixed fixtures, not uncertainty over datasets/seeds.
- `latency.csv`: assumed human latencies and ideal worker-count sensitivity.
- `exact_hotspot.json`: separate cProfile diagnostic, not authoritative timing.
- `preprocessing_cpu.json`: warmed-process supplement for Stage 22 offline CPU;
  separate from the fresh-process benchmark and not added to its timing medians.
- `scalability.png` / `bottlenecks.png`: plots from saved measurements.
- `verification.json`: preservation, phase accounting and reproducibility checks.

Timed phases are disjoint. Stage 22 selection commits active blocks and advances
the chosen-label cursor; inference calls close_free within each acquisition. Its
full-path evidence calculation is separately timed offline. Stage 31 selection
scores candidate panels; inference updates wealth and decisions. Exact inference
covers Design construction and both factor solvers; selection chooses the item
and purchase mask. Other includes loop checks, validation, bookkeeping, snapshots,
final rank closure and timer overhead. The inference fraction therefore excludes
some broadly statistical work, especially final rank closure. No double counting.

Plain wall/CPU exclude imports/fixture setup, Stage 22 evidence precomputation,
and Stage 31 panel enumeration; those costs are reported separately. Setup wall
begins after NumPy/psutil imports, includes module imports/fixtures/AST compilation,
and is not a clean production cold-start estimate. Subprocess elapsed includes
both timing passes and interpreter startup; it is not algorithm runtime.

Peak plain memory is the OS process high-water working set through the plain pass,
including imports, setup and transient allocations. Peak process memory also
includes the instrumented pass. Ready RSS is saved, but subtracting these measures
does not estimate algorithm-only memory. CPU percent uses one core as 100%.
Windows CPU-clock quantization and scheduling noise limit short-run precision.
Phase fractions come from instrumented runs and have timer overhead; use plain
wall time as authoritative. No subtractive timing correction is applied.
Phase fractions pool instrumented seconds across the three repetitions so that
the three disjoint fractions sum to one; timings/quantiles use repetition medians.

Stage 22 replay consumes precomputed full-path evidence. Future synthetic labels
are used only to benchmark this historical offline simulator. This is not an
online implementation or a deployment label-leakage claim. Profiling establishes
no statistical guarantee. Original thresholds/stopping rules are unchanged.
Stage 31 capped runs are flagged incomplete. Exact sequential supports only two
binary systems; no multi-system scaling claim is made for it.

Parallel latency scenarios are optimistic aggregate-work lower bounds, not a
scheduling implementation. A strictly adaptive single trajectory cannot generally
keep 100 annotators busy without changing its sampling protocol.
[WMT17 findings, Table 9](https://www.statmt.org/wmt17/pdf/WMT17.pdf) gives historical
anchors: DA 17.1/17.5 seconds per translation; five-translation RR 20.8 seconds per
translation, hence 104 seconds per panel. These idle-filtered, task-dependent
historical averages do not measure SAFE-EVAL annotation time.
