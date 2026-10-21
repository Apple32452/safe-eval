# Adaptive partial-cell inference: final assessment

**NO-GO for this candidate as an ICML-level new contribution.** Partial-cell acquisition can save labels relative to Stage 22, but the separation is already attained by existing joint evidence controls. No new correlation-sharing or efficiency theorem beyond those controls has been established.

| Method | Mean unique labels | Candidate change vs method |
|---|---:|---:|
| stage22 | 15.398 | -6.67% |
| partial_hedge | 14.371 | +0.00% |
| joint_product | 14.371 | +0.00% |
| joint_mixture | 14.371 | +0.00% |
| peak_wor_adaptation | 14.371 | +0.00% |
| hedge_round_robin | 14.527 | -1.08% |

These are equally weighted results on 24 fixed small binary matrix/graph cells and 20 matched path seeds, not an estimate of WMT performance. Partial-cell methods share per-system uniform streams; Stage 22 necessarily follows a common paired item stream. Equal budgets, estimands and nominal family error are matched; purchased paths differ.

- Versus stage22: mean label difference -1.0271, conditional MCSE 0.0375; 13 improved / 4 tied / 7 worse cells.
- Versus joint_product: mean label difference +0.0000, conditional MCSE 0.0000; 0 improved / 24 tied / 0 worse cells.
- Versus joint_mixture: mean label difference +0.0000, conditional MCSE 0.0000; 0 improved / 24 tied / 0 worse cells.
- Versus peak_wor_adaptation: mean label difference +0.0000, conditional MCSE 0.0000; 0 improved / 24 tied / 0 worse cells.
- Versus hedge_round_robin: mean label difference -0.1562, conditional MCSE 0.0245; 10 improved / 7 tied / 7 worse cells.

## Proven findings

The exact-rational binary implementation has 95% anytime joint coverage and thus familywise coverage of every requested sign, under predictable system selection and fresh uniform sampling within its remaining items. PPR processes are supermartingales at support boundaries; the proof does not incorrectly demand equality of conditional expectation there. The PEAK-style adaptation uses the predictable remaining null mean and is proved separately. See THEORY.md. No finite-grid guarantee for arbitrary continuous MT scores is claimed.

All 2,880 method/path records finished with zero observed wrong declarations; all five partial-cell arms had 100% observed joint coverage over their 480 paths each. These tiny fixed matrices do not estimate worst-case coverage. The proof, rather than the empirical rate, establishes the guarantee. A separate [bounded-score implicit construction](CONTINUOUS_PROOF.md) extends the PEAK-style joint argument mathematically, but no tractable continuous solver has been implemented or tested.

For an N-item reference-star population with reference scores all one and L all-zero leaves, compatible-completion certificates require at least N+L labels. Reference-first acquisition attains this bound. With N=4/6/8 and L=2 it costs at most 6/8/10 versus Stage 22 costs 9/12/15 for its unchanged certificate and specified within-item order. These are restricted, exact separations; they are not lower bounds over all 95%-valid procedures. Existing joint controls attain the same upper bound.

## Novelty and unresolved limitations

The post-run diagnostic in RANGE_ONLY_AUDIT.json independently recomputed the simple remaining-range certificates on all 480 candidate paths. Every edge's resolution time was identical to the candidate. Therefore this study establishes an allocation/range-accounting benefit, not an empirical statistical-efficiency gain from joint evidence. It cannot distinguish the statistical power of the joint methods on larger or more difficult pools.

Failure cases matter: the 8-item extreme and reversed-extreme complete graphs cost the candidate 24 labels versus Stage 22's 21, a 14.29% increase. Exact ties required the full matrix. The allocator is neither uniformly better nor globally optimal. The 33.33% extreme-star benefit is real but also achieved by all matched joint controls.

Joint adaptive-stream testing (PEAK), products of arm martingales (Kaufmann/Koolen), and finite-pool PPR inference already cover the key construction. Fixed hedging, shared caching, projection and a reference-first schedule do not establish a genuinely new method. Correlation is not borrowed to infer unseen coordinates. The prototype is binary-only, exponential in system count, and the reference-first policy may oversample an unhelpful anchor. See RELATED_WORK.md and failure cells.

A literal post-observation-remaining-mean substitution in the cited Ryu/Wornell categorical WoR expression fails a two-item check; this expression was excluded from matched-validity comparisons pending source/implementation clarification. This does not refute the authors' general vector-gambling framework or establish our superiority over its full algorithms. The experiment does not establish dominance over every strongest existing Joint-CS implementation.

## Recommendation

Do not start WMT or an ICML submission from this construction. A GO would require a tractable continuous-score partial-cell certificate with an instance-dependent improvement that survives existing joint/stream controls, or a genuine computational/lower-bound separation. That theoretical gap remains open. No additional synthetic tuning is justified by the present evidence.
