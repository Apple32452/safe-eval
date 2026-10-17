"""Exhaustive rational checks; no WMT data, random seed, or parameter tuning."""
import argparse
from fractions import Fraction as F
from itertools import combinations, product
import hashlib
import json
from pathlib import Path

from assignment_boost import (capped_factors, centered_boost, centered_factors,
                              naive_plugin_counterexample, worst_expectation)


def assignments(r, k):
    for ones in combinations(range(r), k):
        ones = set(ones)
        yield tuple(int(i in ones) for i in range(r))


def enumerated_expectations(table, k):
    r = len(table)
    return tuple(sum((table[i][y] for i, y in enumerate(labels)), F(0)) / r
                 for labels in assignments(r, k))


def audit():
    probes = expectations = boost_states = boost_expectations = 0
    unbounded_states = 0
    for r in range(1, 5):
        for predictions in product((F(1, 10), F(1, 2), F(9, 10)), repeat=r):
            for k in range(r + 1):
                for theta in (F(-1, 2), F(0), F(1, 2)):
                    table = centered_factors(predictions, k, theta)
                    assert all(x == 1 for x in enumerated_expectations(table, k))
                    for cap in (F(3, 2), F(2)):
                        for multiplier in (F(1), F(4, 3), F(3)):
                            capped = capped_factors(table, k, multiplier, cap)
                            brute = enumerated_expectations(capped, k)
                            assert max(brute) == worst_expectation(
                                table, k, multiplier, cap)
                            probes += 1
                            expectations += len(brute)
                        boost = centered_boost(predictions, k, theta, cap)
                        assert boost.multiplier >= 1
                        capped = capped_factors(table, k, boost.multiplier, cap)
                        brute = enumerated_expectations(capped, k)
                        assert max(brute) <= 1
                        if boost.finite_maximum:
                            assert max(brute) == 1
                            assert worst_expectation(
                                table, k, boost.multiplier + F(1, 10000), cap) > 1
                        else:
                            assert worst_expectation(
                                table, k, boost.multiplier * 2, cap) == max(brute)
                            unbounded_states += 1
                        boost_states += 1
                        boost_expectations += len(brute)
    example = naive_plugin_counterexample()
    assert example["working_mean"] == 1
    assert example["true_mean"] == F(185, 181) > 1
    assert example["robust_multiplier"] == 1
    return {"status": "passed", "arithmetic": "fractions.Fraction; no tolerances",
            "pool_sizes": [1, 2, 3, 4],
            "prediction_grid": ["1/10", "1/2", "9/10"],
            "remaining_totals": "all 0 through r",
            "stakes": ["-1/2", "0", "1/2"], "caps": ["3/2", "2"],
            "multipliers_for_identity": ["1", "4/3", "3"],
            "top_k_probes": probes, "enumerated_assignment_expectations": expectations,
            "boost_states": boost_states,
            "boost_assignment_expectations": boost_expectations,
            "unbounded_boost_states": unbounded_states,
            "counterexample": {key: str(value) for key, value in example.items()},
            "scope": "one-step algebra and conditional validity only; no full-CS coverage or benchmark claim",
            "source_sha256": {
                name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                for name in ("assignment_boost.py", "audit_stage12.py", "test_stage12.py")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--check-reference", type=Path)
    args = parser.parse_args()
    result = audit()
    if args.check_reference is not None:
        expected = json.loads(args.check_reference.read_text())
        if result != expected:
            raise SystemExit("The audit differs from the recorded reference.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("Passed {top_k_probes} top-k probes, {boost_states} boost states, "
          "and the exact plug-in counterexample.".format(**result))
