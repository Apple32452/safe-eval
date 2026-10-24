"""Frozen two-context correction screen; simulated units are not human time."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MASTER = 20261024
REPEATS = 100
CAP = 2000
PILOT = 20
ALPHA = .05
PI = (.5, .5)
RHOS = (.10, .25, .50, .80)
METHODS = ("target_random", "adaptive_ipw", "adaptive_augmented")
SCENARIOS = {
    "unequal_variance": ((.50, .95), (1, 1)),
    "unequal_duration": ((.80, .80), (1, 3)),
    "mixed_variance": ((.98, .55), (1, 1)),
    "homogeneous": ((.80, .80), (1, 1)),
    "opposed_tie": ((.90, .10), (1, 1)),
}
GATE_SCENARIOS = ("unequal_variance", "unequal_duration", "mixed_variance")


def seed(scenario, repeat):
    value = f"{MASTER}|{scenario}|{repeat}".encode()
    return int.from_bytes(hashlib.sha256(value).digest()[:8], "little")


def predictions(counts, sums):
    return tuple(float(sums[s]) / (int(counts[s]) + 4) for s in (0, 1))


def proposal(counts, sums, duration):
    m = predictions(counts, sums)
    weights = [PI[s] * math.sqrt(max(.05, 1 - m[s] ** 2)) /
               math.sqrt(duration[s]) for s in (0, 1)]
    total = sum(weights)
    return tuple(.3 * PI[s] + .7 * weights[s] / total for s in (0, 1))


def signal_and_bounds(method, chosen, y, q, m):
    if (method not in METHODS or chosen not in (0, 1) or y not in (-1, 1)
            or len(q) != 2 or not all(x > 0 for x in q)
            or not math.isclose(sum(q), 1., abs_tol=1e-12)):
        raise ValueError("Invalid correction input")
    if method == "target_random":
        if not all(math.isclose(q[s], PI[s], abs_tol=1e-12) for s in (0, 1)):
            raise ValueError("Raw judgments require target-randomized panels")
        return float(y), -1., 1.
    if method == "adaptive_ipw":
        bound = max(PI[s] / q[s] for s in (0, 1))
        return PI[chosen] * y / q[chosen], -bound, bound
    base = sum(PI[s] * m[s] for s in (0, 1))
    signal = base + PI[chosen] * (y - m[chosen]) / q[chosen]
    low = min(base + PI[s] * (-1 - m[s]) / q[s] for s in (0, 1))
    high = max(base + PI[s] * (1 - m[s]) / q[s] for s in (0, 1))
    return signal, low, high


def conditional_mean(method, q, m, win_probs):
    return sum(q[s] * sum(prob * signal_and_bounds(
        method, s, y, q, m)[0] for prob, y in
        ((win_probs[s], 1), (1 - win_probs[s], -1))) for s in (0, 1))


def one_trajectory(panel_uniforms, judge_uniforms, method, win_probs, duration):
    if method not in METHODS or panel_uniforms.shape != judge_uniforms.shape:
        raise ValueError("Matched panel/judge streams required")
    if panel_uniforms.ndim != 1 or np.any(panel_uniforms < 0) or np.any(
            panel_uniforms >= 1) or np.any(judge_uniforms < 0) or np.any(
                judge_uniforms >= 1):
        raise ValueError("Latent uniforms must be in [0,1)")
    counts = [0, 0]
    sums = [0, 0]
    log_wealth = np.zeros((2, len(RHOS)), dtype=float)
    costs = 0
    decision = 0
    contradiction = 0
    threshold = math.log(2 / ALPHA)
    for t, (panel_u, judge_u) in enumerate(zip(panel_uniforms, judge_uniforms), 1):
        q = (PI if method == "target_random" or t <= PILOT else
             proposal(counts, sums, duration))
        m = predictions(counts, sums)
        chosen = 0 if panel_u < q[0] else 1
        y = 1 if judge_u < win_probs[chosen] else -1
        x, low, high = signal_and_bounds(method, chosen, y, q, m)
        if low > x + 1e-12 or x > high + 1e-12:
            raise AssertionError("Observed signal outside predictable bound")
        counts[chosen] += 1
        sums[chosen] += y
        costs += duration[chosen]
        for d, scale in enumerate((max(1., -low), max(1., high))):
            signed = x if d == 0 else -x
            for j, rho in enumerate(RHOS):
                factor = 1 + rho * signed / scale
                if factor < .2 - 1e-12:
                    raise AssertionError("Invalid e-factor")
                log_wealth[d, j] += math.log(factor)
        mixture = [float(np.logaddexp.reduce(log_wealth[d]) -
                         math.log(len(RHOS))) for d in (0, 1)]
        if t < PILOT:
            continue  # All methods pay for the complete prespecified pilot.
        if mixture[0] >= threshold and mixture[1] >= threshold:
            contradiction = 1
            break  # Ambiguous conflicting evidence: report no direction.
        if mixture[0] >= threshold:
            decision = 1
            break
        if mixture[1] >= threshold:
            decision = -1
            break
    else:
        t = len(panel_uniforms)
    theta = sum(PI[s] * (2 * win_probs[s] - 1) for s in (0, 1))
    truth = int(np.sign(theta)) if abs(theta) > 1e-12 else 0
    return dict(method=method, tasks=t, duration=costs, decision=decision,
                truth=truth, correct=int(decision != 0 and decision == truth),
                wrong=int(decision != 0 and decision != truth),
                abstained=int(decision == 0), contradiction=contradiction,
                p0_tasks=counts[0])


def summarize(rows):
    summary = {}
    for scenario in SCENARIOS:
        summary[scenario] = {}
        for method in METHODS:
            subset = [x for x in rows if x["scenario"] == scenario and
                      x["method"] == method]
            if len(subset) != REPEATS:
                raise AssertionError("Missing frozen repeat")
            correct_cost = [x["duration"] for x in subset if x["correct"]]
            summary[scenario][method] = dict(
                correct=len(correct_cost), wrong=sum(x["wrong"] for x in subset),
                abstained=sum(x["abstained"] for x in subset),
                mean_capped_duration=float(np.mean([x["duration"] for x in subset])),
                mean_completed_duration=(float(np.mean(correct_cost))
                                         if correct_cost else None),
                mean_capped_tasks=float(np.mean([x["tasks"] for x in subset])))
    passed = []
    for scenario in GATE_SCENARIOS:
        groups = summary[scenario]
        candidate = groups["adaptive_augmented"]
        controls = [groups[x] for x in METHODS[:2]]
        good = (all(candidate["correct"] >= b["correct"] for b in controls)
                and candidate["wrong"] == 0
                and candidate["mean_completed_duration"] is not None
                and all(b["mean_completed_duration"] is not None and
                        candidate["mean_completed_duration"] <=
                        .9 * b["mean_completed_duration"] for b in controls))
        passed.append(bool(good))
        summary[scenario]["gate_pass"] = bool(good)
    summary["overall_gate_pass"] = sum(passed) >= 2
    return summary


def run(output, repeats=REPEATS, cap=CAP):
    if repeats != REPEATS or cap != CAP:
        raise ValueError("Only the frozen 100-repeat/2000-task run is allowed")
    rows = []
    for scenario, (win_probs, duration) in SCENARIOS.items():
        for repeat in range(repeats):
            rng = np.random.default_rng(seed(scenario, repeat))
            panel_u, judge_u = rng.random((2, cap))
            for method in METHODS:
                rows.append(dict(scenario=scenario, repeat=repeat,
                                 **one_trajectory(panel_u, judge_u, method,
                                                  win_probs, duration)))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "replicates.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    record = dict(master=MASTER, repeats=REPEATS, cap=CAP, pilot=PILOT,
                  alpha=ALPHA, pi=PI, rhos=RHOS, scenarios=SCENARIOS,
                  protocol_sha256=hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest())
    (output / "metadata.json").write_text(json.dumps(record, indent=2) + "\n")
    summary = summarize(rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="experiments/panel_aware_gate/results_reference")
    args = parser.parse_args()
    print(json.dumps(run(args.output), indent=2))
