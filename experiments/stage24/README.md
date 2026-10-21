# Stage 24: joint finite-pool inference feasibility

Independent branch `research/stage24-joint-finite-pool`, based on the final Stage 23 boundary. Existing stages and local main are unchanged; no WMT data is loaded.

Read RELATED_WORK.md for source-level overlap and THEORY.md for the guarantee and its limits. PROTOCOL.md was fixed before results. The implemented candidate is a proof-of-validity pilot, not a new universal-portfolio algorithm or a continuous-score method.

From repository root:

    python -m unittest discover -s experiments/stage24 -p test_joint.py -v
    python experiments/stage24/run_small.py
    python experiments/stage24/report.py

Run the experiment in a fresh clone/empty results_reference to regenerate fixtures and the source lock. If results_reference is already present, the same sources, fixtures and previous-stage hashes must match. The program refuses changed sources. No WMT command, download, push, or previous-stage mutation is part of this procedure.

Results: results_reference/FINDINGS.md, per_cell.csv, paired_per_cell.csv, per_family.csv, overall.csv, costs.png/svg and verification records. All numeric settings/seeds are in PROTOCOL.md and results_reference/LOCK.json. Uniform methods share paths and within-item system order; adaptive paths differ by design and use the same uniforms as a coupling. History duplicates are not independent data. The unchanged Stage 22 scheduler asserts final decisions are correct; any violated assertion aborts rather than silently excluding the run.
