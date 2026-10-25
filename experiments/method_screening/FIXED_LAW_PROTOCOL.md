# Post-result diagnostic: match predictive law, not just prior information

The first two-system screen shows DP full beating the learning paired baseline
in moderate/reversed cases. This is not evidence that DP's conditional null
representation is responsible: DP uses fixed homogeneous probabilities while
paired_update learns a categorical predictive law from purchased differences.

Before running this follow-up, freeze exactly one additional control: reuse the
paired_update solver, null_histograms, constraints and numerical safeguards, but
set its predictive alt to the original fixed prior difference law. This is an
in-memory one-assignment evaluation adapter, not a changed historical file or
optimization of the DP. No stakes, thresholds, bounds or hyperparameters tuned.
Use exactly the same 30 matrices/orders and compare with both full and partial DP.
Timing once per fixture is descriptive; no speedup generalization. This is an
explicit post-result mechanism diagnostic, not independent validation.

Predictability and factor-feasibility proof are unchanged: the optimizer's
alternative may be any fixed probability distribution. Test all 384 tiny binary
paths for accounting and exact signs; rely on the conditional proof for coverage.

For q=1 and homogeneous priors, all remaining items have four common outcome
factors f00,f01,f10,f11. Null completions constrain c10-c01 through the observed
difference. For any number of zero differences, all can be assigned to whichever
of 00/11 has larger factor, without violating any other remaining-total condition.
Thus the worst-null constraint depends on the zero factors only through their
maximum. Replacing both zero factors by this maximum preserves feasibility and
weakly improves predicted log growth. The full exact problem therefore admits a
three-difference-event optimum, using predictive probabilities
((1-pa)*pb, pa*pb+(1-pa)*(1-pb), pa*(1-pb)). This is a restricted representation
argument, not a theorem for partial caches, heterogeneous item predictions or
multiple systems. It does not establish bitwise equality between numerical solvers.

Directional-law correction before the final diagnostic: sequential_probe uses
Design(pa,pb) for the positive factor and Design(1-pa,1-pb) for the negative
factor, not a single shared alternative. For the negative B-A difference this
requires paired priors (1-pb,1-pa). The initial fixed-law diagnostic used (pb,pa)
and therefore was not matched in the negative direction. Preserve it as
fixed_law_initial_direction_mismatch.json, excluded from the final comparison.
The corrected adapter changes only those two predictive-law assignments;
all constraints, solvers and statistical guarantees remain unchanged.
