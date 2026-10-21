# Stage 25: adaptive partial-cell feasibility

Separate branch `research/stage25-adaptive-partial-cells`. No WMT24 or other WMT outcomes are accessed. Previous stages remain unchanged.

Read THEORY.md for the rigorous conditional-coverage argument, the extreme-star separation and its limits; RELATED_WORK.md records why these do not establish novelty. PROTOCOL.md was frozen before the synthetic study. Results and final decision appear in results_reference/ASSESSMENT.md.

From repository root:

    python -m unittest discover -s experiments/stage25 -p test_partial.py -v
    python experiments/stage25/run_small.py
    python experiments/stage25/report.py

All partial-cell confidence decisions use Fraction arithmetic over the complete binary-total grid. Known product/mixture controls and a clearly labeled PEAK-style finite-pool adaptation are used; none is presented as a complete reimplementation of every strongest published Joint-CS algorithm. The Stage 22 comparator imports its original engine/scheduler without edits. Report both sign errors and confidence-set exclusions. Tests support the proof; empirical zero error is not proof.
