# Scope of the shared dual objective

For a current set of eligible cells C and active comparison edges E, let
a_{e,c}=1{c is an endpoint of e}*p_c*(1-p_c). We use the model's Bernoulli
variance as a predictable proxy for the unknown residual second moment.
Consider the convex program

    min_{q_c>=0, sum_c q_c=1} max_{e in E} sum_{c in C} a_{e,c}/q_c.

For a probability vector lambda on E, the inner weighted objective is
sum_c [sum_e lambda_e*a_{e,c}]/q_c. By Cauchy-Schwarz its minimum is

    G(lambda) = [sum_c sqrt(sum_e lambda_e*a_{e,c})]²,

with q_c proportional to the square root. Convex duality (or minimax on
the positive interior, followed by a limit for zero weights) gives the
program value max_lambda G(lambda). G is concave as an infimum of linear
functions of lambda. With at most two unresolved comparisons, lambda has
one scalar coordinate in [0,1]. The implementation optimizes that scalar,
then applies a 20% uniform floor so that **every active unobserved cell has
positive probability**. The floor means the actual proposal need not solve
the unconstrained program exactly.

For a fixed target matrix, the optimization does not certify a valid
e-process on its own. Validity comes from recomputing the existing exact
conditional null-calibrated factors under the **actual** proposal q at
every step. The variance proxy depends on predictive calibration; if
history is reversed, it can be misleading without affecting validity.

This is not an expected stopping-cost bound. Even if the proxy is exactly
optimized, the acquisition need not be faster than a matched control using
the same stopping factors. Multiple-comparison variance optimization and
active test selection have substantial prior work; originality is not
asserted. The frozen study measures whether any end-to-end gain remains.
