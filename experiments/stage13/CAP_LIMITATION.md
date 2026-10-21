# A cap limitation in the frozen family-wide reserve

The frozen reserve implementation caps both the raw evidence and each betting
expert at the largest decision threshold, 9480, before forming its 75/25 mixture.
That is valid but introduces an avoidable loss of power in the family-wide
setting. It was identified when interpreting the audited reference results.

If R<=B and H<=B, then (3R+H)/4>=B if and only if R=H=B. Furthermore, H is the
average of eight betting experts, each capped at B, so H=B requires all eight
experts to have reached their individual caps. Thus a family-wide statistical
reserve decision requires saturation of both the raw branch and every expert,
unless the deterministic finite-pool certificate decides first. This is a
conjunction caused by component capping, rather than the intended flexibility
of an uncapped fixed mixture.

The per-pair threshold is only 40. A capped raw branch alone contributes
7110, and a single capped betting expert contributes 296.25 to its mixture.
Those contributions exceed 40, so the same cap does not create this particular
directional-crossing bottleneck in the per-pair setting.

Validity is preserved: capping, downward rounding and predictable stopping
remain conservative. The standalone paired-PPR family results directly test
their own threshold and can be used for the feasibility question. The reserve's
family costs should not be used to infer a fundamental disadvantage of history,
or to compare with a properly implemented uncapped mixture.

A bounded follow-up would give each component a ceiling at least its decision
threshold divided by its mixture weight. A common ceiling of 32*9480 is
sufficient for these weights. Raising the ceiling also requires overflow-safe
integer updates; merely changing CAP in the frozen code is unsafe. This
correction has NOT been implemented or evaluated in Stage 13. All reported
Stage 13 results retain the original protocol, sources and query seeds.
