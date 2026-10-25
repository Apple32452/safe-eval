"""Replay saved purchases with independent null enumeration and decisions."""
from __future__ import annotations

import argparse
import hashlib
import json
from functools import lru_cache
from itertools import product
from pathlib import Path

import numpy as np

from joint_order import DIRECTED, IMPLIED, ORDERS, PAIRS, RHOS, state_update
from run_study import ALPHA, GRAPHS, HERE, METHODS, N, SCENARIOS, make_paths


@lru_cache(maxsize=30000)
def check_state(s_tuple, m_tuple, prior):
    s, m = np.array(s_tuple), np.array(m_tuple)
    totals = np.array(list(product(*(range(int(a), int(a+b+1)) for a, b in zip(s, m)))))
    masks = [np.all(np.column_stack([totals[:, DIRECTED[i][0]] <=
                                     totals[:, DIRECTED[i][1]] for i in ids]), axis=1)
             for ids in IMPLIED]
    if not m.sum():
        return np.array([mask.any() for mask in masks]), 0, 0.
    update = state_update(s_tuple, m_tuple, prior, N)
    pred = np.clip((s + 4*np.array(prior))/(N-m+4), .05, .95)
    weight = m * np.array([sum(1/max(abs(pred[v]-pred[u]), .1)
                               for u in range(3) if u != v) for v in range(3)])
    q = .2*m/m.sum() + .8*weight/weight.sum()
    if not np.allclose(q, update["q"], atol=1e-12):
        raise AssertionError("Proposal replay failed")
    laws = np.zeros((len(totals), 6))
    for v in range(3):
        if m[v]:
            laws[:, 2*v+1] = q[v]*(totals[:, v]-s[v])/m[v]
            laws[:, 2*v] = q[v] - laws[:, 2*v+1]
    checks, largest = 0, 0.
    for index, mask in enumerate(masks):
        if mask.any():
            expected = laws[mask] @ update["joint"][index]
            largest = max(largest, float(expected.max()))
            if expected.max() > 1+1e-10:
                raise AssertionError("Joint factor fails an integer null completion")
            checks += len(expected)
    for index, (a, b) in enumerate(DIRECTED):
        mask = totals[:, a] <= totals[:, b]
        if mask.any():
            pair = laws[mask] @ update["pair"][index]
            centered = laws[mask] @ update["centered"][index]
            largest = max(largest, float(pair.max()), float(centered.max()))
            if max(pair.max(), centered.max()) > 1+1e-10:
                raise AssertionError("Pair factor fails an integer null completion")
            checks += len(pair) * (1 + len(RHOS))
    return np.array([mask.any() for mask in masks]), checks, largest


