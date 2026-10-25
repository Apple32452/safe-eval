"""Frozen matched shared-cell experiment for joint ordering evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import scipy

from joint_order import Evidence, PAIRS, state_update

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stage17"))
from continuous_engine import make_paths

N = 16
REPEATS = 20
ALPHA = .05
METHODS = ("joint_order", "exact_pair_closure", "centered_pair_closure", "stage22")
GRAPHS = {"star": (0, 1), "triangle": (0, 1, 2)}
SCENARIOS = {
    "independent_strong": ((.15, .50, .85), (.20, .50, .80), False),
    "independent_moderate": ((.30, .50, .70), (.30, .50, .70), False),
    "correlated_strong": ((.15, .50, .85), (.20, .50, .80), True),
    "reversed": ((.85, .50, .15), (.15, .50, .85), False),
    "near_ties": ((.45, .50, .55), (.30, .50, .70), False),
}


def seed_for(scenario, repeat):
    digest = hashlib.sha256(f"20261025|joint_order_gate|{scenario}|{repeat}".encode()).digest()
    return int.from_bytes(digest[:8], "little")


def record_stop(cost, decisions, truth, n):
    wrong = int(np.any(np.asarray(decisions) != truth))
    return {"paid": int(cost), "charged": int(3*n if wrong else cost),
            "wrong": wrong, "correct_completion": 1 - wrong,
            "decisions": list(map(int, decisions))}


def run_cells(scores, prior, seed):
    scores = np.asarray(scores, int)
    if scores.shape[0] != 3 or not np.isin(scores, (0, 1)).all():
        raise ValueError("Exactly three binary system rows required")
    n = scores.shape[1]
    s, m = np.zeros(3, int), np.full(3, n)
    unseen = [list(range(n)) for _ in range(3)]
    seen = set()
    rng = np.random.default_rng(seed)
    evidence = Evidence(ALPHA)
    truth = np.array([np.sign(scores[a].sum() - scores[b].sum()) for a, b in PAIRS])
    stops = {graph: {} for graph in GRAPHS}
    trace = []
    fallbacks = failed_status = 0
    for t in range(3*n):
        update = state_update(tuple(s), tuple(m), tuple(prior), n)
        fallbacks += update["fallbacks"]; failed_status += update["failed_status"]
        v = int(rng.choice(3, p=update["q"]))
        position = int(rng.integers(len(unseen[v])))
        item = unseen[v].pop(position)
        if (v, item) in seen:
            raise AssertionError("Repurchased a cell")
        seen.add((v, item))
        value = int(scores[v, item])
        s[v] += value; m[v] -= 1
        evidence.advance(update, 2*v + value, s, m)
        trace.append({"row": v, "item": item, "value": value,
                      "q": update["q"].tolist()})
        for graph, ids in GRAPHS.items():
            for method, name in enumerate(METHODS[:3]):
                decisions = evidence.decisions[method, list(ids)]
                if name not in stops[graph] and np.all(decisions != 2):
                    stops[graph][name] = record_stop(t+1, decisions, truth[list(ids)], n)
        if all(len(stops[g]) == 3 for g in GRAPHS):
            break
    if not all(len(stops[g]) == 3 for g in GRAPHS):
        raise AssertionError("Unresolved graph at full evaluation")
    return {"stops": stops, "trace": trace, "unit_fallbacks": fallbacks,
            "solver_failed_status": failed_status}


def stage22(scores, edge_ids, order):
    n = scores.shape[1]
    edges = np.array([PAIRS[i] for i in edge_ids], dtype=np.int16)
    paths = np.tile(order, (len(edges), 1, 1))
    events, _ = make_paths(scores, edges, paths, 2 * len(edges) / ALPHA)
    prefix = [int(np.flatnonzero(event != 2)[0]) + 1 for event in events[:, 0]]
    decisions = [int(events[i, 0, count - 1]) for i, count in enumerate(prefix)]
    # The proved common-prefix footprint exactly prices active-vertex purchases.
    cost = sum(max([prefix[i] for i, edge in enumerate(edges) if v in edge], default=0)
               for v in range(3))
    truth = np.array([np.sign(scores[a].sum() - scores[b].sum()) for a, b in edges])
    result = record_stop(cost, decisions, truth, n)
    result["edge_prefixes"] = prefix
    return result


def one_case(scenario, repeat):
    actual, prior, correlated = SCENARIOS[scenario]
    seed = seed_for(scenario, repeat)
    rng = np.random.default_rng(seed)
    uniforms = rng.random((1 if correlated else 3, N))
    scores = (uniforms < np.asarray(actual)[:, None]).astype(int)
    cells = run_cells(scores, prior, seed ^ 0xC0FFEE)
    order = np.random.default_rng(seed ^ 0x22).permutation(N)
    for graph, ids in GRAPHS.items():
        cells["stops"][graph]["stage22"] = stage22(scores, ids, order)
    return {"scenario": scenario, "repeat": repeat, "seed": seed,
            "scores": scores.tolist(), "stage22_order": order.tolist(), **cells}


def summarize(cases, repeats=REPEATS):
    result = {}
    rng = np.random.default_rng(20261025)
    for scenario in SCENARIOS:
        records = [c for c in cases if c["scenario"] == scenario]
        if len(records) != repeats:
            raise ValueError("Missing repeats")
        result[scenario] = {}
        for graph in GRAPHS:
            costs = {}
            group = {}
            for method in METHODS:
                rows = [c["stops"][graph][method] for c in records]
                costs[method] = np.array([r["charged"] for r in rows])
                group[method] = {
                    "mean_paid": float(np.mean([r["paid"] for r in rows])),
                    "mean_charged": float(costs[method].mean()),
                    "correct_completions": sum(r["correct_completion"] for r in rows),
                    "wrong_paths": sum(r["wrong"] for r in rows),
                }
            ids = rng.integers(repeats, size=(10000, repeats))
            comparisons = {}
            for control in METHODS[1:]:
                candidate, base = costs["joint_order"], costs[control]
                boot = 1 - candidate[ids].mean(axis=1) / base[ids].mean(axis=1)
                comparisons[control] = {
                    "relative_saving": float(1 - candidate.mean() / base.mean()),
                    "paired_bootstrap_95": np.quantile(boot, [.025, .975]).tolist()}
            group["comparisons"] = comparisons
            result[scenario][graph] = group
    no_errors = all(result[s][g]["joint_order"]["wrong_paths"] == 0
                    for s in SCENARIOS for g in GRAPHS)
    aligned = all(result[s][g]["comparisons"][c]["paired_bootstrap_95"][0] > 0
                  for s in ("independent_strong", "independent_moderate")
                  for g in GRAPHS for c in ("exact_pair_closure", "stage22"))
    reversed_ok = all(result["reversed"][g]["comparisons"][c]["relative_saving"] >= -.10
                      for g in GRAPHS for c in ("exact_pair_closure", "stage22"))
    result["expansion_gate"] = bool(no_errors and aligned and reversed_ok)
    result["numerical"] = {
        "unit_fallbacks": sum(c["unit_fallbacks"] for c in cases),
        "solver_failed_status": sum(c["solver_failed_status"] for c in cases)}
    return result


def run(output, repeats=REPEATS):
    output = Path(output)
    if repeats < 1 or output.exists():
        raise ValueError("Positive repeats and a new output directory required")
    cases = []
    for scenario in SCENARIOS:
        for repeat in range(repeats):
            cases.append(one_case(scenario, repeat))
        print("finished", scenario, repeats, flush=True)
    summary = summarize(cases, repeats)
    output.mkdir(parents=True)
    (output / "cases.json").write_text(json.dumps(cases, separators=(",", ":")) + "\n")
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (output / "metadata.json").write_text(json.dumps({
        "repeats": repeats, "items": N, "systems": 3, "alpha": ALPHA,
        "protocol_sha256": hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest(),
        "numpy": np.__version__, "scipy": scipy.__version__,
        "status": "synthetic mechanism screen; no new theorem or human evidence"
    }, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=REPEATS)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repeats), indent=2))
