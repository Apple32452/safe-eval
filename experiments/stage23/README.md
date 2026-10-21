# Stage 23: paper-level contribution audit

Stage 23 does not run a new benchmark experiment. It decides whether the
audited Stage 22 result supports a technically distinct paper contribution
after comparison with the closest 2026 sequential-ranking work and classical
common-random-number ranking-and-selection literature.

Read `PROTOCOL.md` for the frozen gate, `PRELIMINARY_AUDIT.md` for the current
boundary, and `THEORY.md` for the restricted minimality statement. WMT24
remains untouched. The independent exhaustive audit is:

```bash
python -m unittest discover -s experiments/stage23 -p 'test_*.py' -v
python experiments/stage23/audit_stage23.py
```

No external validation is authorized until the contribution audit passes.

