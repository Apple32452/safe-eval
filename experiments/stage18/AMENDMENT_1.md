# Stage 18 technical amendment 1

The first one-repeat software check completed the common-control simulation but
the summarizer stopped before reporting a comparison. It loaded all 50 archived
Stage 17 repeats while the smoke-test grid correctly expected only repeat zero.

Before any 50-repeat Stage 18 control was run, the candidate loader was changed
to retain only keys in the requested Stage 18 grid. This has no effect on the
frozen 50-repeat comparison, whose requested keys already include all 50 Stage
17 repeats. The protocol, acquisition method, e-process, seeds, budgets, gate,
and saved smoke outcomes were not changed. The corrected summarizer and updated
implementation lock were committed before continuing.
