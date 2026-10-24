"""Frozen synthetic screen of a uniform finite-pool cell permutation."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "stage17"))
sys.path.insert(0, str(ROOT / "experiments" / "stage22"))
from continuous_engine import RHOS, make_paths
from run_stage22 import simulate_graph, star_edges

MASTER = 20261024
ALPHA = 0.05
REPEATS = 50
ITEMS = 128
SCENARIOS = {
    "independent_easy": ([.9, .1, .2, .4, .6], False),
    "independent_weak": ([.6, .5, .48, .45, .42], False),
    "shared_easy": ([.9, .1, .2, .4, .6], True),
    "independent_close": ([.50, .52, .48, .53, .47], False),
}


def seed(*parts):
    digest = hashlib.sha256("|".join(map(str, (MASTER, *parts))).encode()).digest()
    return int.from_bytes(digest[:8], "little")


def matrix(scenario, repeat, items=ITEMS):
    rates, shared = SCENARIOS[scenario]
    rng = np.random.default_rng(seed("scores", scenario, repeat))
    draws = rng.random((1 if shared else len(rates), items))
    return (draws < np.asarray(rates)[:, None]).astype(float)


def pair_control(scores, edges, scenario, repeat):
    systems, items = scores.shape
    rng = np.random.default_rng(seed("stage22", scenario, repeat))
    item_order = rng.permutation(items)
    permutations = np.broadcast_to(item_order, (len(edges), 1, items)).copy()
    events, _ = make_paths(scores, edges, permutations, 2 * len(edges) / ALPHA)
    priority = rng.permutation(systems * items).reshape(scores.shape)
    record = simulate_graph(scores, edges, permutations[:, 0],
                            events[:, 0], priority, "star_pruned", fractions=(1.,))
    return int(record["completion_cost"]), record["decision"].tolist()


def cell_permutation(scores, edges, order, alpha=ALPHA):
    """Advance each unresolved pair through its fixed, uniform signed-cell path.

    A global uniform permutation ensures that the restriction to any pair is
    itself a uniform permutation. All incident unresolved pairs see every
    purchased endpoint cell in that order. A cached score is never charged
    twice. In particular, no outcome-dependent item order is constructed.
    """
    scores = np.asarray(scores, dtype=float)
    edges = np.asarray(edges, dtype=int)
    systems, items = scores.shape
    if scores.ndim != 2 or items < 2 or not np.isfinite(scores).all():
        raise ValueError("Expected a finite score matrix with at least two items")
    if np.any((scores < 0) | (scores > 1)):
        raise ValueError("Scores must be in [0,1]")
    if edges.ndim != 2 or edges.shape[1] != 2 or np.any(edges[:, 0] >= edges[:, 1]):
        raise ValueError("Expected canonical, ordered pair endpoints")
    if np.any(edges < 0) or np.any(edges >= systems):
        raise ValueError("Endpoint outside the score matrix")
    order = np.asarray(order, dtype=int)
    if (order.shape != (systems * items,) or
            not np.array_equal(np.sort(order), np.arange(systems * items))):
        raise ValueError("Expected a complete uniform cell permutation")
    if not 0 < alpha < 1:
        raise ValueError("Invalid family error level")

    threshold = 2 * len(edges) / alpha
    log_threshold = np.log(threshold)
    wealth = np.zeros((2, len(edges), len(RHOS)))
    partial_sums = np.zeros(len(edges))
    prefix = np.zeros(len(edges), dtype=int)
    decisions = np.full(len(edges), 2, dtype=int)
    purchased = []
    seen = np.zeros_like(scores, dtype=bool)
    incident = [[e for e, (a, b) in enumerate(edges) if v in (a, b)]
                for v in range(systems)]

    for flat in order:
        v, i = divmod(int(flat), items)
        active = [e for e in incident[v] if decisions[e] == 2]
        if not active:
            continue
        assert not seen[v, i]
        seen[v, i] = True
        purchased.append((v, i))
        for e in active:
            a, b = edges[e]
            sign = 1 if v == a else -1
            x = sign * scores[v, i]
            remaining = 2 * items - prefix[e]
            for d, directed in enumerate((x, -x)):
                observed = partial_sums[e] if d == 0 else -partial_sums[e]
                center = -observed / remaining
                if center > -1:
                    factor = 1 + RHOS * (directed - center) / (1 + center)
                    if np.min(factor) <= 0:
                        raise AssertionError("Invalid bounded betting factor")
                    wealth[d, e] += np.log(factor)
            partial_sums[e] += x
            prefix[e] += 1
            remaining -= 1
            s = partial_sums[e]
            deterministic = 1 if s > remaining else -1 if s < -remaining else 2
            if remaining == 0:
                decisions[e] = int(np.sign(s))
            elif deterministic != 2:
                decisions[e] = deterministic
            else:
                # The stake mixture is fixed before any target outcome.
                peak = np.max(wealth[:, e, :], axis=1)
                mixture = peak + np.log(np.mean(
                    np.exp(wealth[:, e, :] - peak[:, None]), axis=1))
                crossed = mixture >= log_threshold
                if crossed[0] != crossed[1]:
                    decisions[e] = 1 if crossed[0] else -1
        if np.all(decisions != 2):
            break

    if np.any(decisions == 2) or len(purchased) != len(set(purchased)):
        raise AssertionError("Incomplete conclusions or repeated charges")
    truth = np.sign(scores[edges[:, 0]].sum(1) - scores[edges[:, 1]].sum(1))
    return {"labels": len(purchased), "decision": decisions.tolist(),
            "truth": truth.astype(int).tolist(), "purchased": purchased,
            "prefix": prefix.tolist()}


def run(output, repeats=REPEATS):
    if not 0 < repeats <= REPEATS:
        raise ValueError("Only the predeclared first 1..50 repeats are allowed")
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for scenario in SCENARIOS:
        for repeat in range(repeats):
            scores = matrix(scenario, repeat)
            edges = star_edges(len(scores), 0)
            baseline, old_decision = pair_control(scores, edges, scenario, repeat)
            rng = np.random.default_rng(seed("cells", scenario, repeat))
            new = cell_permutation(scores, edges, rng.permutation(scores.size))
            if new["decision"] != old_decision or new["decision"] != new["truth"]:
                raise AssertionError("Full comparison decisions disagree")
            rows.append(dict(scenario=scenario, repeat=repeat, stage22=baseline,
                             cells=new["labels"], truth=json.dumps(new["truth"]),
                             decision=json.dumps(new["decision"])))
    with (destination / "replicates.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    digest = hashlib.sha256((HERE / "PROTOCOL.md").read_bytes()).hexdigest()
    (destination / "metadata.json").write_text(json.dumps(dict(
        protocol_sha256=digest, master=MASTER, repeats=repeats, alpha=ALPHA,
        items=ITEMS, scenarios=SCENARIOS), indent=2) + "\n")
    summary = {}
    for scenario in SCENARIOS:
        subset = [row for row in rows if row["scenario"] == scenario]
        base = np.mean([row["stage22"] for row in subset])
        cost = np.mean([row["cells"] for row in subset])
        summary[scenario] = dict(stage22=base, cells=cost,
                                 saving_percent=100 * (base - cost) / base,
                                 passed=bool(cost <= .9 * base))
    summary["gate_pass"] = sum(x["passed"] for x in summary.values()) >= 3
    (destination / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="results/cell_permutation_probe")
    parser.add_argument("--repeats", type=int, default=REPEATS)
    args = parser.parse_args()
    print(json.dumps(run(args.output, args.repeats), indent=2))
