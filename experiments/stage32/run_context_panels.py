"""Synthetic five-way panel-context diagnostic for a fixed pairwise target."""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


PANELS = (("A", "B", "C", "D", "E"), ("A", "B", "F", "G", "H"))
TARGET_PROB = (0.25, 0.75)
WIN_PROB = (0.90, 0.10)
RHO = (0.10, 0.25, 0.50, 0.80)
ALPHA = 0.05
SEED = 20261022
METHODS = ("target_random", "adaptive_naive", "adaptive_ipw")


def target_mean() -> float:
    return sum(p * (2 * w - 1) for p, w in zip(TARGET_PROB, WIN_PROB))


def adaptive_g_probability(previous_sign: int) -> float:
    if previous_sign not in (-1, 1):
        raise ValueError("previous_sign must be -1 or +1")
    return 0.9 if previous_sign == 1 else 0.8


def ranking(panel_index: int, judge_uniform: float) -> tuple[str, ...]:
    if panel_index not in (0, 1) or not 0 <= judge_uniform < 1:
        raise ValueError("invalid panel index or latent judgment")
    panel = PANELS[panel_index]
    first, second = ("A", "B") if judge_uniform < WIN_PROB[panel_index] else ("B", "A")
    return (first, second, *panel[2:])


def pair_sign(full_ranking: tuple[str, ...]) -> int:
    return 1 if full_ranking.index("A") < full_ranking.index("B") else -1


def corrected_signal(panel_index: int, sign: int, q_g: float) -> tuple[float, float]:
    if panel_index not in (0, 1) or sign not in (-1, 1) or not 0 < q_g < 1:
        raise ValueError("invalid propensity or panel judgment")
    q = (q_g, 1 - q_g)
    bound = max(p / r for p, r in zip(TARGET_PROB, q))
    return TARGET_PROB[panel_index] * sign / q[panel_index], bound


def conditional_expectation(q_g: float, corrected: bool) -> float:
    """Exact enumeration of panels and two A/B rankings, for tests/audit."""
    if not 0 < q_g < 1:
        raise ValueError("both panels need positive probability")
    q = (q_g, 1 - q_g)
    return sum(q[s] * (WIN_PROB[s] * (1 if not corrected else TARGET_PROB[s] / q[s])
                       + (1 - WIN_PROB[s]) * (-1 if not corrected else -TARGET_PROB[s] / q[s]))
               for s in (0, 1))


def one_trajectory(panel_uniforms: np.ndarray, judge_uniforms: np.ndarray,
                   method: str) -> dict:
    if method not in METHODS:
        raise ValueError(method)
    if panel_uniforms.ndim != 1 or judge_uniforms.shape != panel_uniforms.shape:
        raise ValueError("matched one-dimensional random-number streams required")
    if not np.all((0 <= panel_uniforms) & (panel_uniforms < 1)) or not np.all(
            (0 <= judge_uniforms) & (judge_uniforms < 1)):
        raise ValueError("random-number streams must be uniform variates in [0,1)")
    log_wealth = np.zeros((2, len(RHO)), dtype=float)
    threshold = math.log(2 / ALPHA)
    previous = 1
    g_panels = 0
    decision = 0
    for t, (panel_u, judge_u) in enumerate(zip(panel_uniforms, judge_uniforms), start=1):
        q_g = TARGET_PROB[0] if method == "target_random" else adaptive_g_probability(previous)
        panel = 0 if panel_u < q_g else 1
        g_panels += int(panel == 0)
        sign = pair_sign(ranking(panel, float(judge_u)))
        if method == "adaptive_ipw":
            signal, bound = corrected_signal(panel, sign, q_g)
        else:
            signal, bound = float(sign), 1.0
        scaled = signal / bound
        # Every factor is strictly positive since max(rho) < 1 and |scaled| <= 1.
        for k, rho in enumerate(RHO):
            log_wealth[0, k] += math.log1p(rho * scaled)
            log_wealth[1, k] += math.log1p(-rho * scaled)
        mixture = np.logaddexp.reduce(log_wealth, axis=1) - math.log(len(RHO))
        if mixture[0] >= threshold and mixture[1] >= threshold:
            raise AssertionError("contradictory direction declarations")
        previous = sign
        if mixture[0] >= threshold:
            decision = 1
        elif mixture[1] >= threshold:
            decision = -1
        if decision:
            break
    else:
        t = len(panel_uniforms)
    return {"method": method, "panels": t, "g_panels": g_panels,
            "decision": decision, "wrong": int(decision == 1),
            "correct": int(decision == -1), "abstained": int(decision == 0)}


def experiment(repeats: int, cap: int) -> list[dict]:
    if repeats < 1 or cap < 1:
        raise ValueError("repeats and cap must be positive")
    rows = []
    for repeat in range(repeats):
        rng = np.random.default_rng(SEED + repeat)
        panel_uniforms, judge_uniforms = rng.random((2, cap))
        for method in METHODS:
            rows.append({"repeat": repeat, **one_trajectory(panel_uniforms, judge_uniforms, method)})
    return rows


def summarize(rows: list[dict], repeats: int) -> dict:
    summary = {}
    for method in METHODS:
        subset = [r for r in rows if r["method"] == method]
        if len(subset) != repeats:
            raise ValueError("missing repeat/method rows")
        correct = [r["panels"] for r in subset if r["correct"]]
        summary[method] = {
            "wrong": sum(r["wrong"] for r in subset),
            "correct": len(correct),
            "abstained": sum(r["abstained"] for r in subset),
            "mean_capped_panel_tasks": float(np.mean([r["panels"] for r in subset])),
            "mean_panels_given_correct": float(np.mean(correct)) if correct else None,
            "fraction_g_panels": sum(r["g_panels"] for r in subset) /
                                 sum(r["panels"] for r in subset),
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=500)
    parser.add_argument("--cap", type=int, default=2000)
    parser.add_argument("--output", type=Path, default=Path("results/stage32_development"))
    args = parser.parse_args()
    rows = experiment(args.repeats, args.cap)
    summary = summarize(rows, args.repeats)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "replicates.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (args.output / "summary.json").write_text(json.dumps({
        "seed": SEED, "repeats": args.repeats, "cap": args.cap,
        "alpha_familywise": ALPHA, "stakes": RHO, "target_pi": TARGET_PROB,
        "conditional_a_win_prob": WIN_PROB, "target_mean_a_minus_b": target_mean(),
        "summary": summary,
    }, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    print("Results:", args.output)


if __name__ == "__main__":
    main()
