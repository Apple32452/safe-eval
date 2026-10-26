# Post-run wording clarification

The frozen protocol's phrase "identical matrices, history and item strata"
applies to the data and to the three same-inference cell-acquisition controls.
Its more specific method list says paired exact closure receives **global
historical marginals**. The actual pre-run implementation did exactly that.
Stage 22 used its preserved common-item inference without historical features.
Those methods received the same target scores and item order, but did not
condition their inference on item stratum. No code, frozen run, numerical
result, or protocol hash changed in this clarification. The matched same-
inference row-peer and peer-cell comparisons remain the decisive ones.
