# Stage 24: joint finite-pool feasibility, frozen before results

No WMT outcomes are loaded. No previous stage is changed. This is a feasibility/falsification study, not a confirmatory ICML result.

## Candidate

One joint mean-vector betting CS, with predictable integer directions selected using a regularized covariance estimate of previously observed complete rows. Each system-item score is charged once. Test a uniform common-row acquisition and an outcome-adaptive weighted-without-replacement row acquisition. Historical synthetic predictions influence only acquisition. All unobserved rows have positive known probability. Every query purchases all systems on its selected item; adaptive system-subset acquisition is proved abstractly but is NOT implemented in this pilot.

The proof is general for bounded scores; the executable inversion is restricted to binary scores, enumerating all integer system totals. No assumed covariance model, Gaussian approximation, independence across systems, or asserted low-rank population structure is used. Floats choose the predictable bet direction; exact integer factor formulas and downward-rounded wealth certify acceptance conservatively.

## Comparators

- Unchanged Stage 17 pair evidence plus unchanged Stage 22 active-vertex scheduler, using the original 0.05 family budget.
- Per-system beta-binomial prior/posterior ratio CS with alpha=0.05/system_count, projected to pair signs and scheduled with the same Stage 22 pruning. This is an existing-method baseline, not a novelty claim.
- Joint diagonal-bet ablation on exactly the same uniform row order (isolates covariance use).
- Joint covariance-bet method, uniform rows.
- Joint covariance-bet method, adaptive rows. This last comparison changes both acquisition and evidence relative to Stage 22. Its corrected HT innovations do not use an invalid uniform-row likelihood.

## Synthetic design

Two small shapes: 4 systems x 8 items (star, ring, complete graphs), and 3 systems x 24 items (star, complete; ring is identical to complete and omitted). Four fixed binary matrix families: common-factor strong gap, independent strong gap, common-factor weak gap, and antagonistic systems. Generate from fixed master seed 20261029; include exact ties when generated. Three histories: aligned but noisy auxiliary scores, constant/uninformative scores, and reversed auxiliary scores. History never enters the certificate. All matrices/seeds are generated and saved before methods run.

20 independent held-out path seeds per matrix/graph/history cell. Uniform methods share item permutation and within-item system order. Adaptive method uses the same initial uniforms as a coupling, not the same item path; changing probabilities necessarily changes paths. Deduplicate uniform results across histories in interpretation. Report per-cell and aggregate costs, paired differences, win/tie/loss, error rates, and full-population fallback. No hyperparameter search, method selection by observed gains, or WMT experiment.

## Decision gate

A research GO requires all of: a claim beyond direct combinations of existing vector CS / adaptive inverse probability betting; correct proof and exact small-state checks; at least 5% overall unique-label reduction against BOTH Stage 22 and per-system CS; strict benefit in at least two distinct matrix families; and no family with more than 5% excess cost. Otherwise NO-GO for this candidate as an ICML contribution (not an impossibility result for all joint inference).

## Verification

Independent Fraction arithmetic verifies one-step conditional means and factor expectations, including adaptive unequal probabilities and partially observed system-cell designs. Exhaustively enumerate all 2-system x 3-item binary matrices and every adaptive acquisition branch for the implemented joint CS, using exact rational path probabilities. Check familywise coverage, label uniqueness, predictability, exact full-pool/tie handling, covariance versus diagonal distinctions, and deterministic reproduction. Previous-stage source hashes and new source hashes are checked before/after. Small-n zero errors do not establish the theorem or general efficiency. The standard vector-betting ingredients are not new; the source comparison determines whether any distinct theorem remains.
