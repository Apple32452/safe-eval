# Stage 22: graph-aware safe evaluation

Stage 22 is a precommitted WMT25 development test of the Stage 20 pruning
theorem on sparse requested-comparison graphs. The primary task compares every
candidate system with one reference system and averages over every possible
reference. The strong control evaluates all systems on the same common item
stream; the candidate skips a system only after all of its requested incident
edges have resolved.

The protocol and related-work boundary were committed before implementation or
Stage 22 outcome computation. WMT24 remains untouched.

Implementation and reproduction commands will be added only after the
implementation is frozen.
