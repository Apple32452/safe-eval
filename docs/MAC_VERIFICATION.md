# Stage 7 reproduction on Taewoon's Mac

On October 12, 2026, the submitted terminal log showed:

- All 28 invariant tests passed in 0.849 seconds.
- The fixed run used 100 repeats and two workers.
- All 117 cases and 117,000 method trajectories completed in 244.0 seconds.
- The analyzer reported checks of 117,000 saved decisions and 35,100 reserved
  stopping bounds, audits of all 117 full-curve case bundles, and matching of
  11,700 paired Stage 6 raw stops.
- No traceback or failed test appeared.

The submitted log's 117 case rows and all 585 displayed query means matched
the released reference log exactly at the displayed one-decimal precision.
Cases were matched by scenario, language pair and target system; worker output
order was allowed to differ. These are log comparisons, rather than a separate
read of the Mac's saved per-trial files.

This reproduces the existing Stage 7 diagnostic. It does not add independent
models, raters or a new held-out release. Complete findings and their limits
remain in the released experiment's FINDINGS.md.
