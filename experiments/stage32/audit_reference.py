"""Independently check saved Stage 32 rows against the reported aggregate."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def audit(directory: Path) -> int:
    info = json.loads((directory / "summary.json").read_text())
    with (directory / "replicates.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    repeats = info["repeats"]
    cap = info["cap"]
    names = ("target_random", "adaptive_naive", "adaptive_ipw")
    if len(rows) != repeats * len(names) or set(info["summary"]) != set(names):
        raise AssertionError("missing methods or repeats")
    if info["target_pi"] != [0.25, 0.75] or info["conditional_a_win_prob"] != [0.9, 0.1]:
        raise AssertionError("not the frozen panel model")
    if abs(info["target_mean_a_minus_b"] + 0.4) > 1e-12:
        raise AssertionError("wrong target sign")
    for repeat in range(repeats):
        if {r["method"] for r in rows if int(r["repeat"]) == repeat} != set(names):
            raise AssertionError("duplicate or missing method")
    for name in names:
        group = [r for r in rows if r["method"] == name]
        tasks = [int(r["panels"]) for r in group]
        greens = [int(r["g_panels"]) for r in group]
        decisions = [int(r["decision"]) for r in group]
        if any(not 1 <= n <= cap or not 0 <= g <= n for n, g in zip(tasks, greens)):
            raise AssertionError("invalid task or panel count")
        if any(d not in (-1, 0, 1) for d in decisions):
            raise AssertionError("invalid decision")
        if any(int(r["wrong"]) != (d == 1) or
               int(r["correct"]) != (d == -1) or
               int(r["abstained"]) != (d == 0)
               for r, d in zip(group, decisions)):
            raise AssertionError("wrong outcome label")
        if any(d == 0 and n != cap for d, n in zip(decisions, tasks)):
            raise AssertionError("abstained before cap")
        reported = info["summary"][name]
        correct_tasks = [n for d, n in zip(decisions, tasks) if d == -1]
        checks = {
            "wrong": sum(d == 1 for d in decisions),
            "correct": len(correct_tasks),
            "abstained": sum(d == 0 for d in decisions),
            "mean_capped_panel_tasks": sum(tasks) / repeats,
            "mean_panels_given_correct": (sum(correct_tasks) / len(correct_tasks)
                                          if correct_tasks else None),
            "fraction_g_panels": sum(greens) / sum(tasks),
        }
        for key, observed in checks.items():
            expected = reported[key]
            if observed is None or expected is None:
                if observed is not expected:
                    raise AssertionError((name, key, observed, expected))
            elif abs(observed - expected) > 1e-12:
                raise AssertionError((name, key, observed, expected))
    return len(rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=Path("experiments/stage32/results_reference"))
    args = parser.parse_args()
    print(f"Audited {audit(args.input)} Stage 32 trajectories.")
