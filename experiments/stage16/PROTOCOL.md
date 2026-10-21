# Stage 16 pre-outcome protocol: WMT25 external validation

## Purpose

Test the unchanged Stage 15 `frontier_evidence` acquisition rule on a newer
public human-evaluation benchmark before inspecting its complete outcomes.
The development result was mixed: +0.82 certified pairs at 50% of unique
labels and +10.80 at 75% on WMT23. This external test is therefore necessary
before treating the scheduler as a credible method candidate.

The WMT25 README and evaluation scripts were inspected only to determine the
JSONL schema. The complete 128,674,273-byte human-evaluation JSONL has not
been downloaded or summarized before this protocol. Its Git LFS object is
`sha256:a36ebce10c9ea26f71449933721de3a87e27f6a5b09d96b5daa026eaf1d197ab`
at upstream commit `2fc0874d85278d8c7e0807951e54d8422e7957e4`.

## Frozen parsing rule

Source repository:
`https://github.com/wmt-conference/wmt25-general-mt`, file
`data/wmt25-genmt-humeval.jsonl`.

Each nonempty line must be valid JSON with string `doc_id` and a nonempty
`scores` mapping. The language key is the part of `doc_id` before the first
`_#_`. Duplicate `(language, doc_id)` lines fail. Exclude system names whose
case-folded, punctuation-stripped name begins with `ref` or `human`.

Within each language:

1. Count the number of distinct items with at least one annotation list for
   each remaining system.
2. Retain every system attaining the maximum coverage count. This uses
   annotation availability only, not scores or errors.
3. Retain the exact intersection of items annotated for every retained system;
   do not impute missing annotations.
4. Include the language only when at least three systems and 30 common items
   remain. Report every excluded language and the reason.

For a retained system-item, require a nonempty list of annotation dictionaries.
Every annotation must contain a finite numeric score in [0,100] and an `errors`
list. Every listed error must be a dictionary whose severity case-folds to
`minor` or `major`. Define the strict binary consensus outcome as one iff
**every** retained annotation has score exactly 100 and has an empty error
list. Otherwise it is zero. This outcome is frozen for comparability with the
earlier binary error-free work. It is not the official continuous WMT25 human
score or a practical MQM margin.

## Inference and acquisition

- Form all unordered pairs of retained systems within each included language.
- For each pair and repeat, precommit an independent uniform permutation of
  its common item pool using NumPy PCG64 and SHA256-derived seeds.
- Use 50 repeat blocks and master seed 20261023.
- Use categorical finite-population PPR evidence and the deterministic sign
  certificate exactly as in Stage 15, generalized only so the evidence ceiling
  and pool size are not tied to WMT23 constants.
- For a language with K pairs, use directional threshold `40*K`, giving
  nominal 95% family control separately within that language and policy.
- A unique `(system,item)` outcome costs one label and is reusable across all
  pairs in that language. After each paid label, close every available pair
  prefix exactly as in Stage 15.
- Checkpoints are floor(25%,50%,75%) of all retained unique system-item labels.

Three fixed policies:

1. `focus_random`: finish pairs in a precommitted outcome-independent random
   order.
2. `evidence_first`: choose the unresolved pair with greatest current maximum
   directional PPR evidence, then its first missing frontier label.
3. `frontier_evidence`: among unseen labels required by current unresolved
   pair frontiers, choose the label maximizing

       sum_p [Q + min(E_p, 40*K*Q)], Q=2^20,

   with the unchanged outcome-independent random unique-label tie priority.

No prediction model, coefficient, practical margin, pair filtering, or policy
change is allowed after parsing the outcome file.

## Primary external-validation claim and gate

The primary budget is 75%, selected because Stage 15 showed its clear
development signal there. Sum the number of correctly certified pairs across
all included languages within each repeat, and compare
`frontier_evidence - evidence_first`. Report the mean, conditional Monte Carlo
standard error, all 50 differences, wins/ties/losses, and per-language means.

The external gate requires:

- positive mean primary difference overall;
- positive mean difference in a strict majority of included languages; and
- no observed excess in wrong declarations for `frontier_evidence`.

The 25% and 50% checkpoints are secondary and all losses remain reported.
Passing this gate supports generalization of the scheduling effect. It still
does not establish ICML novelty because the target is a strict binary proxy
and the needed allocation theorem and matched active-ranking baselines remain
unfinished. Failure rejects external support for this frozen candidate.
