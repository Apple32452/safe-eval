"""Replay fresh fixed matrices and audit predictable q decisions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from adaptive_probe import SCENARIOS, QS, choose_q, matched_stage22_cost


def audit(results):
    summary = {}
    repeats = len(results["aligned_strong"]["cases"])
    n = 32
    for name, (true_a, true_b, pa, pb) in SCENARIOS.items():
        costs = {k: [] for k in ("full", "fixed_half", "adaptive", "stage22")}
        choices = {str(q): 0 for q in QS}
        fallback_count = 0
        for rep, case in enumerate(results[name]["cases"]):
            rng = np.random.default_rng(20261025 + rep + 100 * len(name))
            scores = (rng.random((2, n)) < np.array([[true_a], [true_b]])).astype(np.int8)
            if case["true_gap"] != int(scores[0].sum() - scores[1].sum()):
                raise AssertionError("Target reconstruction disagrees with saved gap")
            truth = int(np.sign(case["true_gap"]))
            for method in ("full", "fixed_half", "adaptive"):
                row = case["methods"][method]
                bought = set()
                seen = np.zeros_like(scores, dtype=bool)
                known = np.zeros_like(scores)
                for event in row["path"]:
                    item, buy_a, buy_b = event[:3]
                    if method == "adaptive":
                        q = event[3]
                        selected, design, factors, fallback = choose_q(seen, known, pa, pb)
                        if not np.isclose(selected, q):
                            raise AssertionError("Saved q uses the wrong history")
                        worst, _ = design.worst_null(factors, 1)
                        if worst > 1 + 1e-9:
                            raise AssertionError("Adaptive positive null constraint violated")
                        choices[str(q)] += 1
                    for v, selected in ((0, buy_a), (1, buy_b)):
                        if selected:
                            if (v, item) in bought:
                                raise AssertionError("Purchased a score twice")
                            bought.add((v, item))
                            seen[v, item] = True
                            known[v, item] = scores[v, item]
                if len(bought) != row["cost"] or row["decision"] != truth or row["wrong"]:
                    raise AssertionError("Incorrect cost or completed sign")
                fallback_count += row["fallbacks"]
                costs[method].append(row["cost"])
            prefix = [i for i, _, _ in case["methods"]["full"]["path"]]
            order = prefix + [i for i in range(n) if i not in prefix]
            control = matched_stage22_cost(scores, np.array([[0, 1]], dtype=np.int16),
                                           order, np.random.default_rng(15519 + rep))
            if control != case["stage22"]:
                raise AssertionError("Stage 22 control disagrees with replay")
            costs["stage22"].append(control)
        means = {k: float(np.mean(v)) for k, v in costs.items()}
        if any(not np.isclose(means[k], results[name]["mean_cost"][k]) for k in means):
            raise AssertionError("Saved means disagree with costs")
        rng = np.random.default_rng(1515 + len(name))
        paired = {}
        for control in ("full", "fixed_half"):
            diff = np.array(costs["adaptive"]) - np.array(costs[control])
            bootstrap = np.mean(diff[rng.integers(0, repeats, (3000, repeats))], axis=1)
            paired[control] = dict(mean=float(diff.mean()),
                                   descriptive_ci95=[float(v) for v in np.quantile(
                                       bootstrap, [.025, .975])],
                                   percent=100 * (means["adaptive"] / means[control] - 1))
        summary[name] = dict(mean_cost=means, q_choices=choices,
                             optimizer_fallbacks=fallback_count, adaptive_vs=paired)
    gate = (all(summary[name]["adaptive_vs"][control]["percent"] <= -10
                for name in ("aligned_strong", "aligned_moderate")
                for control in ("full", "fixed_half")) and
            summary["shifted_opposite"]["adaptive_vs"]["full"]["percent"] <= 10)
    return dict(repeats=repeats, summary=summary, gate_pass=bool(gate))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(json.loads(args.input.read_text())), indent=2))
