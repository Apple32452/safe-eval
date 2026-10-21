# Stage 19 validity and design rationale

For a fixed system pair, the shared core is the first `k` positions of a
uniform random item permutation. Conditional on that prefix, a uniform random
permutation of the remaining items completes a marginally uniform permutation
of the full finite population. The Stage 17 e-process is therefore anytime
valid along every precommitted hybrid path.

The global adaptive scheduler can select which pair prefix to advance using all
previously revealed shared labels. A wrong scheduled declaration for a pair is
pathwise contained in the event that its complete precommitted path ever crosses
the wrong boundary. The per-pair bound and union bound continue to control the
family event without assuming independence between pair paths.

The core exploits dense reuse: one completely scored item advances all system
pairs. After the core, many easy comparisons may already be resolved. The tail
then avoids spending every new item on every system and targets only labels that
advance unresolved pair frontiers. Stage 19 tests whether this division can
strictly improve the number of valid conclusions at a fixed unique-label budget.
