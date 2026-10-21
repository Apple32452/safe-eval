# Stage 21 findings: pilot-selected chain certification

## Result

The frozen development gate failed decisively. At 75% labels, the primary
selected-chain method produced 37.04 correct all-pair conclusions per repeat,
compared with 1,275.70 for the Stage 18 all-pair common test set. The deficit
was 1,238.66 conclusions (conditional Monte Carlo standard error 1.78), with
losses in all 50 repeats and all 14 language means. Both methods made zero
observed wrong conclusions.

The selected chain produced no conclusions at the 25% pilot checkpoint. At 50%
labels it produced 6.46 conclusions versus 790.68 for the baseline; at 75% it
declared 2.34 adjacent edges and added 0.30 conclusions by closure per language
and repeat on average. It never certified a complete ranking.

Reducing the tested family did help the intended component: at 75%, the
`40(S-1)` selected-chain threshold produced 37.04 conclusions versus 22.02 for
the otherwise identical `40S(S-1)/2` ablation. The gain was far too small to
offset the fragility of a chain, where one difficult or pilot-inverted adjacent
edge blocks an entire transitive segment.

## Integrity and audit

The one-repeat simulation completed, but the initial reporter had a Python
parse error and produced no comparison. `AMENDMENT_1.md` records the
parentheses-only correction. The corrected reporter, compile check, and lock
were committed before the smoke result was read or the full experiment ran.

The conditional e-process passes exhaustive checks over every five-item ternary
null population and permutation. The final audit verifies the implementation
lock, WMT25 hashes, exact Stage 18 reference, all 4,200 saved rows, closure and
budget accounting, and an exact 84-row repeat-zero replay.

## Research decision

Pilot-selected adjacent certification is valid but empirically unusable for
this target. It should not be tuned further on WMT25. Together, Stages 18--21
show that the common random test set is a strong baseline; pair-specific tails
lose badly, safe pruning gives only a 0.665% gain in six languages, and a
selected chain sacrifices too many direct conclusions.

The current experiment line has not produced an ICML-level contribution. The
Stage 20 pathwise pruning theorem is the strongest new technical result, but its
complete-graph effect is too small and recent adaptive-evaluation and sequential
model-confidence-set work substantially overlap the broad framing. A new paper
direction should be agreed before accessing WMT24 or running further WMT25
variants.
