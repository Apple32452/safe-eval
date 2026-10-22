# Stage 33: real-log feasibility and prospective panel experiment

## Retrospective diagnostic

Read the public raw WMT11 individual-system ranking CSV archived by
[Lopez](https://github.com/alopez/wmt-ranking). Include complete rows
with five distinct, nonblank system IDs and ranks in 1..5 (ties allowed).
For each input and unordered nonreference system pair, count the
distinct companion triplets, distinct raters and opposite nontied
preferences across different panels.

For one descriptive contrast, compare the signed A-over-B preference
on the same input and pair when the reference is among the other three
options versus absent. The primary subset requires disjoint raters
between conditions; a secondary subset includes all matched cells.
Average within-cell differences equally. Bootstrap source items (2,000
draws, seed 3301), keeping their pair cells together. This is post hoc
exploration, not a causal estimate: reference inclusion and the other
companions can vary together, task assignment and rater mix were not
controlled for this question, and rater noise can reverse preferences.
The item-only bootstrap also does not account for the same rater
appearing on multiple source items. Treat its interval as a descriptive
screen, not a fully calibrated uncertainty statement.

## Prospectively randomized human feasibility pilot

Use the public WMT25 English to Chinese source, reference and system
outputs already used in SAFE-EVAL. Before any new five-way judgments,
choose close-quality systems A=Qwen3-235B and B=GPT-4.1, with P0
companions C=Algharb, D=Shy, E=Claude-4 and P1 companions F=IRB-MT,
G=RuZh, H=Laniqo. Companion groups were selected using existing WMT25
mean scores, so this is a development choice, not untouched validation.

The extractor validates upstream bytes and SHA256, requires all eight
nonempty distinct outputs, and samples one eligible segment per document
from 40 of 51 eligible documents using seed 3303. Only a digest and
system mapping are committed; raw translation text stays in local
ignored results. No human pilot judgments have yet been collected.

For each selected source, show A/B with P0 or P1 to two **distinct
raters per context** (160 five-way tasks total). Randomize display
positions, blind systems, display the same source and reference, and
never assign a rater the same source twice. Raters must read English
and Chinese. Rank 1 (best) through 5 (worst), ties allowed; record
time. The task generator checks unique assignment per input.

Define Y=+1 when A ranks above B, Y=0 for a tie and Y=-1 otherwise.
For each document, compare mean Y in P1 versus P0. Average these
document effects equally and bootstrap documents for a descriptive
interval; report ties, missingness, rater agreement and task time.
The one-segment-per-document design makes document clustering
coincide with item clustering here. The 40-document pilot is a
feasibility screen, not paper-level evidence for a small effect.
Raters may judge several documents, so a confirmatory analysis must
account for both rater and document dependence or use a design-based
randomization test based on the recorded assignments.
Any promising result needs a larger independent replication, human
time accounting and matched active-ranking baselines.

The historical reference-presence contrast and prospective high/low
companion contrast are different questions. Neither would make
inverse-propensity weighting or active selection a new method; compare
[Sakaguchi et al. (2014)](https://aclanthology.org/W14-3301/),
[Knowles (2021)](https://aclanthology.org/2021.wmt-1.56/), and
[Waudby-Smith et al.](https://arxiv.org/abs/2210.10768).
