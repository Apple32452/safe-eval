# Bounded-score theoretical extension (not an implemented solver)

The executed study is binary-only. The following implicit construction shows that the statistical feasibility is not restricted to binary scores. It does not provide a scalable or numerically certified continuous implementation and is not presented as a novel theorem.

Let fixed X_vi lie in [0,1]. At each cell time, select a system predictably and then select an unobserved item uniformly within that system using fresh randomization. For a null vector theta, let system v have n_v observed scores with sum S_v and set

    c_v(theta)=(N theta_v-S_v)/(N-n_v).

Restrict theta to the deterministic feasible box S_v/N <= theta_v <= (S_v+N-n_v)/N. For the selected system, c_v is its conditional null mean. Choose a_v as the previously observed mean, or c_v before its first observation. Update only that system's process with

    f_v(theta)=1+(a_v-c_v(theta))*(Y-c_v(theta))/(13/50).

For all a_v,c_v,Y in [0,1], f_v>=1/26. At the true mean vector, E[f_v|past, selected system]=1 by uniform sampling of the remaining fixed entries. Hence each paused coordinate capital is a nonnegative martingale in the full acquisition filtration. Because only one capital changes per acquisition, their product is also a nonnegative martingale, as is their arithmetic mean and any fixed convex mixture of the product and mean.

Invert the fixed equal hedge at threshold 20, intersect over all earlier cell times and with the feasible box. This gives a 95% anytime-valid joint confidence set in [0,1]^m. Projecting it onto all requested differences controls the probability of any wrong reported sign at any time by 0.05. Empty sets do not authorize arbitrary declarations. Once both endpoints are completely observed, their full-pool sign is deterministic. The guarantee holds under arbitrary score correlation and adaptive system choice, but not uncorrected outcome-adaptive item probabilities.

With rational scores and constants, all factors are polynomials in the mean coordinates after clearing positive denominators. Exact quantifier elimination could in principle decide the necessary sign projections on the finite sequence of semialgebraic sets. This is a computability observation, not a tractable algorithm or an implementation guarantee. Using an approximate grid as if exact is not justified. Arbitrary real-valued input representations would require additional numerical assumptions.

This extension uses the published PEAK scalar betting form and standard finite-pool conditional centering and joint martingale aggregation. It supplies no new efficiency guarantee. The only strict cost separation proved in this study remains the restricted extreme-star comparison, which existing joint controls can also attain. The missing research result is a tractable, correlation-exploiting partial-cell certificate with an advantage beyond these known combinations.
