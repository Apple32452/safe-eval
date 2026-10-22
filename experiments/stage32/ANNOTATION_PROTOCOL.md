# Proposed human validation of companion-panel effects

This is a **prospective protocol**, not collected data. Its purpose is to
check the premise behind Stage 31 before claiming that panel allocation can
preserve a pairwise comparison target.

1. Select real, licensed evaluation inputs and two fixed MT systems A and B.
   For each input, save their outputs before annotation. Construct at least
   two companion triplets from other fixed systems, for the same input.
   Set an explicit target distribution over the triplets in advance; name
   the source and population of inputs and raters.
2. Randomly allocate the **same input and A/B outputs** to each companion
   triplet across distinct, independent raters. Blind system identities and
   randomize display order. Record input, output hashes, panel membership,
   actual displayed order, rater and task IDs, randomization probabilities,
   complete five-way ranking, ties or unjudgeable status, and task duration.
3. Estimate the within-input effect of companion assignment on the A/B
   preference (A above B = +1, tied = 0, B above A = -1), with clustering
   and rater effects accounted for in the design and analysis. Report its
   magnitude and uncertainty, the frequency of reversals, and variation
   across language pairs, relative system quality, input difficulty, and
   display position. Separate a detectable context effect from ordinary
   between-rater noise.
4. For a prospective sequential comparison, use **fresh randomized inputs
   and independently assigned raters per round**; log the pre-judgment
   companion probabilities, impose a positive probability floor for every
   target panel, and predeclare the target mixture, allowable stakes,
   familywise error allocation, and stopping threshold. A/B evaluations
   on the same input by multiple raters are useful for the context study
   but are not automatically independent rounds for the Stage 32 e-process.
   Treat an input/rater block as one unit or prove a valid block-level
   conditional expectation before using repeated evaluations for inference.
5. Compare target-randomized, adaptive unweighted, and adaptive corrected
   policies against matched contemporary active-ranking baselines. Report
   wrong conclusions, abstentions, panel tasks, **measured human time**,
   and confidence intervals across language pairs. Analyze missing ratings
   and low-propensity weights transparently. Keep an external language or
   campaign untouched until policy and analysis are frozen.

Neither historical five-way logs nor a single rank observed for one panel
reveal the counterfactual rank a rater would have assigned to another
panel. Repeated, randomized panel assignment is required for a causal
test of companion effects. Obtaining human data, consent as applicable,
and a credible matched comparison is future work.
