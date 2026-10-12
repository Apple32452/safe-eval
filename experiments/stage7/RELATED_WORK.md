# Focused audit of the Stage 6 claim boundary

This is a focused primary-source check performed before interpreting Stage 6,
not an exhaustive novelty review. No paper below has been reproduced as its
original experimental pipeline. Only the published binary PPR control is
implemented directly. Random extra queries isolate our acquisition mechanism;
they do not replace the stronger published-method comparisons an ICML paper
would require.

| Primary work | Relevant existing result | Implication for this project |
| --- | --- | --- |
| [Waudby-Smith and Ramdas, finite-population CS](https://arxiv.org/abs/2006.04347) | A prior/posterior-ratio construction gives confidence sequences for sampling without replacement. | Our raw inference is an existing method. Preserving its stream is the core requirement. |
| [Kossen et al., Active Testing, ICML 2021](https://proceedings.mlr.press/v139/kossen21a.html) | Select test labels for efficient evaluation, with estimators correcting selection bias. | Active model evaluation and its acquisition motivation are established. Our guard does not establish superiority to LURE. |
| [Zrnic and Candes, Active Statistical Inference, ICML 2024](https://proceedings.mlr.press/v235/zrnic24a.html) | Predictions guide label acquisition for efficient valid statistical inference. | Combining predictions, acquisition and inference is not itself novel. |
| [Csillag et al., Prediction-Powered E-Values, ICML 2025](https://arxiv.org/html/2502.04294v2) | Predictable predictions and collection policies can preserve e-value, supermartingale and e-process guarantees. | Generic prediction-assisted anytime validity is already available; a distinct operational efficiency result is needed. |
| [Robust Sampling for Active Statistical Inference](https://arxiv.org/html/2511.08991v1) | A robust sampling interpolation targets variance protection when predictions are inaccurate. | Bad-transfer protection overlaps in motivation; its asymptotic variance comparison is different from our finite pathwise query-cost cap. |
| [Doane, protein design model comparison, preprint October 6, 2026](https://doi.org/10.21203/rs.3.rs-11098459/v1) | Exact known-hit and unknown-mass bounds remain valid under adaptive query order and shared measurements. Its Guarded-SeqVOI controller does not have a label-cost bound relative to greedy. | Deterministic known-label bounds and caching ideas are not new. The biological decision setting differs, but it narrows the novelty claim further. |

The precise proposed combination is a retained ordinary raw 95% stream,
additional deterministic information and an explicit allowance on unique paid
labels. We have not established that this combination is unpublished. The
budget argument is simple and should not be sold as a new general confidence
sequence theorem. Stage 6 tests whether this particular mechanism is useful.

A publisher search also identified *Exact Finite-Population Sequential
Auditing for Selective Release from Model-Proposed Candidate Sets* (Hu et al.,
Mathematics 2026, [publisher](https://www.mdpi.com/2227-7390/14/18/3427)). The
full publisher text was inaccessible during this audit, so no theorem or
specific overlap is inferred from that title/search result. It remains an
item to read before making a novelty claim.

Public data are the pinned [Google WMT MQM human-evaluation
release](https://github.com/google/wmt-mqm-human-evaluation). The TSVs, source
hashes, conservative quality-control exclusions and finite estimand are
documented separately in `data/DATA_PROVENANCE.json`.
