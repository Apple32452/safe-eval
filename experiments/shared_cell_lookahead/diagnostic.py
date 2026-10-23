"""Exact small-pool cost-to-go diagnostic for shared system--item purchases.

Every target score matrix is fixed once drawn. The independent Bernoulli
probabilities are used to plan acquisitions and to weight the exhaustive
synthetic population, never to justify a sign declaration.
"""
from __future__ import annotations

import argparse
import gzip
import json
from functools import lru_cache
from pathlib import Path


SYSTEMS = 3
ITEMS = 3
CELLS = SYSTEMS * ITEMS
POW3 = tuple(3 ** j for j in range(CELLS))
STAR = ((0, 1), (0, 2))
TRIANGLE = ((0, 1), (0, 2), (1, 2))
EASY = (.9,) * 3 + (.5,) * 3 + (.1,) * 3
MODERATE = (.7,) * 3 + (.55,) * 3 + (.4,) * 3
HETEROGENEOUS = (.9, .7, .6, .55, .35, .65, .3, .4, .15)
SHIFTED = (.1,) * 3 + (.5,) * 3 + (.9,) * 3
SCENARIOS = {
    "easy": (EASY, EASY),
    "moderate": (MODERATE, MODERATE),
    "heterogeneous": (HETEROGENEOUS, HETEROGENEOUS),
    "shifted": (EASY, SHIFTED),
}


