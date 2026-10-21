# Stage 22 related-work boundary

This record limits the Stage 22 claim before implementation.

- Kossen et al., *Active Testing: Sample-Efficient Model Evaluation* (ICML
  2021), actively selects test points and uses importance weighting for
  sample-efficient risk estimation. This blocks a broad active-evaluation
  claim. Stage 22 instead studies exact finite-pool pair conclusions, shared
  system-item costs, and pathwise removal of vertices from a requested
  comparison graph.
  https://proceedings.mlr.press/v139/kossen21a.html
- Karimi et al., *Online Active Model Selection for Pre-trained Classifiers*
  (AISTATS 2021), studies online selection of the best classifier. This blocks
  a broad best-model-identification claim.
  https://proceedings.mlr.press/v130/reza-karimi21a.html
- Arviv et al., *Stop Guessing When to Stop Testing: Efficient Model
  Evaluation with Just Enough Data* (Findings of ACL 2026), covers sequential
  stopping for evaluation, pairwise comparison, ranking, and selection and
  reports large compute reductions. This blocks novelty claims based merely on
  adaptive stopping or reduced test size.
  https://aclanthology.org/2026.findings-acl.43/
- Arnold et al., *Sequential Model Confidence Sets* (JRSS B, 2026), provides
  time-uniform nonasymptotic multi-model inference through e-processes and
  confidence sequences. This blocks a broad sequential ranking/confidence-set
  claim.
  https://doi.org/10.1093/jrsssb/qkag066

The unresolved narrow question is whether a requested sparse comparison graph,
shared per-system-per-item annotation costs, exact without-replacement
finite-pool inference, and pathwise edge-resolution dominance form a useful
joint contribution. Stage 22 can establish empirical materiality only. It
cannot by itself establish novelty, because a complete definition- and
algorithm-level comparison with model-racing, multiple-comparisons-with-control,
and best-arm-identification work is still required.
