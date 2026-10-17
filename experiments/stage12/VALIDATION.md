# Validation record

Base: main merge commit `38c10afc084b8af9284b21d9364c0478effd254b`,
tree `48193bba65852ee35eac39460b781ba0326860ef` (merged Stage 11).

Local checks on 17 October 2026:

- All 61 tests passed: 28 Stage 7, seven Stage 8, eight Stage 9 and six each
  in Stages 10, 11 and 12. Each stage ran in a separate Python process.
- The Stage 12 exhaustive audit passed 9,828 top-k budget probes and 3,276
  boost states. It enumerated 27,972 assignment expectations for the identity
  checks and 9,324 for the boost checks. Arithmetic was exact throughout.
- The two-item counterexample returned working expectation 1, actual
  conditional expectation 185/181 and corrected multiplier 1.
- A fresh audit output matched the committed reference dictionary, including
  hashes of all three Stage 12 Python source files.
- All 163 files listed in the Stage 7--11 manifests retained their hashes
  (48, 23, 32, 35 and 25 respectively). Stage 8--11 protocol checks passed.

The workflow adds Stage 12's six tests and exact reference comparison to
the existing Ubuntu/Python 3.9 and 3.12 and macOS/Python 3.12 checks. This
record describes local results; remote workflow status is available on the
pull request. Earlier benchmark audits and results are reused, not rerun.

No WMT outcomes, benchmark settings, or historical-fit choices were changed.
No new human annotations or confirmatory data were acquired. These checks
establish one-step algebra and its reference implementation, not novelty,
full confidence-sequence coverage for a new method, or label-cost superiority.