def audit_case(case):
    scenario, repeat = case["scenario"], case["repeat"]
    seed = int.from_bytes(hashlib.sha256(
        f"20261025|joint_order_gate|{scenario}|{repeat}".encode()).digest()[:8], "little")
    if seed != case["seed"]:
        raise AssertionError("Wrong seed")
    actual, prior, correlated = SCENARIOS[scenario]
    expected_scores = (np.random.default_rng(seed).random((1 if correlated else 3, N)) <
                       np.array(actual)[:, None]).astype(int)
    scores = np.array(case["scores"])
    if not np.array_equal(scores, expected_scores):
        raise AssertionError("Changed synthetic matrix")
    truth = np.array([np.sign(scores[a].sum()-scores[b].sum()) for a, b in PAIRS], int)
    s, m = np.zeros(3, int), np.full(3, N)
    joint, pair, centered = np.zeros(13), np.zeros(6), np.zeros((6, len(RHOS)))
    eliminated = np.zeros((3, 13), bool)
    decisions = np.full((3, 3), 2, int)
    stopped = {g: {} for g in GRAPHS}
    remaining = [list(range(N)) for _ in range(3)]
    rng = np.random.default_rng(seed ^ 0xC0FFEE)
    checks = 0
    largest = 0.
    fallback_count = failed_count = 0
    for t, event in enumerate(case["trace"], 1):
        _, count, maximum = check_state(tuple(s), tuple(m), prior)
        checks += count; largest = max(largest, maximum)
        update = state_update(tuple(s), tuple(m), prior, N)
        fallback_count += update["fallbacks"]; failed_count += update["failed_status"]
        v = int(rng.choice(3, p=update["q"]))
        item = remaining[v].pop(int(rng.integers(len(remaining[v]))))
        if (v, item) != (event["row"], event["item"]):
            raise AssertionError("Adaptive purchase replay failed")
        if not np.allclose(event["q"], update["q"], atol=1e-12):
            raise AssertionError("Saved propensity changed")
        y = int(scores[v, item])
        if y != event["value"]:
            raise AssertionError("Saved outcome changed")
        j = 2*v+y
        joint += np.log(update["joint"][:, j])
        pair += np.log(update["pair"][:, j])
        centered += np.log(update["centered"][:, j])
        center_mix = np.logaddexp.reduce(centered, axis=1) - np.log(len(RHOS))
        for order_id, ids in enumerate(IMPLIED):
            eliminated[0, order_id] |= joint[order_id] >= np.log(1/ALPHA)
            eliminated[1, order_id] |= np.logaddexp.reduce(pair[list(ids)]) - np.log(len(ids)) >= np.log(1/ALPHA)
            eliminated[2, order_id] |= np.logaddexp.reduce(center_mix[list(ids)]) - np.log(len(ids)) >= np.log(1/ALPHA)
        s[v] += y; m[v] -= 1
        feasible, _, _ = check_state(tuple(s), tuple(m), prior)
        eliminated |= ~feasible
        for method in range(3):
            survivors = [w for i, w in enumerate(ORDERS) if not eliminated[method, i]]
            for edge, (a, b) in enumerate(PAIRS):
                if decisions[method, edge] != 2:
                    continue
                lower, upper = s[a]-s[b]-m[b], s[a]+m[a]-s[b]
                if lower > 0:
                    decisions[method, edge] = 1
                elif upper < 0:
                    decisions[method, edge] = -1
                elif m[a] == m[b] == 0:
                    decisions[method, edge] = np.sign(s[a]-s[b])
                elif survivors and all(w[a] > w[b] for w in survivors):
                    decisions[method, edge] = 1
                elif survivors and all(w[a] < w[b] for w in survivors):
                    decisions[method, edge] = -1
            for graph, ids in GRAPHS.items():
                name = METHODS[method]
                d = decisions[method, list(ids)]
                if name not in stopped[graph] and np.all(d != 2):
                    wrong = int(np.any(d != truth[list(ids)]))
                    stopped[graph][name] = {"paid": t, "charged": 3*N if wrong else t,
                        "wrong": wrong, "correct_completion": 1-wrong, "decisions": d.tolist()}
    if fallback_count != case["unit_fallbacks"] or failed_count != case["solver_failed_status"]:
        raise AssertionError("Numerical diagnostic replay failed")
    order = np.random.default_rng(seed ^ 0x22).permutation(N)
    if list(order) != case["stage22_order"]:
        raise AssertionError("Changed Stage 22 item path")
    for graph, ids in GRAPHS.items():
        pairs = np.array([PAIRS[e] for e in ids])
        events, _ = make_paths(scores, pairs, np.tile(order, (len(ids), 1, 1)), 2*len(ids)/ALPHA)
        costs, values, bought = [], [], set()
        for edge, (a, b) in enumerate(pairs):
            count = next(t+1 for t, value in enumerate(events[edge, 0]) if value != 2)
            costs.append(count); values.append(int(events[edge, 0, count-1]))
            bought.update((int(v), int(i)) for v in (a, b) for i in order[:count])
        wrong = int(np.any(np.array(values) != truth[list(ids)]))
        stopped[graph]["stage22"] = {"paid": len(bought), "charged": 3*N if wrong else len(bought),
            "wrong": wrong, "correct_completion": 1-wrong, "decisions": values, "edge_prefixes": costs}
    if stopped != case["stops"]:
        raise AssertionError("Independent sign/stop/cost replay differs")
    return checks, largest


