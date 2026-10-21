# Stage 14: exploratory shared-label pilot

This pilot tests one part of the proposed allocation direction. It uses
precommitted uniform pair-specific query streams and counts each unique
system-item label once across all comparisons in a language. The target is
the direction of the fixed WMT23 binary error-free proportion difference,
not a practical MQM margin or an official WMT ranking. See PROTOCOL.md and
FINDINGS.md for the design, post-pilot amendment and interpretation.

From the repository root with Python, NumPy and SciPy installed:

```bash
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest discover -s experiments/stage14 -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage14/shared_pilot.py --languages en-de he-en zh-en --repeats 12 --output results/stage14_local
python experiments/stage14/summarize_pilot.py --input results/stage14_local
```

The reference `results_reference/` directory contains compact replicate
counts, source-provenance metadata and an accounting summary. Source data
are checksummed by the existing Stage 7 loader. The initial three-policy
output was saved before adding the two post-pilot concentration controls.
