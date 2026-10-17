# Stage 10 research record

- The user authorized the stronger-baseline and novelty study after reviewing
  Stage 9's modest aligned gain and unfavorable calibration comparisons.
- Main is now 90b44f3175568704f37a3703d086f27b26437a19. Its tree matches the
  complete audited Stage 9 result tree. All prior stage manifests pass.
- Wrote PROTOCOL.md before implementing or inspecting fine-calibration
  benchmark comparisons. Twelve outcome-independent bisections and fixed
  repair-investigation resource limits are specified in advance.
- Before implementation or any new benchmark comparison, made the repaired
  investigation concrete: if its initial exact count completes within the
  fixed limits, examine three predetermined lower thresholds without a
  monotonicity assumption. Use only completed valid counts for repair_raw95;
  otherwise retain fine_raw95. The primary contrast is against repair_raw95.
- Initial mathematical resource checks capped all three repair counts. N=154
  reached 102 of 154 layers with 41,283 peak states before exhausting five
  million transitions. Before any Stage 10 benchmark comparison, preserved the
  initial source, logs and attempts and revised the final fixed limits to
  one million states and twenty million transitions for every actual pool.
  Twelve fine-search bisections and all thresholds remain unchanged. Fresh
  certificates are regenerated from the revised source. No favorable cost
  result motivated this resource change.

## Frozen comparison and completed audit

- Froze the protocol, implementation and source-trace manifest at
  f163038f4fadc00d50609a565b4952429671f751 before the benchmark comparison.
- The comparison completed all 117 cases and 70,200 trajectories in 34.1
  seconds, including 46,800 unchanged Stage 9 source trajectories.
- The independent audit passed in 243.3 seconds: 70,200 saved decisions,
  2,340 preserved Stage 9 metrics, 1,568 backward fine-risk counts, four exact
  repaired-risk certificates, 23,400 raw95 stopping bounds and 12,313,800
  new-control query replay steps. No new prediction-capital replay is claimed.
- Aligned prediction saves 0.666% against the selected finer control, or 1.813
  labels with conditional MCSE .273. It improves 18 target means and worsens
  21; German and both adverse histories favor calibration. About 42% of the
  earlier absolute mean-label advantage disappears with finer calibration.
- The N=154 repaired counts complete, but all three lower grid thresholds are
  invalid. The two larger repaired counts are capped under the recorded final
  resource limits. The selected repaired control equals fine_raw95 everywhere.
- The twelve primary language/history report contrasts were independently
  reconstructed from per-trial costs and matched the frozen analyzer.
- Added plot_stage10.py after the freeze as presentation-only code. It reads
  already-audited comparison values and changes no metric or inference rule.
- The frozen code is published on research/stage10-calibration-audit. After an
  interrupted result upload, publication resumed on 2026-10-17 at the user's
  request. The compact result package contains the final findings, completed
  audit, certificates, tables, figure and file manifest.
- All 117 lossless Stage 9 curve files remain available locally. Their hashes,
  saved decisions and reference metrics were verified before reuse.
