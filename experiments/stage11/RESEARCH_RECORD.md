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
