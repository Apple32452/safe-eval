# Stage 21 technical amendment 1

The one-repeat simulation completed, but the reporter failed at Python parse
time before reading or comparing its saved rows. Two generator sums on one line
were missing parentheses around their division.

Before the smoke result was summarized and before any 50-repeat run, the line
was expanded into explicit parenthesized sums. No data, method, pilot, selected
edge, threshold, seed, checkpoint, closure rule, or gate changed. A compile
check over every Stage 21 Python file was added to the pre-run verification, and
the corrected reporter and implementation lock were committed before continuing.
