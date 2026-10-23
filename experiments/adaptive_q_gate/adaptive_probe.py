"""Predictable q selection with exact conditional fixed-pool e-factors."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "exact_sequential_probe"))
sys.path.insert(0, str(ROOT / "experiments" / "block_gate"))
from sequential_probe import Design, certificate, factor  # noqa: E402
from block_probe import matched_stage22_cost  # noqa: E402

QS = (.25, .5, .75, 1.)
SCENARIOS = {"aligned_strong": (.9, .1, .9, .1),
             "aligned_moderate": (.7, .3, .7, .3),
             "shifted_opposite": (.3, .7, .9, .1)}


def choose_q(seen, known, pa, pb):
    """Return an exact factor and q using only the pre-purchase history."""
    candidates = []
    for q in QS:
        design = Design(seen, known, q, pa, pb)
        positive, fallback = factor(design, 1)
        both = int(np.count_nonzero(~seen[0] & ~seen[1]))
        price = 1 + q * both / len(design.eligible)
        growth = float(design.alt @ np.log(positive))
        candidates.append((growth / price, q, design, positive, fallback))
    _, q, design, positive, fallback = max(candidates, key=lambda row: (row[0], row[1]))
    return q, design, positive, fallback


def adaptive_certificate(scores, pa, pb, seed, alpha=.05):
    scores = np.asarray(scores, dtype=np.int8)
    if scores.ndim != 2 or scores.shape[0] != 2 or not np.isin(scores, (0, 1)).all():
        raise ValueError("Expected two binary score rows")
    n = scores.shape[1]
    seen = np.zeros_like(scores, dtype=bool)
    known = np.zeros_like(scores)
    wealth = np.zeros(2)
    rng = np.random.default_rng(seed)
    path, fallbacks = [], 0
    decision = None
    while decision is None:
        lower = int(known[0].sum() - known[1].sum() - np.count_nonzero(~seen[1]))
        upper = int(known[0].sum() - known[1].sum() + np.count_nonzero(~seen[0]))
        if lower > 0 or upper < 0 or seen.all():
            decision = 1 if lower > 0 else -1 if upper < 0 else int(np.sign(
                known[0].sum() - known[1].sum()))
            break
        q, plus, fplus, plus_fallback = choose_q(seen, known, pa, pb)
        minus = Design(seen, known, q, 1 - pa, 1 - pb)
        fminus, minus_fallback = factor(minus, -1)
        fallbacks += int(plus_fallback) + int(minus_fallback)
        i = int(rng.choice(plus.eligible))
        a_unknown, b_unknown = ~seen[:, i]
        buy_a = bool(a_unknown)
        buy_b = bool(b_unknown and (not a_unknown or rng.random() < q))
        a, b = (int(scores[0, i]) if buy_a else -1,
                int(scores[1, i]) if buy_b else -1)
        missing = bool(b_unknown and not buy_b)
        wealth[0] += np.log(fplus[plus.event(i, a, b, missing)])
        wealth[1] += np.log(fminus[minus.event(i, a, b, missing)])
        if buy_a:
            seen[0, i], known[0, i] = True, a
        if buy_b:
            seen[1, i], known[1, i] = True, b
        path.append((i, int(buy_a), int(buy_b), q))
        lower = int(known[0].sum() - known[1].sum() - np.count_nonzero(~seen[1]))
        upper = int(known[0].sum() - known[1].sum() + np.count_nonzero(~seen[0]))
        threshold = np.log(2 / alpha)
        if lower > 0:
            decision = 1
        elif upper < 0:
            decision = -1
        elif seen.all():
            decision = int(np.sign(known[0].sum() - known[1].sum()))
        elif wealth[0] >= threshold and wealth[1] < threshold:
            decision = 1
        elif wealth[1] >= threshold and wealth[0] < threshold:
            decision = -1
        if len(path) > 2 * n:
            raise AssertionError("Acquisition did not terminate")
    truth = int(np.sign(scores[0].sum() - scores[1].sum()))
    return dict(cost=int(seen.sum()), decision=int(decision), truth=truth,
                wrong=bool(decision != truth), fallbacks=fallbacks, path=path)


def run(repeats=12, items=32):
    result = {}
    for name, (true_a, true_b, pa, pb) in SCENARIOS.items():
        cases = []
        for rep in range(repeats):
            rng = np.random.default_rng(20261025 + rep + 100 * len(name))
            scores = (rng.random((2, items)) < np.array([[true_a], [true_b]])).astype(np.int8)
            seed = 87119 + rep
            methods = {"full": certificate(scores, pa, pb, 1, seed),
                       "fixed_half": certificate(scores, pa, pb, .5, seed),
                       "adaptive": adaptive_certificate(scores, pa, pb, seed)}
            prefix = [i for i, _, _ in methods["full"]["path"]]
            order = prefix + [i for i in range(items) if i not in prefix]
            stage22 = matched_stage22_cost(scores, np.array([[0, 1]], dtype=np.int16),
                                          order, np.random.default_rng(15519 + rep))
            if any(m["wrong"] for m in methods.values()):
                raise AssertionError("Wrong completed fixed-pool sign")
            cases.append(dict(methods=methods, stage22=int(stage22),
                              true_gap=int(scores[0].sum() - scores[1].sum())))
        means = {key: float(np.mean([case["methods"][key]["cost"] for case in cases]))
                 for key in ("full", "fixed_half", "adaptive")}
        means["stage22"] = float(np.mean([case["stage22"] for case in cases]))
        result[name] = dict(mean_cost=means, cases=cases)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=12)
    parser.add_argument("--items", type=int, default=32)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = run(args.repeats, args.items)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, separators=(",", ":")) + "\n")
    for name, row in output.items():
        print(name, row["mean_cost"], flush=True)
