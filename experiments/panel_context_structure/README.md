# Panel context and shared judgments

This folder records a graph characterization for when adaptively chosen
multi-system panels may share **unweighted** pair judgments without
altering uniform-companion pair targets under arbitrary context effects.

Read the [proof and scope](THEOREM.md), [protocol](PROTOCOL.md), and
[audited result](FINDINGS.md). `audit.py` enumerates small graphs and
constructs a biased context witness; `test_audit.py` checks the boundary
cases. It is a structural diagnostic, not an ICML paper result.
