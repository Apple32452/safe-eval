# Evaluation method screening before acceleration

Read [REPORT.md](REPORT.md) for the NO-GO recommendation and qualifications.
No previous method or result is modified. No WMT data is read. New algorithms
or optimized SAFE-EVAL implementations are not delivered; the fixed-law adapter
is a comparison control around the existing exact paired solver.

From repository root, Python 3.12 with NumPy, SciPy, psutil and matplotlib:

```powershell
python -u experiments/method_screening/screen.py
python experiments/method_screening/two_system.py
python experiments/method_screening/fixed_law.py
python experiments/method_screening/analyze.py
```

These overwrite only this directory's outputs. Save copies before comparing
machines. Single-thread BLAS/OpenMP settings are set before NumPy imports.
The main screen runs 84 fresh-process timings and reconstructs 100 archived
matrices' matched method costs. The two-system supplement reuses 30 matrices,
checks every original full-block path prefix, replays six original DP paths,
and checks 384 tiny paths for the learning paired adapter. The fixed-law
diagnostic checks another 384 paths and matches both DP directional alternatives.
The two adapters' exhaustive checks concern accounting/correctness on tiny
examples, not a proof of worst-case error probability.

`results/manifest.json`, `two_system_lock.json` and `fixed_law_lock.json` record
source hashes and frozen inputs. `verification.json` audits preservation,
reproducibility and path/cost parity. Main, the 100-matrix archive, and the earlier
computational profile remain unchanged. The initial direction-mismatched
fixed-law diagnostic is preserved but excluded; a clean final rerun does not
need to reproduce that discarded intermediate result.

`matched_archive.csv` and `paired_archive.csv` contain all primary matched
strata; `timings.jsonl` and `timing_summary.csv` preserve raw and summarized
computational measurements. `two_system.json` keeps old/new Stage22 costs,
full uniform paths, purchases and DP replay evidence. `fixed_law.json` contains
the strongest directional-law comparison. PNG plots are generated from these
saved measurements. No aggregate score mixes incompatible tasks.

Existing tests executed successfully in this session:

```powershell
python -m unittest discover -s experiments/joint_order_controls -p test_controls.py -v
python -m unittest discover -s experiments/exact_sequential_probe -p test_sequential_probe.py -v
```

Five control tests and two sequential tests passed, including pre-observation
predictability, null-completion feasibility, unique purchases and retirement.
Previously archived large conditional-expectation audits are reused, not rerun.
