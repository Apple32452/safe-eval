# Necessary two-system strong-control and sampling-path supplement

Written before supplemental outcomes. The archived sequential_probe.run joins
its stopped q=1 prefix to remaining items in index order. Uniform WoR inference
does not automatically apply after that join. Preserve archive values; do not
use the old Stage 22 column as a verified uniform-path comparator.

Regenerate all 30 existing N=32 matrices from their published seeds. Reuse exact
full/partial costs and paths from the archive; verify scores' truth gaps and the
entire q=1 prefix against an independently generated full random acquisition
path. At q=1, each step chooses uniformly from eligible items then consumes one
rng.random draw for the certain second purchase. Precompute that full path from
seed 97531+repeat, independently of labels, and use it for both Stage 22 and an
evaluation adapter of the existing controls.paired_update, two directions,
alpha=.05 (directional threshold 40), exact remaining-difference bounds.

The adapter is a strong baseline, not an acceleration proposal. It reuses the
existing optimizer, histogram constraints, predictive counts and safeguards.
Both endpoints are purchased before updating at every chosen item. Uniform-path
and predictability requirements ensure each original exact factor remains a
supermartingale under its directional null. Ville plus union bound gives 95%
anytime correctness of the two requested signs; deterministic remaining-total
decisions are exact. Arbitrary dependence between endpoints is allowed.

Keep priors, fixed matrices, objective (full-pool mean-difference sign), alpha,
and unique-cell cost matched. The paired baseline learns categorical differences
using only previous purchases, as in its existing implementation; the sequential
DP uses its existing fixed predictive probabilities. This is a stronger permitted
baseline, not a claim of an isolated factor-only ablation. Partial q=.5 uses its
original adaptive cell path and same RNG seed, not the full-block acquisition rule.

No new matrices or tuning. Compare each of strong/moderate/reversed scenarios
separately with paired descriptive bootstrap intervals (seed 48173, 10000 draws).
New paired/Stage22 runtime is one pass per archived fixture (screening, not a
fresh three-repeat CPU benchmark). Use the prior frozen profiling study only
to describe the DP's costs, never as matched timing on these different matrices.
Additionally replay q=1 and q=.5 once on repeat=0 in each of the three scenarios
to check saved costs/paths and obtain same-fixture screening timing (six replays).
Exhaustively check the adapter's truth/unique purchases on all 64 binary 2x3
matrices and all six permutations; this supports accounting, not a coverage proof.
