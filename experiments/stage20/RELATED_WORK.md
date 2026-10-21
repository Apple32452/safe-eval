# Stage 20 closest-work boundary

- Kossen et al., *Active Testing: Sample-Efficient Model Evaluation* (ICML
  2021), actively chooses test points and uses importance weighting for
  unbiased risk estimation. It does not study shared system-item label costs or
  pathwise pruning dominance for a family of fixed-benchmark pair conclusions.
- Arviv et al., *Stop Guessing When to Stop Testing: Efficient Model Evaluation
  with Just Enough Data* (arXiv 2026), covers adaptive stopping for model
  scoring, pairwise comparisons, ranking, and selection. It uses group
  sequential tests and explicitly simplifies the multiple-comparison issue.
- Arnold et al., *Sequential Model Confidence Sets* (JRSS B, 2026), gives
  time-uniform nonasymptotic multi-model inference through e-processes and
  confidence sequences.

These papers block broad claims about sequential or sample-efficient model
evaluation. The Stage 20 candidate is limited to finite fixed pools, exact
family control, shared per-system-per-item costs, and pathwise safe removal of
labels that cannot advance an unresolved edge. A later paper must compare
definitions and algorithms directly rather than rely on this short boundary.