@lru_cache(maxsize=None)
def state_info(state: int):
    """Trit 0 = unknown, 1 = known zero, 2 = known one."""
    digits = tuple(state // power % 3 for power in POW3)
    ones = tuple(sum(digits[v * ITEMS + i] == 2 for i in range(ITEMS))
                 for v in range(SYSTEMS))
    missing = tuple(sum(digits[v * ITEMS + i] == 0 for i in range(ITEMS))
                    for v in range(SYSTEMS))
    return digits, ones, missing


def bounds(state: int, a: int, b: int):
    _, ones, missing = state_info(state)
    return ones[a] - ones[b] - missing[b], ones[a] - ones[b] + missing[a]


def signs(state: int, edges):
    result = []
    for a, b in edges:
        low, high = bounds(state, a, b)
        if low > 0:
            result.append(1)
        elif high < 0:
            result.append(-1)
        elif low == high == 0:
            result.append(0)
        else:
            result.append(None)
    return tuple(result)


def feasible_signs(state: int, edges) -> int:
    count = 0
    for a, b in edges:
        low, high = bounds(state, a, b)
        count += int(low < 0) + int(low <= 0 <= high) + int(high > 0)
    return count


class Planner:
    def __init__(self, probabilities, edges):
        self.p = tuple(float(p) for p in probabilities)
        if len(self.p) != CELLS or not all(0 < p < 1 for p in self.p):
            raise ValueError("Expected nine probabilities strictly in (0,1)")
        self.edges = tuple(tuple(edge) for edge in edges)
        if not self.edges or any(a >= b or b >= SYSTEMS for a, b in self.edges):
            raise ValueError("Invalid comparison graph")

    def candidates(self, state):
        digits, _, _ = state_info(state)
        unresolved = (edge for edge, sign in zip(self.edges, signs(state, self.edges))
                      if sign is None)
        degree = [0] * SYSTEMS
        for a, b in unresolved:
            degree[a] += 1
            degree[b] += 1
        return sorted((j for j, digit in enumerate(digits) if digit == 0),
                      key=lambda j: (-degree[j // ITEMS], j // ITEMS, j % ITEMS))

    @lru_cache(maxsize=None)
    def bellman(self, state: int):
        """Return optimal expected remaining labels and first cell to buy."""
        if None not in signs(state, self.edges):
            return 0., None
        best_cost, best_cell = float("inf"), None
        for cell in self.candidates(state):
            p = self.p[cell]
            expected = (1 + (1 - p) * self.bellman(state + POW3[cell])[0]
                        + p * self.bellman(state + 2 * POW3[cell])[0])
            if expected < best_cost - 1e-12:
                best_cost, best_cell = expected, cell
        return best_cost, best_cell

    def greedy(self, state: int):
        if None not in signs(state, self.edges):
            return None
        before = feasible_signs(state, self.edges)
        best_gain, best_cell = -float("inf"), None
        for cell in self.candidates(state):
            p = self.p[cell]
            after = ((1 - p) * feasible_signs(state + POW3[cell], self.edges)
                     + p * feasible_signs(state + 2 * POW3[cell], self.edges))
            gain = before - after
            if gain > best_gain + 1e-12:
                best_gain, best_cell = gain, cell
        return best_cell


def target_weight(mask, probabilities):
    weight = 1.
    for cell, p in enumerate(probabilities):
        weight *= p if mask & (1 << cell) else 1 - p
    return weight


def buy(state, mask, cell):
    if state_info(state)[0][cell] != 0:
        raise AssertionError("Repeated system--item purchase")
    value = (mask >> cell) & 1
    return state + POW3[cell] * (1 + value), [cell // ITEMS, cell % ITEMS, value]


def trajectory(mask, planner: Planner, method):
    state = 0
    ledger = []
    if method in ("lookahead", "greedy"):
        while None in signs(state, planner.edges):
            cell = (planner.bellman(state)[1] if method == "lookahead"
                    else planner.greedy(state))
            state, purchase = buy(state, mask, cell)
            ledger.append(purchase)
    elif method in ("pruned_blocks", "common_blocks"):
        for item in range(ITEMS):
            if None not in signs(state, planner.edges):
                break
            if method == "common_blocks":
                active = range(SYSTEMS)
            else:
                active = sorted({v for edge, sign in zip(planner.edges,
                                 signs(state, planner.edges)) if sign is None
                                 for v in edge})
            # The item block is committed before any score in it is revealed.
            for v in active:
                state, purchase = buy(state, mask, v * ITEMS + item)
                ledger.append(purchase)
    else:
        raise ValueError(f"Unknown method: {method}")
    decision = signs(state, planner.edges)
    if None in decision:
        raise AssertionError("Unresolved graph after all eligible purchases")
    return dict(cost=len(ledger), decision=decision, ledger=ledger)


def truth(mask, edges):
    totals = [sum((mask >> (v * ITEMS + i)) & 1 for i in range(ITEMS))
              for v in range(SYSTEMS)]
    return tuple((totals[a] > totals[b]) - (totals[a] < totals[b])
                 for a, b in edges)


def first_difference(planner):
    """Find the first reachable state on an optimal path with differing rules."""
    states = {0}
    while states:
        next_states = set()
        for state in sorted(states):
            if None not in signs(state, planner.edges):
                continue
            opt = planner.bellman(state)[1]
            myopic = planner.greedy(state)
            if opt != myopic:
                return dict(state=list(state_info(state)[0]),
                            lookahead=[opt // ITEMS, opt % ITEMS],
                            greedy=[myopic // ITEMS, myopic % ITEMS],
                            optimal_remaining=planner.bellman(state)[0])
            next_states.update((state + POW3[opt], state + 2 * POW3[opt]))
        states = next_states
    return None


def run():
    result = {"protocol": "experiments/shared_cell_lookahead/PROTOCOL.md",
              "settings": {}}
    methods = ("lookahead", "greedy", "pruned_blocks", "common_blocks")
    for scenario, (planner_p, target_p) in SCENARIOS.items():
        for graph, edges in (("star", STAR), ("triangle", TRIANGLE)):
            planner = Planner(planner_p, edges)
            expected = {name: 0. for name in methods}
            rows = []
            for mask in range(1 << CELLS):
                weight = target_weight(mask, target_p)
                outputs = {name: trajectory(mask, planner, name) for name in methods}
                actual = truth(mask, edges)
                for name, output in outputs.items():
                    if tuple(output["decision"]) != actual:
                        raise AssertionError("Invalid logical sign")
                    expected[name] += weight * output["cost"]
                rows.append(dict(mask=mask, weight=weight, truth=actual,
                                 methods=outputs))
            if abs(sum(row["weight"] for row in rows) - 1) > 1e-12:
                raise AssertionError("Incomplete target probability mass")
            if planner_p == target_p and abs(expected["lookahead"] -
                                             planner.bellman(0)[0]) > 1e-9:
                raise AssertionError("Exhaustive cost and Bellman value disagree")
            key = scenario + "_" + graph
            result["settings"][key] = dict(
                scenario=scenario, graph=graph, edges=edges,
                planner_probabilities=planner_p, target_probabilities=target_p,
                expected_cost=expected, first_difference=first_difference(planner),
                rows=rows)
            print(key, {k: round(v, 5) for k, v in expected.items()}, flush=True)
    s = result["settings"]
    good = all(
        all(s[f"{scenario}_star"]["expected_cost"]["lookahead"] <=
            .9 * s[f"{scenario}_star"]["expected_cost"][control] + 1e-12
            for control in ("greedy", "pruned_blocks"))
        and s[f"{scenario}_star"]["first_difference"] is not None
        for scenario in ("easy", "moderate"))
    shifted = s["shifted_star"]["expected_cost"]
    result["diagnostic_gate_pass"] = bool(
        good and shifted["lookahead"] <= 1.1 * shifted["pruned_blocks"] + 1e-12)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(result, separators=(",", ":")) + "\n").encode()
    if args.output.suffix == ".gz":
        args.output.write_bytes(gzip.compress(encoded, mtime=0))
    else:
        args.output.write_bytes(encoded)
    print("diagnostic_gate_pass", result["diagnostic_gate_pass"])
