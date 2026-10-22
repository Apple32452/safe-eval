# Sequential exact-factor development screen (pre-results)

This is a small, two-system development screen before attempting a shared
comparison graph. The binary target pool has 32 fixed items. Use ten fixed
replicates for each of three scenarios: aligned strong (.90/.10), aligned
moderate (.70/.30), and shifted opposite-sign (.30/.70 target with .90/.10
predictor). The negative-direction optimization uses a deliberately
sign-flipped `.10/.90` alternative; it is misspecified in the shifted case.
Scores are drawn once per replicate, then fixed for all randomized methods.
Predictive probabilities are supplied before seeing target scores; the
experiment does **not** train them on this simulated target.

Methods: exact conditional factors for full blocks (q=1), partial blocks
with q=.75 and q=.5, and the frozen Stage 22 single-edge PPR control on the
full-block item's order. Every method must use two-sided threshold
`2/.05=40`, exact logical bounds, and charge distinct purchased cells. Each
factor is optimized at each predictable history subject to worst-case
conditional expectation no greater than one over every compatible fixed
binary null. The exact null separation is a dynamic program over the full
pool total difference. The optimizer must check its own worst-case factor
before each purchase, and fail closed if numerical feasibility is uncertain.

Report all mean label costs, exact signed correctness, optimization fallbacks,
and comparison to full blocks and Stage 22. The *go/no-go gate* for expansion
to multiple systems is at least 10% fewer purchased labels than both full
blocks and Stage 22 in **both** aligned scenarios, with no more than 10%
regression against full blocks under reversed prediction. Ten repeats are
only a software and signal screen; passing would not yet justify a claim.
WMT25 and WMT24 remain untouched.