def audit(directory):
    directory = Path(directory)
    cases = json.loads((directory/"cases.json").read_text())
    meta = json.loads((directory/"metadata.json").read_text())
    saved = json.loads((directory/"summary.json").read_text())
    digest = hashlib.sha256((HERE/"PROTOCOL.md").read_bytes()).hexdigest()
    repeats = meta["repeats"]
    if (meta["protocol_sha256"] != digest or meta["items"] != N or
            meta["systems"] != 3 or meta["alpha"] != ALPHA or repeats < 1):
        raise AssertionError("Frozen metadata changed")
    if {(c["scenario"], c["repeat"]) for c in cases} != {
            (s, i) for s in SCENARIOS for i in range(repeats)} or len(cases) != repeats*len(SCENARIOS):
        raise AssertionError("Missing or duplicate cases")
    checks, largest = 0, 0.
    for case in cases:
        count, maximum = audit_case(case)
        checks += count; largest = max(largest, maximum)
    rng = np.random.default_rng(20261025)
    all_no_errors = True
    aligned = True
    reverse_ok = True
    for scenario in SCENARIOS:
        group = sorted([c for c in cases if c["scenario"] == scenario], key=lambda c: c["repeat"])
        for graph in GRAPHS:
            costs = {}
            for method in METHODS:
                rows = [c["stops"][graph][method] for c in group]
                costs[method] = np.array([r["charged"] for r in rows])
                computed = {"mean_paid": np.mean([r["paid"] for r in rows]),
                    "mean_charged": costs[method].mean(),
                    "correct_completions": sum(r["correct_completion"] for r in rows),
                    "wrong_paths": sum(r["wrong"] for r in rows)}
                for metric, value in computed.items():
                    if not np.isclose(saved[scenario][graph][method][metric], value):
                        raise AssertionError("Summary mismatch")
                if method == "joint_order" and computed["wrong_paths"]:
                    all_no_errors = False
            idx = rng.integers(repeats, size=(10000, repeats))
            for control in METHODS[1:]:
                a, b = costs["joint_order"], costs[control]
                saving = 1-a.mean()/b.mean()
                ci = np.quantile(1-a[idx].mean(axis=1)/b[idx].mean(axis=1), [.025, .975])
                comparison = saved[scenario][graph]["comparisons"][control]
                if not np.isclose(saving, comparison["relative_saving"]) or not np.allclose(ci, comparison["paired_bootstrap_95"]):
                    raise AssertionError("Bootstrap mismatch")
                if control in ("exact_pair_closure", "stage22"):
                    if scenario in ("independent_strong", "independent_moderate"):
                        aligned &= ci[0] > 0
                    if scenario == "reversed":
                        reverse_ok &= saving >= -.10
    expected_gate = bool(all_no_errors and aligned and reverse_ok)
    if expected_gate != saved["expansion_gate"]:
        raise AssertionError("Expansion gate mismatch")
    numerical = {"unit_fallbacks": sum(c["unit_fallbacks"] for c in cases),
                 "solver_failed_status": sum(c["solver_failed_status"] for c in cases)}
    if numerical != saved["numerical"]:
        raise AssertionError("Numerical summary mismatch")
    return {"status": "passed", "cases": len(cases),
            "graph_method_results": len(cases)*len(GRAPHS)*len(METHODS),
            "integer_null_expectations_checked_with_replays": checks,
            "largest_null_expectation": largest, "protocol_sha256": digest,
            "expansion_gate": expected_gate,
            "note": "Conditional checks enumerate integer null completions; no human data."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.input)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
