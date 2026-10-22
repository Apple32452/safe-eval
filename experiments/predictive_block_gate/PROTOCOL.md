# Historical predictor and graph-aware block development screen

This protocol fixes the 30-repeat development comparison before looking at
its results. A two-repeat software smoke was run first and is not used to
select parameters or make scientific claims.

## Target and observations

For each of five named synthetic scenarios, use 30 seed-fixed matrices with
5 systems, 128 target items, and 4 requested reference edges. A score is
binary in this screen. Side features are known before target sampling. For
each system, a linear ridge predictor is fitted to 256 independently
generated **historical** examples and the corresponding side features. The
target matrix is never an input to the fit. One scenario reverses the
historical base rates and feature slope to stress prediction mismatch.

The sampling policy chooses a block before seeing any current target score.
All methods must resolve all four full-pool signs at `alpha=.05`, with
two-sided e-process thresholds `2*4/.05`, logical bounds, and exact signs at
full exposure. The cost is the number of distinct system–item scores bought.
There is no imputation counted as a purchased human score.

## Fixed methods

1. **Raw Stage 22:** full blocks in the identical uniform item order as the
   prediction-aware full-block trial, and the frozen Stage 22 certificate.
2. **Prediction-aware full block:** all unresolved endpoints on a uniformly
   selected fresh item, with a prediction-centered finite-pool e-process.
3. **Prediction-aware uniform partial block:** uniformly selected eligible
   item; maximum-degree unknown endpoint guaranteed, each other unknown
   active endpoint included with probability `.75`.
4. **Prediction-aware graph partial block:** item probability is half uniform
   and half proportional to `1 + sum_v degree(v)*m_vi*(1-m_vi)` among unknown
   active endpoints. Include the highest-degree unknown endpoint. Each other
   endpoint `v` is included with probability
   `max_e[.2 + .8*exp(-abs(predicted_total_a-predicted_total_b)/(.12*N))]`
   over unresolved incident edges. All probabilities are predictable and
   positive. Repeated items are allowed but purchased cells are cached.

For each unresolved edge, the signal is its already observed contrast plus
the sum of predictions for unseen endpoints plus the inclusion-weighted
residuals in the chosen block. Its conditional mean is the exact fixed-pool
contrast, regardless of predictor quality. The lower and upper support
bounds maximize the negative and positive residuals over all possible items;
the e-process never assumes independent system scores within an item.

## Decision rule for further research

The graph partial policy must lower **average completed label cost** by at
least 10% relative to the prediction-aware full block in at least two of the
four aligned scenarios, with no increase over 10% on the reversed-history
scenario, to justify a larger WMT25 development comparison. Its gain must
also be distinguished from the gain of the same predictions with full blocks.
We will report every scenario and the matched paths regardless of outcome.
Thirty repeats are exploratory; observed zero errors does not prove the
familywise guarantee, and this screen alone cannot establish ICML novelty.

The existing literature already covers historical-data-guided active
confidence sequences for a single model, inverse-weighted adaptive inference,
and shared-item anytime ranking. A future novelty claim needs a new
allocation theorem or a substantial matched efficiency gain in a setting
those results do not already cover, then held-out confirmation.
