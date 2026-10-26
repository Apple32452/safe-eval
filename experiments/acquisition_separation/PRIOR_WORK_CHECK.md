# Post-result check against published EC-squared acquisition

Declared 2026-10-26 after the frozen 48-problem acquisition-class calculation
and its exact audit, before computing this additional control. The original
study and its strict-separation decision remain unchanged. This is not
independent validation.

Golovin, Krause and Ray, *Near-Optimal Bayesian Active Learning with Noisy
Observations* (NeurIPS 2010), Section 3, already formulates equivalence-class
determination and develops EC2 (equivalence class edge cutting):
https://papers.nips.cc/paper_files/paper/2010/file/1e6e0a04d20f50967c64dac2d639a577-Paper.pdf

Our zero-error finite problem maps directly to that framework: hypotheses
are the 64 complete score matrices; tests purchase individual cells; two
hypotheses belong to the same class if their requested sign vectors agree.
All cell tests have unit cost. Thus the general idea of choosing individual
cells to identify a comparison class is not a new problem formulation.

For the current compatible set V, define the remaining cross-class weight
`W(V)=sum_{h<h' in V, g(h)!=g(h')} pi(h)*pi(h')` using the original prior.
EC2 chooses the unseen cell maximizing
`W(V)-sum_y P(y|V)*W(V_y)`. Break exact ties by the smallest row-major cell
index. Use exact rational arithmetic. Do not substitute posterior-normalized
edge weights or the paper's approximate EffECXtive criterion.

Run the same four priors and both graphs. At alpha=0, use EC2's exact logical
stopping rule and compare with the zero-error optimal cell policy. At
alpha=1/20, keep the EC2 acquisition choice fixed at every history but allow
the same linear program to optimize all stopping and report randomization
subject to the per-matrix error bound. This second method is an explicitly
labeled **EC2 acquisition plus optimal valid stopping** control, not an
unmodified reproduction of the published algorithm.

This produces 16 additional problems. Retain the existing priors, costs,
target comparisons and certificate construction. Verify the EC2 selection
against direct pair-of-hypotheses edge enumeration; then independently replay
all 64 fixed matrices and check exact cost bounds. Report all results.

Even an improvement over this greedy acquisition does not make an exhaustive
optimal decision process a novel scalable algorithm. The comparison identifies
the remaining gap to a concrete published acquisition rule.
