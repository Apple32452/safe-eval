# Using the Stage 9 reference files

The compact results_reference folder contains the completed comparison tables,
runtime metadata, query-stream hashes, worst-path summaries, figure and audit
record. It omits the large per-trial decision table and full query/capital
curves. It cannot be passed directly to analyze_stage9.py. Reproduce a full run
in a new output directory using the commands in README.md to obtain those files
and replay every decision locally.

The certificates_reference folder contains exact integer path counts, exact
risk fractions and the raw/calibrated state tables used by the reference run.
Each JSON certificate records the gate-table checksum and generating runtime.
The counts concern every possible total K, not merely the observed benchmark
targets. They certify the actual floating gates on that runtime; they are not
Monte Carlo estimates or formal verification of NumPy/hardware.

Generate fresh certificates for a reproduction on another runtime. The runner
checks every raw and calibrated gate before starting. A different gate table
must be recertified rather than silently reusing a reference error allowance.

MANIFEST_SHA256.json records the byte hashes of the Stage 9 files other than
the manifest itself. The frozen PROTOCOL_LOCK.json separately records the
eleven implementation/protocol files committed before the fixed comparison.
Read FINDINGS.md for the result and the scope of the guarantee.
