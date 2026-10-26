# Anytime pairwise scalability audit

Read REPORT.md for results, COMPLEXITY.md for restricted equivalence arguments,
and RELATED_WORK.md for the primary-source review. Branch starts at 5d991e7.
No previous method is optimized or edited. All inputs are synthetic.

From repository root (Python 3.12, NumPy, psutil and matplotlib):

```powershell
# Preserve the shipped results AND checkpoints before a fresh run.
Move-Item -LiteralPath experiments/scalability_audit/results -Destination experiments/scalability_audit/results_previous
python -u experiments/scalability_audit/audit.py
python experiments/scalability_audit/diagnostic.py
python experiments/scalability_audit/analyze.py
python -m unittest discover -s experiments/stage22 -p test_stage22.py -v
```

Runs write only this directory's results. Start with a fresh results directory;
old checkpoints must not remain because the parent monitors their phase fields.
The benchmark takes several minutes and retains timeouts. It imports
the existing profiling instrumentation helper but never changes the source files.
BLAS/OpenMP threads are fixed to one. No WMT data, including WMT24, is loaded.

## Files and interpretation

- manifest.json freezes the 20-case matrix, source hashes, environment, repeats
  and a preflight memory exclusion. raw.jsonl has all 60 evidence repetitions.
- case_*.json are worker checkpoints; a timeout cannot erase completed evidence
  measurements. worker_stderr.log preserves unexpected errors.
- summary.csv/json contain medians, ranges, phase p50/p95 and replay outcomes.
- verification.json checks exact event/evidence parity, phase call counts,
  smallest-fixture replay parity, source preservation and main preservation.
- systems_scaling.png and items_and_phases.png visualize the measured matrix.

Plain evidence wall/CPU includes make_paths validation, gathers, CS arithmetic,
crossings and complete output arrays, but excludes imports/fixture construction.
Phase timings come from a SECOND instrumented pass, with exact array parity;
their costs cannot simply be subtracted from first-pass wall times. CS-update
phase includes centering, both directional wealth updates and mixture reduction.
Stop phase includes statistical crossings and deterministic finite-pool endpoints.
Their p50/p95 measure an entire P-pair common-item batch. This is fixed-null
sign testing, not interval endpoint inversion. Other attribution includes input
validation, dense difference construction and evidence recording.

Replay is measured only for repetition zero (one observation per case), with
instrumented global predicates and original close_free. Do not report its timing
as a three-repeat median. Global stop time includes comparison plus np.any;
availability time includes cursor/event resolution but no new wealth arithmetic.
The other repetitions do not rerun replay. A 45-second replay timeout is censored,
not a full runtime or failed statistical run. No partial labels/costs are reported.

Memory is OS process high-water working set, not algorithm-only allocation.
Plain peak is captured after the first pass; attribution peak also includes
two retained output sets and timers. A censored replay may exceed its last
recorded peak: report that peak only as the checkpoint's observed value.
The 1.5-GiB preflight estimate is a workload filter, not an OS memory limiter.
Single-machine timing varies; all observations and ranges are retained.

The engine intentionally computes full future-label paths for offline simulation.
This is not an online evaluator or evidence that labels can be read before a
query. Validity claims concern the original common-prefix and fixed support
assumptions. No proposed counter, dependency index, streaming runner, alternative
CS or faster stopping implementation has been built or benchmarked.
