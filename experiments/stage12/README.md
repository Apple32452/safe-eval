# Stage 12: contribution audit and exact small-pool checks

Start with [the novelty assessment](NOVELTY_AUDIT.md). The result is a clearer
contribution decision and a checked mathematical extension, not a new WMT
experiment or an established novel method. Stages 7--11 remain unchanged.

From the complete repository root:

```bash
python -m unittest discover -s experiments/stage12 -p 'test_*.py' -v
python experiments/stage12/audit_stage12.py --output results/stage12_local/VERIFICATION.json
```

These standard-library checks take seconds. No GPU, dataset, network access,
paid service, or previous experiment output is required. The audit uses
exact fractions and enumerates all assignments in each recorded small-pool
state. Its saved source hashes identify the implementation that was checked.
The general algebra is proved in [THEORY.md](THEORY.md); finite enumeration
checks the implementation and does not replace that proof.

[Reference verification](results_reference/VERIFICATION.json) records 9,828
top-k probes and 3,276 boost states. Zero-factor saturation and additional
endpoints/ties are covered by the six unit tests. The test grid itself contains
no unbounded-boost states, which is reported explicitly.

[PRIOR_WORK_INSPECTION.json](PRIOR_WORK_INSPECTION.json) fingerprints the selected
MPOS author-code files inspected from the public archive. Their ZIP member
CRCs were checked; the complete archive's MD5 was not independently computed.
No third-party source code is redistributed or executed here. The archive
contains no manuscript; the audit records that limitation.
