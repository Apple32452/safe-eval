# Stage 7 research record

1. The user completed Stage 6 locally: 18 tests passed; all 117 printed case
   rows and 468 displayed numbers matched the reference. They then supplied
   the successful analysis completion for 70,200 decisions, 46,800 active
   stopping bounds and 117 replayed query ledgers.
2. The prespecified next diagnostic was to apply the unchanged Stage 5 methods
   to the same WMT23 data. This is not a newly tuned method or untouched data.
3. Stage 5 statistical modules and their prior tests were copied byte for byte.
   The WMT23 parser/extracts and Stage 6 comparison rows were also preserved.
4. All 117 folds, seeds and transformed historical banks match the Stage 6
   reference. A compatibility test matched one actual WMT23 raw stream and its
   raw precision stops, and checked lossless curve encoding. No prediction-cost
   comparison from that test selected a setting or method.
5. All 27 compatibility/statistical tests passed before the diagnostic freeze.
   Primary reserve_mix75 and all secondary controls retain their previous
   settings; 50%/90% reserve weights remain diagnostics.
6. The new adapter, full-path audit, plotting code, parent records and comparison
   protocol were frozen before prediction-cost summaries were inspected.
7. The full comparison uses 117 cases, 100 repeats and ten Stage 5 methods.
   The Stage 6 active10/random10 rows are reused as paired comparator costs.
8. The independent analysis audits saved full interval curves, original-grid
   PPR replay, first precision decisions and reserve inequalities. Its result
   and counts are retained in `results_reference/VERIFICATION.json`.
9. The first full-curve audit compared numeric endpoints even when both raw
   intervals were empty. Stage 5 uses canonical [1,0] for an empty candidate
   set; the previous raw interval intersection can have other inverted bounds.
   The audit was corrected to require identical nonempty flags and exact
   endpoints whenever nonempty. Different empty representations are counted
   explicitly and remain coverage failures. A finite-grid enumeration test
   was added; the release has 28 tests. No statistical module, dataset,
   parameter, decision or performance result changed. Original analyzer and
   failure output are preserved in `development_audits/`.

Future edits to acquisition or predictor rules must treat WMT23 as development
data. The statistics concern recorded binary annotation means on fixed pools,
with unit target-segment query cost. Historical annotation cost, human time,
rater reliability and future populations are outside the comparison.
