"""Idealized, outcome-free scale calculation for four-judge panels."""
from __future__ import annotations

import json
from math import ceil, sqrt
from statistics import NormalDist

VARIANCE_BOUND = 4 / 3


def plan(deltas=(.2, .4, .6), alpha=.05, power=.8, pilot_docs=40):
    if not 0 < alpha < 1 or not .5 < power < 1 or pilot_docs < 1:
        raise ValueError("Invalid planning parameters")
    z = NormalDist().inv_cdf(1 - alpha / 2) + NormalDist().inv_cdf(power)
    effect_scale = z * sqrt(VARIANCE_BOUND / pilot_docs)
    return {
        "assumptions": "independent 2-of-4 document assignments; bounded fixed potential outcomes; no interference; normal approximation",
        "alpha": alpha, "power": power,
        "variance_bound": VARIANCE_BOUND,
        "pilot_documents": pilot_docs, "pilot_tasks": 4 * pilot_docs,
        "approx_min_detectable_signed_effect": effect_scale,
        "scenarios": [{"signed_effect": d, "approx_documents": ceil(VARIANCE_BOUND * (z / d) ** 2),
                       "approx_tasks": 4 * ceil(VARIANCE_BOUND * (z / d) ** 2)}
                      for d in deltas if d > 0]
    }


if __name__ == "__main__":
    print(json.dumps(plan(), indent=2))
