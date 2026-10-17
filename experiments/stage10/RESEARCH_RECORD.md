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
- All 117 lossless Stage 9 curve files remain available locally. They will
  be hashed and their saved decisions/reference metrics verified before reuse.
