# Stage 8 research record

The parent repository commit is a4cd0b0f19c99be23cbbe47cf3aa71788aad7ef9.
All 58 parent files were reconciled to their GitHub blob hashes after restoring
the local workspace. All 49 files of the released Stage 7 snapshot are unchanged.

The primary contrast, methods, data, seeds, precision and reporting quantities
were specified before the full comparison. Seven new statistical tests passed,
including exact original-branch compatibility and full small-pool enumeration.
The one-repeat, 117-case software run and its independent audit passed before
the 100-repeat run. Protocol and implementation hashes were published in
GitHub commit **5253c2548772529dadea2e33f2abc0862eaa368d** before that full run.

The full run completed 117 cases and 70,200 trajectories. Its first full audit
passed without changing the frozen engine, cases, rules, code hashes or audit.
Results were not used to retune the reserve weight or any predictor setting.

The auxiliary report_details.py was added during the full run to implement the
prespecified worst-path reporting from audited rows. It is a read-only reporting
addition outside the original frozen inference/audit files. It does not change
decisions, intervals, data, costs or the frozen analyzer. Its means are checked
against the audited comparison tables. Its source hash is in MANIFEST_SHA256.json.

The software-check and full scientific figures were inspected visually. There
was no need to revise the frozen plot generator. Compact reference outputs and
logs are committed; full decisions and curves remain regenerable local outputs.
Do not run the analyzer on the trimmed results_reference directory.
