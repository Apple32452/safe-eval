# Pre-outcome variance correction

The Stage 34 protocol was first committed as `17d7c251` on 2026-10-24,
before any new human judgments. It incorrectly used variance upper bound 1
for two independent two-judge groups. Stage 33 assigns two of **four fixed
selected judges** per group without replacement. Under the sharp null and
fixed outcomes `Y_1,...,Y_4 in [-1,1]`, the randomization variance of the
P1-minus-P0 mean contrast is the four-judge finite-population sample
variance `S^2=(1/3)*sum_j (Y_j-mean(Y))^2`, whose maximum is `4/3`.
The maximum occurs at two outcomes -1 and two outcomes +1.

For fixed treatment-specific potential outcomes the Neyman variance is
`S_1^2/2 + S_0^2/2 - S_tau^2/4 <= 4/3`. The planning calculation is
updated to use `4/3`; the exact randomization test, outcome definition,
allocation, data boundary, and significance level do not change. This
correction precedes any analysis of human responses and is visible in git
history. The planning numbers remain a normal approximation, not a power
guarantee.
