# Stage 26: rater structure and a synthetic partial-label gate

Stage 26 is an exploratory research record, not a new ICML method. It does not
change the Stage 17–25 protocols or results. It does not use WMT24.

## Questions

1. Does the [frozen WMT25 human annotation file](https://github.com/wmt-conference/wmt25-general-mt/tree/2fc0874d85278d8c7e0807951e54d8422e7957e4/data)
   contain enough distinct rater information to motivate modeling annotator
   uncertainty? How much overlap is there across systems and items?
2. Can an elementary use of *partially acquired* scores reduce unique-label
   cost beyond Stage 22's paired-prefix acquisition on fixed finite matrices?

The rater audit only summarizes the 14 Stage 16/17 included languages, their
maximum-coverage systems, and their common item sets. It verifies the upstream
human evaluation JSONL (128,674,273 bytes, SHA256
`a36ebce10c9ea26f71449933721de3a87e27f6a5b09d96b5daa026eaf1d197ab`)
and shared-control JSONL (17,796,659 bytes, SHA256
`bdbf27700af9ec457ae7f81acfd301cd54503b8e5660c6cac5f7c33c9683f9fa`)
before using either. Both raw files are excluded from Git. The committed
summary contains only aggregate counts.

The synthetic experiment holds fixed one binary matrix per scenario (5
systems, 24 items); it uses 100 preseeded uniform item permutations per
scenario and requested graph, with the same permutation, paired evidence,
within-item priority, and familywise error threshold for all methods. It
counts each system-item annotation once. Requested graphs are a star, a ring,
and the complete graph. The generating scenarios have identical rows, close
Bernoulli probabilities, separated Bernoulli probabilities, and anti-correlated
rows; realized fixed-pool differences need not equal generating probabilities.

The three methods are (a) the frozen Stage 22 active-vertex acquisition rule,
(b) dynamically skipping now-inactive vertices inside a committed item, and
(c) the same dynamic rule with sharp deterministic bounds using every acquired
label. An independent copy of the Stage 22 acquisition loop records occasional
valid-procedure errors rather than asserting that every Monte Carlo run must
be correct. A unit test compares it to the frozen implementation on a correct
path. The third method retains **exactly the same** paired evidence path and
threshold for every surviving edge. Its additional declaration uses only the
logical fact that all unobserved scores lie in `[0,1]`.

For a pair `(a,b)`, let `T_a,T_b` be sums of observed scores and `u_a,u_b`
the number of unobserved scores. The complete-pool contrast sum is always in
`[T_a-T_b-u_b, T_a-T_b+u_a]`. A strictly positive lower bound certifies `a>b`;
a strictly negative upper bound certifies `a<b`; a singleton zero certifies a
tie. These bounds hold for every fixed matrix, regardless of acquisition.
The paired e-process error event is unchanged because the item permutation,
per-edge prefix, betting parameters and thresholds are unchanged. Declaring
from the logical bound cannot add a false sign. Thus the original taskwise
familywise guarantee carries over by event inclusion. This argument does not
give a new statistical theorem; similar deterministic completion and
retirement ideas already appear in sequential ranking.

The exact `2^6 × 2^6` small-matrix/mask test verifies the bound for every
binary 2-system, 3-item matrix and exposure mask. It is a software audit,
not a substitute for the event-inclusion argument.

## Results and interpretation

See [FINDINGS.md](FINDINGS.md), [rater audit](results_release/RATER_AUDIT.json),
and [synthetic summary](synthetic_reference/summary.json). The results do not
clear Stage 23's novel joint-acquisition gate. The rater audit is descriptive
and the synthetic comparison includes no new-rater population inference.

## Reproduction

From the repository root, with NumPy installed:

```bash
python -m unittest discover -s experiments/stage26 -p 'test_*.py' -v
python experiments/stage26/run_synthetic_gate.py --output results/stage26_synthetic
python experiments/stage26/audit_raters.py \
  --source external/wmt25/wmt25-genmt-humeval.jsonl \
  --control-source external/wmt25/wmt25-genmt-humeval_control.jsonl \
  --output results/stage26_raters
```

For a new checkout, fetch the two raw files from the pinned official commit:

```bash
mkdir -p external/wmt25
curl -fL --retry 3 -C - -o external/wmt25/wmt25-genmt-humeval.jsonl \
  'https://github.com/wmt-conference/wmt25-general-mt/raw/2fc0874d85278d8c7e0807951e54d8422e7957e4/data/wmt25-genmt-humeval.jsonl'
curl -fL --retry 3 -C - -o external/wmt25/wmt25-genmt-humeval_control.jsonl \
  'https://github.com/wmt-conference/wmt25-general-mt/raw/2fc0874d85278d8c7e0807951e54d8422e7957e4/data/wmt25-genmt-humeval_control.jsonl'
shasum -a 256 external/wmt25/wmt25-genmt-humeval*.jsonl
```

If a network proxy ends a download early, repeat the corresponding `curl`
command to resume it. The audit refuses files that do not match the sizes and
hashes above. GitHub CI runs the synthetic tests and a small smoke experiment
without the 146 MB raw data.
