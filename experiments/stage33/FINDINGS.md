# Stage 33 findings: public WMT11 feasibility audit

The full WMT11 individual-systems ranking CSV archived in
[Lopez's repository](https://github.com/alopez/wmt-ranking)
has 7,842 human ranking rows. We retained 7,694 complete rankings
of five distinct nonblank systems with valid ranks. For nonreference
system pairs on the same source:

| Descriptive quantity | Count |
| --- | ---: |
| Pair/input cells seen with different companion panels | 5,854 |
| Such cells with at least two distinct raters | 4,454 |
| Opposite nontied outcomes across different panels | 948 |

The last count is **not caused reversals**: panel, rater and task vary,
and annotation noise can reverse a preference.

For the specific descriptive contrast of reference-present versus
reference-absent companions, Y is +1 for A preferred, -1 for B
preferred and 0 for ties. The difference is reference-present minus
reference-absent on the **same input and system pair**:

| Matched cells | Pair/input cells | Source items | Mean difference | 95% item-cluster bootstrap interval |
| --- | ---: | ---: | ---: | ---: |
| Disjoint raters across conditions | 1,611 | 693 | -0.0148 | [-0.0597, 0.0343] |
| All matched cells | 2,389 | 930 | -0.0043 | [-0.0405, 0.0327] |

Both intervals span zero. This offers **no clear evidence of a large
average shift** for this one contrast; smaller or heterogeneous effects
remain possible. The intervals are descriptive, not randomization-based
causal intervals, and reference presence is different from the
high/low-companion treatment proposed for new judgments.

The WMT25 English to Chinese extractor was preflighted against the
public JSONL: 51 documents had all eight distinct system outputs.
It selected 40 documents, one segment each. The committed
[manifest](results_reference/candidate_manifest.json) records
provenance and the exact item-ID digest. **No new human judgments
exist yet.** The prospective pilot needs bilingual raters and a
controlled annotation interface.

ICML novelty remains unestablished. Prior work covers active MT
comparison, evaluation task composition and anytime-valid off-policy
inference. If a controlled effect replicates, compare a panel-aware
design against existing methods on reliable conclusions per
measured human minute.
