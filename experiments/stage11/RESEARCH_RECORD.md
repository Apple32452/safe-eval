# Stage 11 record

- User authorized the next baseline comparison on 2026-10-17. Stage 10 PR #3
  was merged by the user; parent main faa189d8888a7ad46afd8a007ab3cbc525a47026
  matches the complete audited Stage 10 tree. Earlier stages are preserved.
- Read Fischer and Ramdas, arXiv:2410.16076v4, especially Algorithm 1,
  Theorem 1 and Sections 4.1–4.2. Chose to apply the general algorithm to
  the same two-sided PPR factors; this is not their particular RiLACS example.
- Wrote PROTOCOL.md and THEORY.md before any new benchmark comparison.
  Fixed Q=2^39 using the signed-int64 bound for all actual pool sizes.
- Added six invariant tests. All pass, including rational conditional
  expectations, all small binary strings, independent observed-branch replay,
  degenerate populations, hull holes, prefix dependence and integer bounds.
- Verified all 70,200 source decisions and 3,510 source metric values and
  wrote the full Stage 10/9 source fingerprint manifest before the comparison.
- The new benchmark comparison has not been run at the protocol freeze.
  Existing prediction-capital and calibration audits will be reused explicitly.

## Completed comparison and independent audit

- Published the freeze commit 7415fecdd7a38074b1901ad63baca10f17e15cee before
  running the new fixed paired benchmark comparison.
- The comparison completed all 117 cases and 93,600 compared trajectories in
  34.5 seconds, including 70,200 unchanged source trajectories.
- Independent replay passed in 20.3 seconds: 93,600 saved decisions, all 3,510
  preserved source metrics, 4,680 total target metrics and 11,700 matched
  stopping bounds. It verified 39 distinct ledgers, 4,104,600 distinct
  method-query replay steps and 377,007,310 live candidate wealth updates.
- No grid interval endpoint or stop differs from the preserved floating raw
  control on any saved path. Boosted sets contain holes on five distinct
  paths; the implementation retains all candidates and returns their hull.
- The primary aligned gain is .341% (.925 labels; conditional MCSE .366).
  Prediction wins 15 target means and loses 24. Both adverse conditions lose
  on all 39 target means; worst observed extra cost against boosting is 260.
- After the frozen audit, added report_stage11.py for independent per-trial
  report reconstruction and plotting only. All 120 comparisons match. No
  inference rule, precision threshold, source trajectory or hypothesis changed.
- The frozen GitHub workflow run 39061866493 passed: all 55 repository tests
  across Ubuntu Python 3.9/3.12 and macOS Python 3.12, plus the configured
  existing end-to-end checks. Stage 11's full new comparison is audited locally.
