"""Post-result audit of requested-edge closure and exact-pair Bonferroni."""
import argparse
import json
from pathlib import Path

import numpy as np

from joint_order import DIRECTED, IMPLIED, PAIRS, decide, possible_orders, state_update
from run_study import ALPHA, GRAPHS, N, SCENARIOS, record_stop

CONTROLS = ("requested_closure", "requested_bonferroni")


def one(case):
    scores = np.array(case["scores"], int)
    prior = SCENARIOS[case["scenario"]][1]
    rng = np.random.default_rng(case["seed"] ^ 0xC0FFEE)
    s, m = np.zeros(3, int), np.full(3, N)
    unseen = [list(range(N)) for _ in range(3)]
    logs = np.zeros(6)
    excluded = {g: np.zeros(13, bool) for g in GRAPHS}
    decisions = {(g, c): np.full(3, 2, int) for g in GRAPHS for c in CONTROLS}
    stopped = {g: {} for g in GRAPHS}
    truth = np.array([np.sign(scores[a].sum()-scores[b].sum()) for a, b in PAIRS], int)
    chosen = set()
    for t in range(3*N):
        update = state_update(tuple(s), tuple(m), prior, N)
        v = int(rng.choice(3, p=update["q"]))
        item = unseen[v].pop(int(rng.integers(len(unseen[v]))))
        y = int(scores[v, item])
        if (v, item) in chosen:
            raise AssertionError("Repeated cell")
        chosen.add((v, item))
        if t < len(case["trace"]):
            old = case["trace"][t]
            if (v, item, y) != (old["row"], old["item"], old["value"]) or not np.allclose(update["q"], old["q"]):
                raise AssertionError("Changed common acquisition prefix")
        logs += np.log(update["pair"][:, 2*v+y])
        s[v] += y; m[v] -= 1
        for graph, edge_ids in GRAPHS.items():
            needed = {PAIRS[e] for e in edge_ids}
            for w, ids in enumerate(IMPLIED):
                use = [i for i in ids if tuple(sorted(DIRECTED[i])) in needed]
                pooled = np.logaddexp.reduce(logs[use]) - np.log(len(use))
                excluded[graph][w] |= pooled >= np.log(1/ALPHA)
            excluded[graph] |= ~possible_orders(s, m)
            for control in CONTROLS:
                previous = decisions[graph, control]
                if control == "requested_closure":
                    current = decide(s, m, excluded[graph], previous)
                else:
                    # All orders removed forces decide() to apply only its
                    # deterministic completion bounds, never statistical logic.
                    current = decide(s, m, np.ones(13, bool), previous)
                    threshold = np.log(2*len(edge_ids)/ALPHA)
                    for edge in edge_ids:
                        if current[edge] != 2:
                            continue
                        a, b = PAIRS[edge]
                        positive = logs[DIRECTED.index((a, b))] >= threshold
                        negative = logs[DIRECTED.index((b, a))] >= threshold
                        if positive != negative:
                            current[edge] = 1 if positive else -1
                decisions[graph, control] = current
                if control not in stopped[graph] and np.all(current[list(edge_ids)] != 2):
                    stopped[graph][control] = record_stop(
                        t+1, current[list(edge_ids)], truth[list(edge_ids)], N)
        if all(len(v) == 2 for v in stopped.values()):
            break
    if not all(len(v) == 2 for v in stopped.values()):
        raise AssertionError("Late control failed full evaluation")
    return {"scenario": case["scenario"], "repeat": case["repeat"],
            "stops": stopped, "extra_prefix_cells": max(0, t+1-len(case["trace"]))}


def run(folder):
    cases = json.loads((folder/"cases.json").read_text())
    rows = [one(case) for case in cases]
    result = {}
    rng = np.random.default_rng(20261026)
    for scenario in SCENARIOS:
        original = sorted([c for c in cases if c["scenario"] == scenario], key=lambda c: c["repeat"])
        late = sorted([r for r in rows if r["scenario"] == scenario], key=lambda r: r["repeat"])
        result[scenario] = {}
        for graph in GRAPHS:
            result[scenario][graph] = {}
            candidate = np.array([c["stops"][graph]["joint_order"]["charged"] for c in original])
            ids = rng.integers(len(late), size=(10000, len(late)))
            for control in CONTROLS:
                group = [r["stops"][graph][control] for r in late]
                base = np.array([r["charged"] for r in group])
                boot = 1-candidate[ids].mean(axis=1)/base[ids].mean(axis=1)
                result[scenario][graph][control] = {
                    "mean_paid": float(np.mean([r["paid"] for r in group])),
                    "mean_charged": float(base.mean()),
                    "wrong_paths": sum(r["wrong"] for r in group),
                    "candidate_relative_saving": float(1-candidate.mean()/base.mean()),
                    "paired_bootstrap_95": np.quantile(boot, [.025, .975]).tolist()}
    return {"status": "post-result control audit", "summary": result,
            "rows": rows, "extra_cells_replayed": sum(r["extra_prefix_cells"] for r in rows),
            "frozen_expansion_gate_changed": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.input)
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
