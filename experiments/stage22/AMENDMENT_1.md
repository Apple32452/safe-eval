# Stage 22 execution-only amendment

After the locked one-language smoke run and before any full-run output was
written, the single-process 14-language command was started. It remained
healthy at 100% CPU but had not completed or printed the first language after
more than three minutes. The process was interrupted before creating its
output directory; no full-run result was available or inspected.

The experiment will therefore run each language as a disjoint shard using the
already locked `run_stage22.py`, identical master seed, 50 repeats, graph
suite, methods, thresholds, and gate. `merge_stage22.py` performs only a
validated concatenation and deterministic row sort. It rejects overlapping
languages and disagreement in all fixed metadata. The independent audit still
replays repeat zero from the unsharded runner.

This amendment changes execution time only. It does not alter the method,
data, outcome access, reference averaging, comparisons, metrics, success gate,
or untouched WMT24 status.
