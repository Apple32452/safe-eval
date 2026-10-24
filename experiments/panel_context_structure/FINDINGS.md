# Panel-context structural diagnostic

Date: 2026-10-24. The [proof](THEOREM.md) identifies exactly when an
adaptive five-way-panel distribution preserves every requested pair's
uniform-companion mean if all included outcomes are reused **unweighted**.
For a complete graph and all five-way panels, it forces uniform panel
selection whenever effects may depend arbitrarily on panel composition.

The [frozen protocol](PROTOCOL.md) was committed to `main` as `a7db90b`
before coding the enumerator. The software checks all **63** nonempty
comparison graphs on four systems with three-way panels and **3,807**
positive integer-weight states, with no disagreement between direct
conditional-probability equality and the graph-component criterion.
There are **207** compatible weighted states. Four tests pass. The count
checks a finite set of tiny instances; the proof covers general finite
graphs under its stated assumptions.

In a complete seven-system, five-way example there are 21 panels and
one component, forcing one uniform distribution. A two-edge sparse
six-system example has two components, permitting mass to shift between
them. An explicit six-system context-effect witness yields a target
pair mean of **0.25** and an adaptive raw mean of **0.40**; raw reuse
changes the estimand by **0.15** in that constructed setting.

This matters for the research goal: the Stage 31 simulated 32.96% panel
task saving relies on context-independent pair outcomes. The structural
diagnostic explains why a context-sensitive target cannot retain all ten
raw pair updates under arbitrary adaptive panel selection. The next
candidate must correct or selectively use byproduct comparisons, while
preserving useful judgments per **human minute**. Simple correction via
propensity weights is established methodology, and no such candidate has
yet beaten strong controls on human data. **No ICML novelty claim is made.**

No WMT24 results or new human responses were used. Reproduce:

```bash
python -m unittest discover -s experiments/panel_context_structure \
  -p 'test_*.py' -v
python experiments/panel_context_structure/audit.py
```
