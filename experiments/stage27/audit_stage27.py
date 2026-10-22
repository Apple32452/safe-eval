"""Exact selection-bias and conditional-factor audit for two-stage sampling."""
from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path

from two_stage import ALPHA, EPSILON, RHOS, SCENARIOS, corrected_signal, run_synthetic


def exact_audit():
    # Four equally likely (item, rater) types: a tie in population contrasts.
    pairs = ((1, 0), (1, 0), (0, 1), (0, 1))
    expected_corrected = 0
    numerator_selected = 0
    denominator_selected = 0
    cases = 0
    for ref, cand in pairs:
        q = 1.0 if ref else EPSILON
        for z, chance in ((0, 1 - q), (1, q)):
            if chance == 0:
                continue
            expected_corrected += chance * corrected_signal(ref, cand, 0.3, q, z) / 4
            if z:
                numerator_selected += chance * (ref - cand) / 4
                denominator_selected += chance / 4
        # Enumerate arbitrary binary potential outcomes and several predictable
        # current-reference-dependent propensities and predictions.
    for values in product((0, 1), repeat=8):
        cells = tuple(zip(values[:4], values[4:]))
        if sum(ref - cand for ref, cand in cells) > 0:
            continue  # positive-direction null is population contrast <= 0
        for low_q in (EPSILON, 0.5, 1.0):
            for m_zero, m_one in product((0.0, 0.5, 1.0), repeat=2):
                mean_signal = 0.0
                for ref, cand in cells:
                    q = 1.0 if ref else low_q
                    m = m_one if ref else m_zero
                    for z in (0, 1):
                        signal = corrected_signal(ref, cand, m, q, z)
                        if abs(signal) > 1 / EPSILON + 1e-12:
                            raise AssertionError("Corrected signal exceeded its bound")
                        if any(1 - rho * EPSILON * abs(signal) <= 0 for rho in RHOS):
                            raise AssertionError("A betting factor was nonpositive")
                    mean_signal += ((1 - q) * corrected_signal(ref, cand, m, q, 0)
                                    + q * corrected_signal(ref, cand, m, q, 1)) / 4
                if mean_signal > 1e-12:
                    raise AssertionError("The corrected signal violates the null")
                for rho in RHOS:
                    if 1 + rho * EPSILON * mean_signal > 1 + 1e-12:
                        raise AssertionError("A null betting factor exceeded one")
                cases += 1
    assert abs(expected_corrected) < 1e-12
    naive_selected_mean = numerator_selected / denominator_selected
    assert abs(naive_selected_mean - 0.6) < 1e-12
    return dict(enumerated_null_settings=cases,
                tied_population_contrast=0,
                expected_corrected_signal=round(expected_corrected, 12),
                naively_selected_pair_mean=naive_selected_mean,
                prospective_rater_identification_counterexample=dict(
                    observed_rater_probability=0.1,
                    observed_rater_difference=1,
                    world_A_new_rater_difference=1,
                    world_B_new_rater_difference=-1,
                    world_A_population_difference=1,
                    world_B_population_difference=-0.8))


def summarize(rows):
    result = []
    for scenario in SCENARIOS:
        group = [r for r in rows if r["scenario"] == scenario]
        both = [r for r in group if r["paired"]["completed"] and r["two_stage"]["completed"]]
        result.append(dict(scenario=scenario, repeats=len(group),
                           population_signs=group[0]["population_signs"],
                           paired_completed=sum(r["paired"]["completed"] for r in group),
                           two_stage_completed=sum(r["two_stage"]["completed"] for r in group),
                           completed_both=len(both),
                           paired_wrong_runs=sum(r["paired"]["wrong"] > 0 for r in group),
                           two_stage_wrong_runs=sum(r["two_stage"]["wrong"] > 0 for r in group),
                           paired_mean_cost_to_stop_or_cap=sum(r["paired"]["cost"] for r in group)/len(group),
                           two_stage_mean_cost_to_stop_or_cap=sum(r["two_stage"]["cost"] for r in group)/len(group),
                           paired_mean_cost_when_both_complete=(sum(r["paired"]["cost"] for r in both)/len(both)
                                                                  if both else None),
                           two_stage_mean_cost_when_both_complete=(sum(r["two_stage"]["cost"] for r in both)/len(both)
                                                                     if both else None)))
    return result


def run(output, repeats=100, max_rounds=800):
    audit = exact_audit()
    rows = run_synthetic(repeats, max_rounds)
    payload = dict(protocol=dict(seed=20261022, alpha=ALPHA, epsilon=EPSILON,
                                 rhos=list(RHOS), max_rounds=max_rounds, repeats=repeats,
                                 item_count=32, rater_count=6,
                                 estimand="Expected system score for an iid uniform item and independent iid uniform rater",
                                 unit_cost="One system-item-rater judgment in each fresh draw"),
                   exact_audit=audit, summary=summarize(rows), replicates=rows)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "RESULTS.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(dict(exact_audit=audit, summary=payload["summary"]), indent=2))
    return payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--repeats", type=int, default=100)
    parser.add_argument("--max-rounds", type=int, default=800)
    args = parser.parse_args()
    run(args.output, args.repeats, args.max_rounds)
