"""Independent ledger and exhaustive completion audit for toy lookahead."""
from __future__ import annotations

import argparse
import itertools
import json
from collections import defaultdict
from pathlib import Path

from diagnostic import CELLS, ITEMS, SCENARIOS, STAR, TRIANGLE, Planner


def exact_signs(values, edges):
    totals = [sum(values[system * ITEMS + item] for item in range(ITEMS))
              for system in range(3)]
    return tuple((totals[a] > totals[b]) - (totals[a] < totals[b])
                 for a, b in edges)


def audit_row(row, edges, planner, method):
    mask = int(row["mask"])
    full = [(mask >> cell) & 1 for cell in range(CELLS)]
    assert tuple(row["truth"]) == exact_signs(full, edges)
    output = row["methods"][method]
    bought = {}
    for purchase in output["ledger"]:
        system, item, value = map(int, purchase)
        cell = system * ITEMS + item
        assert 0 <= system < 3 and 0 <= item < ITEMS
        assert cell not in bought and full[cell] == value
        if method in ("lookahead", "greedy"):
            state = sum((1 + old) * 3 ** idx for idx, old in bought.items())
            intended = (planner.bellman(state)[1] if method == "lookahead"
                        else planner.greedy(state))
            assert cell == intended, "Purchase depends on hidden score or wrong policy"
        bought[cell] = value
    assert len(bought) == output["cost"]
    unknown = [j for j in range(CELLS) if j not in bought]
    final_decision = tuple(output["decision"])
    assert None not in final_decision
    for completion in itertools.product((0, 1), repeat=len(unknown)):
        values = full.copy()
        for cell, value in zip(unknown, completion):
            values[cell] = value
        assert exact_signs(values, edges) == final_decision
    # An outcome on a different, still hidden matrix can never affect the
    # previously selected action; the replay above sees only bought scores.
    return len(unknown)


def audit(payload):
    assert len(payload["settings"]) == len(SCENARIOS) * 2
    counts = defaultdict(int)
    summaries = {}
    methods = ("lookahead", "greedy", "pruned_blocks", "common_blocks")
    for scenario, (planner_p, target_p) in SCENARIOS.items():
        for graph, edges in (("star", STAR), ("triangle", TRIANGLE)):
            key = scenario + "_" + graph
            section = payload["settings"][key]
            assert tuple(tuple(e) for e in section["edges"]) == edges
            assert tuple(section["planner_probabilities"]) == planner_p
            assert tuple(section["target_probabilities"]) == target_p
            planner = Planner(planner_p, edges)
            expected = {name: 0. for name in methods}
            mass = 0.
            assert len(section["rows"]) == 1 << CELLS
            for index, row in enumerate(section["rows"]):
                assert row["mask"] == index
                weight = 1.
                for cell, p in enumerate(target_p):
                    weight *= p if index & (1 << cell) else 1 - p
                assert abs(row["weight"] - weight) < 1e-15
                mass += weight
                for method in methods:
                    counts["checked_paths"] += 1
                    unknown = audit_row(row, edges, planner, method)
                    counts["compatible_completions"] += 1 << unknown
                    expected[method] += weight * row["methods"][method]["cost"]
            assert abs(mass - 1) < 1e-12
            assert all(abs(expected[method] - section["expected_cost"][method])
                       < 1e-10 for method in methods)
            if planner_p == target_p:
                assert expected["lookahead"] <= expected["greedy"] + 1e-10
                assert abs(planner.bellman(0)[0] - expected["lookahead"]) < 1e-10
            summaries[key] = {name: round(expected[name], 8) for name in methods}
    costs = {key: payload["settings"][key]["expected_cost"] for key in summaries}
    positive = all(
        all(costs[scenario + "_star"]["lookahead"] <=
            .9 * costs[scenario + "_star"][control] + 1e-12
            for control in ("greedy", "pruned_blocks"))
        and payload["settings"][scenario + "_star"]["first_difference"] is not None
        for scenario in ("easy", "moderate"))
    shift = costs["shifted_star"]
    assert payload["diagnostic_gate_pass"] == bool(
        positive and shift["lookahead"] <= 1.1 * shift["pruned_blocks"] + 1e-12)
    return dict(counts=counts, expected_cost=summaries,
                diagnostic_gate_pass=payload["diagnostic_gate_pass"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text())
    report = audit(payload)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Checked {report['counts']['checked_paths']} paths and "
          f"{report['counts']['compatible_completions']} compatible completions; "
          f"gate={report['diagnostic_gate_pass']}")
