# Complexity and validity-preserving improvement analysis (not implemented)

Let S be systems, N pool items, P requested unordered pairs, K=6 betting
components, L purchased labels, and Q the number of consumed pair-prefix
observations before each pair's permanent resolution (Q<=PN).

## Existing code

continuous_engine.directional_paths performs Theta(PNK) arithmetic for one
replicate, including resolved pairs and unused future observations. Its current
mathematical state is O(PK), but returned events/evidence use Theta(PN) memory.
make_paths repeats the permutation per pair, sorts every row to validate it
(O(PN log N)), and constructs dense pair differences/gather temporaries.
Storage is Theta(SN+PN+PK). Constant-factor peak memory includes several dense
arrays and is not just the size of the final state.

Stage22 does not recompute statistical wealth while replaying. close_free scans
decision for all unresolved pair IDs, then checks the next prefix item. It is
called once per acquired cell even when few pairs can change. The expression
decision==2 also allocates/evaluates P booleans for each np.any stopping check.
Before/after decision copying and resolution-cost bookkeeping scan P again.
Thus at least Theta(LP) work is imposed by these full scans, including dense
Theta(S^3 N) scaling when L=Theta(SN), P=Theta(S^2). This is a worst-case
structural bound, not an exponent fit to timings. Repeated close_free iterations
can add work. Snapshots additionally gather pair endpoint scores: O(PN) per
fixed checkpoint. Selection sorts active systems per block: at most O(NS log S).

The benchmark measures fixed-null sign e-processes and crossings, not full CS
interval inversion, arbitrary weak-order closure, or all existing SAFE-EVAL
predictor/training costs. Exact DP, grid inversion and joint-order methods have
different complexity and supported dimensions; they are not silently scaled here.

## Proposition 1: global completion checks need not scan all pairs

Assume each pair starts unresolved, resolves at most once, and never reopens,
as in simulate_graph. Maintain U initially P, decrementing it once for each
first resolution. Then after every closure U equals count(decision==2).

Proof: true initially; each unresolved-to-resolved assignment changes both sides
by one, and no other assignment changes either side. Induction proves equality.
Replacing every global unresolved predicate by U>0 preserves every branch.
The counter costs O(P+L) total over initialization, first resolutions and L
checks, instead of Theta(LP). No label order, stake, threshold, first decision,
or label cost changes. Resolution IDs are available at the existing update;
computing a new full-array difference merely to update U would defeat the bound.

This proposition removes only the global-check cost. It is not a bound on the
whole implementation while availability scans and bookkeeping scans remain.
It is elementary incremental bookkeeping, not a novel CS result.

## Proposition 2: prefix closure admits output-sensitive dependency processing

Assume fixed edge prefixes, independent edge event streams, absorbing first
decisions, and acquisition only after close_free reaches a fixed point.
Each unresolved edge waits for its two current endpoint cells. A reverse
dependency index can register that edge at its missing cells; a purchase wakes
only the dependent edges. On completing one prefix event, advance that edge or
resolve it, and register its next missing cells. Already seen cells can be
consumed immediately until the edge is blocked or resolved.

Invariant: for every unresolved edge its cursor is the largest prefix whose
endpoint labels have been seen, truncated at its first resolution. Each edge
advances monotonically; its decision depends only on its own fixed event stream.
Consequently the terminal cursor/decision vector is unique and independent of
the order in which ready edges are processed. The indexed procedure and the
original exhaustive closure reach this same vector after every label. Induction
over purchases then preserves active systems, original priority-based choices,
the entire acquisition ledger, resolution costs, and stopping labels.

Each prefix can create/consume at most two missing-cell registrations. With
array-indexed cells and lists with O(1) amortized operations, initialization,
dependency and closure work is O(P+L+Q), storage O(P+SN), excluding retained event
paths, diagnostics and selection sorting. If computing the original betting
update on demand, arithmetic adds O(KQ). Holding original per-block selection
work fixed gives O(P+L+KQ+NS log S) for this specific streaming evaluation
design, apart from input/output/diagnostic work. This is an operation-count
argument, not a benchmark of a new implementation. No queue, index or optimized
runner is implemented in this audit. The idea is ordinary dependency scheduling.

## Proposition 3: full trajectories are not required for stopping

The original recurrence depends on each pair's current directional sums,
K log-capitals, prefix index and the current paired observation. Replaying those
same arithmetic operations in prefix order reproduces every first crossing.
After resolution, no future value of that pair can change its first crossing.
Keeping current state rather than all PN trajectory entries therefore suffices
for the same requested sign decisions and acquisition path under the preceding
invariants. O(SN+PK+P+N) state including the original priority/seen tables suffices,
excluding full output traces; this is a representational possibility, not a
delivered implementation or measured memory saving.

All three arguments are pathwise: statistical evidence and decisions are
unchanged. Their original anytime taskwise family guarantee therefore transfers
without an additional error budget. This does not authorize feeding unseen
labels to a live evaluator or using nonuniform pair prefixes with a uniform-WoR
factor. The proofs cover this Stage22 independent-edge rule, not arbitrary
closed-testing algorithms that share running wealth across hypotheses.

## What cannot be concluded

An API returning every pair's event and evidence at every item has Omega(PN)
output size; storing those outputs in RAM cannot have sub-PN space. Explicitly
reporting P statuses has Omega(P) output cost per report. Neither fact proves a
general Omega(P) inference cost per item for compressed/implicit algorithms.
Eagerly updating PK separate numeric states costs that many writes, but that is
an implementation-model bound, not an information-theoretic lower bound.

Skipping unresolved updates, reducing look frequency, sparsifying requested
pairs, changing wealth mixtures or switching to per-system CSs may preserve
some validity guarantee but can delay decisions or change labels. They do not
satisfy a claim of unchanged annotation efficiency without a separate proof.
In particular Var(A-B)=Var(A)+Var(B)-2Cov(A,B): arm-only bounds can lose shared-item
correlation information. This identity is not a universal stopping-cost theorem.

These restricted improvements are meaningful engineering opportunities. They
do not establish a new theoretical research contribution or measured speedup.
The equivalence arguments are for exact recurrences and faithfully reproduced
arithmetic. Any future floating-point implementation still needs parity and
rounding/feasibility checks before claiming production equivalence.
