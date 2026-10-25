# Additional control audit after the frozen run

2026-10-25. The frozen 20-repeat study and its full integer-null replay audit
have completed. The frozen expansion gate failed. No method, seed, matrix,
or frozen summary is changed by this additional analysis.

The exact pairwise closure in the protocol uses all six directional pairs,
even for the two-edge star. Averaging extra pair wealths can dilute evidence.
Before presenting the candidate's 8.63% strong-star saving against that
control, check two valid stronger alternatives on the same acquisition path:

1. `requested_closure`: for each weak order, average only the directional
   pair wealths whose unordered edge is requested by the current graph.
   This remains an e-process under that weak order. Eliminate at 1/alpha
   and require all surviving weak orders to agree on a strict sign.
2. `requested_bonferroni`: directly test the requested directions at
   2*requested_edges/alpha with the same exact pair factors. When both
   directions cross simultaneously, abstain; retain the exact logical rule.

The second comparator is included because an all-pairs closure need not
dominate a smaller requested-family Bonferroni test. Continue the original
outcome-adaptive cell path if the saved prefix ends before these controls
finish. Every additional cell is charged to the respective late control,
not to a method that already stopped. Verify the shared saved prefix.

Report all five scenarios and both graphs, raw and error-penalized costs,
and paired descriptive bootstrap intervals (10,000 draws, seed 20261026).
This is an explicitly **post-result baseline audit**, not an independent
confirmation or a change to the failed frozen gate. Its purpose is to
detect an overstated gain from a weaker comparator.
