# Numerical feasibility amendment after a software smoke run

Date: 2026-10-24, **before** the frozen 100-repeat diagnostic. The two-repeat
smoke run hit SciPy SLSQP's `Positive directional derivative for linesearch`
status for one cost-heterogeneous matrix even though the returned epigraph
constraint residual was only `-7.3e-9`, its cost-normalization residual was
zero, and its objective improved substantially over both starting proposals.
The original code rejected both returned solutions based on the optimizer
status string and wrote no result directory or research summary. A second
smoke run after the feasibility correction still had a numerically infeasible
result. We therefore divide every edge's epigraph coefficient by the largest
objective of the two starting proposals. This positive common factor changes
neither the feasible panel proposals nor the minimizing proposal. We always
evaluate and report the **unscaled** proxy.

For the full run, accept an output when its maximum constraint violation is
at most `1e-7`, its cost normalization is within `1e-8`, and its evaluated
proposal meets the original positivity floor after a microscopic projection.
Record both the count of feasible starts and SciPy-reported successes. Reject
any matrix for which neither starting point yields a feasible proposal. All
six matrices in the post-rescaling two-repeat smoke run had two feasible starts
each; the smoke results are exploratory and do not alter the frozen rule.

The matrix generator, seed, target, three methods, proxy, 100 repeats,
positivity floor, bootstrap, and headroom decision are unchanged. This
corrects a numerical termination condition, not a scientific result. The
output is a feasible best-found proposal and does not prove that a numerical
solver reached the global minimum, although the epigraph problem is convex.

The protocol's phrase "lower bound on a surrogate allocation objective" refers
only to the **infeasible full-population information advantage** in choosing a
panel proposal. The best-found numerical proxy itself is not a certified
global lower bound, nor a lower bound on actual stopping cost.
