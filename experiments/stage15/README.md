# Stage 15

This directory contains the pre-result protocol, locked implementation and
audited WMT23 development result for annotation-level frontier utility. See
`FINDINGS.md` for the result and limitations.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m unittest discover -s experiments/stage15 -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python experiments/stage15/frontier_experiment.py --languages en-de he-en zh-en --repeats 50 --output results/stage15_local
python experiments/stage15/summarize_stage15.py --input results/stage15_local
python experiments/stage15/audit_stage15.py --input results/stage15_local
```
