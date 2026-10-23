# Predictable partial-block allocation screen (locked before fresh results)

Hypothesis: a one-step expected log evidence per expected purchased score
criterion can choose the partial-block purchase probability to improve total
stopping cost while retaining exact conditional fixed-pool validity.

Use the Stage 35 two-system binary certificate and 32 fixed items. At each
history, choose q from {.25, .5, .75, 1}. For each candidate, construct its
positive-direction exact factor from the pre-target predictive alternative.
Choose q with the largest predicted positive expected log increment divided
by expected purchased judgments. Ties favor larger q. This rule reads only
past purchased values, predictions, and the current cache. After q is chosen,
compute the negative-direction factor under its predictable sign-flipped
alternative and purchase according to the chosen design. Preserve two-sided
threshold 2/.05, exact logical bounds, and unique-cell accounting. Selection
itself can depend on prior outcomes; neither it nor a current factor sees
the current unpurchased score.

Fresh seed `20261025 + rep + 100*len(scenario)`, twelve independent fixed
matrices in each of the aligned strong (.90/.10), aligned moderate
(.70/.30), and shifted opposite-sign (.30/.70 target with .90/.10 predictor)
scenarios. Compare the adaptive method with exact full blocks (q=1) and
fixed partial blocks (q=.5), and price Stage 22 on the exact full-block
item order. The aligned predictions are intentionally oracle-like generating
rates and were not fitted on target outcomes. They are not a realistic
historical-transfer claim.

Primary gate: at least 10% lower mean purchased-score cost than **both**
matched exact full blocks and fixed q=.5 in **both** aligned scenarios;
no more than 10% regression versus full blocks in the shifted scenario;
no wrong completed signs or null-constraint failures. The 12-repeat screen
is exploratory; even a pass would require independent validation with
real historical predictors and an actual shared comparison graph. Do not
run WMT25 on a failed gate. WMT24 remains reserved.
