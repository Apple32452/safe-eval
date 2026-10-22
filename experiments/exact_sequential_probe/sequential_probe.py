"""Development-only two-system sequential exact conditional e-factors.

Target scores are a fixed finite population. Randomness is acquisition only.
Predictions, q, and optimizer output are computed before each new purchase.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "experiments" / "block_gate"))
from block_probe import matched_stage22_cost  # noqa: E402


def bernoulli(value, p):
    return p if value else 1 - p


class Design:
    """Grouped event factors and per-item fixed-completion coefficients."""

    def __init__(self, seen, known, q, pa, pb):
        seen = np.asarray(seen, dtype=bool)
        known = np.asarray(known, dtype=np.int8)
        if seen.shape != known.shape or seen.shape[0] != 2 or not 0 < q <= 1:
            raise ValueError("Invalid fixed-pool state")
        self.seen, self.known, self.q = seen.copy(), known.copy(), q
        self.n = seen.shape[1]
        self.eligible = np.flatnonzero(~np.all(seen, axis=0))
        if not len(self.eligible):
            raise ValueError("No unpurchased score")
        self.groups = {}
        self.local = np.zeros((self.n, 2, 2, 14), dtype=float)
        self.alt = np.zeros(14, dtype=float)
        self.event_group = {}
        p_item = 1 / len(self.eligible)

        def add(i, a, b, missing, coefficient, alternative, group):
            idx = self.groups.setdefault(group, len(self.groups))
            self.local[i, a, b, idx] += coefficient
            self.alt[idx] += alternative
            self.event_group[i, a if not self.seen[0, i] else -1,
                             -1 if self.seen[1, i] or missing else b,
                             missing] = idx

        for i in self.eligible:
            a_known, b_known = seen[:, i]
            for a in (0, 1):
                for b in (0, 1):
                    if a_known and a != known[0, i] or b_known and b != known[1, i]:
                        continue
                    qa = 1 if a_known else bernoulli(a, pa)
                    qb = 1 if b_known else bernoulli(b, pb)
                    if not a_known and not b_known:
                        if q < 1:
                            # Missing-B event is the same for both possible b;
                            # count its alternative probability only once.
                            add(i, a, b, True, p_item * (1 - q),
                                p_item * (1 - q) * qa * qb,
                                ("both", a, -1))
                        add(i, a, b, False, p_item * q,
                            p_item * q * qa * qb, ("both", a, b))
                    elif a_known and not b_known:
                        add(i, a, b, False, p_item, p_item * qb,
                            ("a_seen", int(a), b))
                    elif not a_known and b_known:
                        add(i, a, b, False, p_item, p_item * qa,
                            ("b_seen", a, int(b)))
        self.local = self.local[:, :, :, :len(self.groups)]
        self.alt = self.alt[:len(self.groups)]
        if not np.isclose(self.alt.sum(), 1):
            raise AssertionError("Alternative event probabilities do not sum to one")

    def row(self, completion):
        return self.local[np.arange(self.n), completion[0], completion[1]].sum(axis=0)

    def worst_null(self, factors, sign):
        """Maximize conditional expectation over compatible fixed nulls."""
        n = self.n
        dp = np.full(2 * n + 1, -np.inf)
        dp[n] = 0
        parents = np.full((n + 1, 2 * n + 1), -1, dtype=int)
        choices = np.zeros((n + 1, 2 * n + 1, 2), dtype=np.int8)
        for i in range(n):
            next_dp = np.full_like(dp, -np.inf)
            for prior in np.flatnonzero(np.isfinite(dp)):
                for a in (0, 1):
                    if self.seen[0, i] and self.known[0, i] != a:
                        continue
                    for b in (0, 1):
                        if self.seen[1, i] and self.known[1, i] != b:
                            continue
                        state = prior + a - b
                        candidate = dp[prior] + self.local[i, a, b] @ factors
                        if candidate > next_dp[state]:
                            next_dp[state] = candidate
                            parents[i + 1, state] = prior
                            choices[i + 1, state] = a, b
            dp = next_dp
        valid = np.arange(2 * n + 1) <= n if sign > 0 else np.arange(2 * n + 1) >= n
        state = int(np.argmax(np.where(valid, dp, -np.inf)))
        if not np.isfinite(dp[state]):
            return -np.inf, None
        value = float(dp[state])
        completion = np.empty((2, n), dtype=np.int8)
        for i in range(n, 0, -1):
            completion[:, i - 1] = choices[i, state]
            state = parents[i, state]
        if state != n or sign * (completion[0].sum() - completion[1].sum()) > 0:
            raise AssertionError("Invalid null completion")
        if not np.isclose(value, self.row(completion) @ factors, atol=1e-8):
            raise AssertionError("DP witness disagrees with factor row")
        return value, completion

    def event(self, i, a, b, missing):
        return self.event_group[i, a, b, missing]


def factor(design, sign, max_rounds=80):
    """Cutting-plane optimization with a checked feasible fallback."""
    unit = np.ones(len(design.groups))
    rows = []
    # Warm-start at a feasible constant and add a worst null before solving.
    _, first = design.worst_null(unit, sign)
    if first is None:
        raise ValueError("Logically resolved hypothesis was passed to factor")
    rows.append(design.row(first))
    current = np.full(len(unit), .99)
    for _ in range(max_rounds):
        mat = np.vstack(rows)
        result = minimize(lambda f: -design.alt @ np.log(f), current,
                          jac=lambda f: -design.alt / f,
                          bounds=[(.001, 100)] * len(unit),
                          constraints=[dict(type="ineq", fun=lambda f: 1 - mat @ f,
                                            jac=lambda f: -mat)],
                          method="SLSQP", options=dict(ftol=1e-10, maxiter=500))
        if not result.success or not np.isfinite(result.x).all():
            return unit, True
        candidate = result.x
        worst, completion = design.worst_null(candidate, sign)
        if worst <= 1 + 1e-8:
            # Scale away solver tolerance. This certificate is a true
            # conditional e-factor even at a near-active constraint.
            safe = candidate / max(1, worst) / (1 + 1e-10)
            certified, _ = design.worst_null(safe, sign)
            if certified > 1 + 1e-9:
                raise AssertionError("Uncertified optimized e-factor")
            return safe, False
        row = design.row(completion)
        if any(np.allclose(row, prior, atol=1e-12) for prior in rows):
            return unit, True
        rows.append(row)
        current = np.minimum(candidate / worst, 100)
    return unit, True


def certificate(scores, pa, pb, q, seed, alpha=.05):
    """Resolve the fixed-pool sign with two safe conditional wealths."""
    scores = np.asarray(scores, dtype=np.int8)
    if scores.shape[0] != 2 or not np.isin(scores, (0, 1)).all():
        raise ValueError("Two binary system rows required")
    n = scores.shape[1]
    seen = np.zeros((2, n), dtype=bool)
    known = np.zeros((2, n), dtype=np.int8)
    rng = np.random.default_rng(seed)
    wealth = np.zeros(2)
    threshold = np.log(2 / alpha)
    path = []
    fallbacks = 0
    decision = None
    while decision is None:
        lower = int(known[0].sum() - known[1].sum() - np.count_nonzero(~seen[1]))
        upper = int(known[0].sum() - known[1].sum() + np.count_nonzero(~seen[0]))
        if lower > 0:
            decision = 1
            break
        if upper < 0:
            decision = -1
            break
        if seen.all():
            decision = np.sign(known[0].sum() - known[1].sum())
            break
        plus = Design(seen, known, q, pa, pb)
        minus = Design(seen, known, q, 1 - pa, 1 - pb)
        fplus, fallback_plus = factor(plus, 1)
        fminus, fallback_minus = factor(minus, -1)
        fallbacks += int(fallback_plus) + int(fallback_minus)
        i = int(rng.choice(plus.eligible))
        a_unknown, b_unknown = ~seen[:, i]
        buy_b = bool(b_unknown and (not a_unknown or rng.random() < q))
        buy_a = bool(a_unknown)
        a = int(scores[0, i]) if buy_a else -1
        b = int(scores[1, i]) if buy_b else -1
        missing = bool(b_unknown and not buy_b)
        wealth[0] += np.log(fplus[plus.event(i, a, b, missing)])
        wealth[1] += np.log(fminus[minus.event(i, a, b, missing)])
        if buy_a:
            seen[0, i], known[0, i] = True, a
        if buy_b:
            seen[1, i], known[1, i] = True, b
        path.append((i, int(buy_a), int(buy_b)))
        # Check logical endpoints before stopping for wealth, exactly as the
        # next iteration will. A mathematically exact logical decision wins.
        lower = int(known[0].sum() - known[1].sum() - np.count_nonzero(~seen[1]))
        upper = int(known[0].sum() - known[1].sum() + np.count_nonzero(~seen[0]))
        if lower > 0:
            decision = 1
        elif upper < 0:
            decision = -1
        elif seen.all():
            decision = np.sign(known[0].sum() - known[1].sum())
        elif wealth[0] >= threshold and wealth[1] < threshold:
            decision = 1
        elif wealth[1] >= threshold and wealth[0] < threshold:
            decision = -1
        if len(path) > 2 * n:
            raise AssertionError("Repeated purchases or failure to terminate")
    truth = int(np.sign(scores[0].sum() - scores[1].sum()))
    return dict(cost=int(seen.sum()), decision=int(decision), truth=truth,
                wrong=bool(decision != truth), path=path, fallbacks=fallbacks)


def run(repeats=10, n=32):
    scenarios = {"aligned_strong": (.9, .1, .9, .1),
                 "aligned_moderate": (.7, .3, .7, .3),
                 "shifted_opposite": (.3, .7, .9, .1)}
    result = {}
    for name, (true_a, true_b, pa, pb) in scenarios.items():
        cases = []
        for rep in range(repeats):
            rng = np.random.default_rng(20261024 + rep + 100 * len(name))
            scores = (rng.random((2, n)) < np.array([[true_a], [true_b]])).astype(np.int8)
            methods = {str(q): certificate(scores, pa, pb, q, 97531 + rep)
                       for q in (1, .75, .5)}
            full_items = [i for i, _, _ in methods["1"]["path"]]
            remaining = [i for i in range(n) if i not in full_items]
            order = np.array(full_items + remaining, dtype=np.int32)
            stage22 = matched_stage22_cost(scores, np.array([[0, 1]], dtype=np.int16),
                                          order, np.random.default_rng(55191 + rep))
            if any(m["wrong"] for m in methods.values()):
                raise AssertionError("Wrong full-pool decision")
            cases.append(dict(methods=methods, stage22=int(stage22),
                              true_gap=int(scores[0].sum() - scores[1].sum())))
        means = {key: float(np.mean([case["methods"][key]["cost"] for case in cases]))
                 for key in ("1", "0.75", "0.5")}
        means["stage22"] = float(np.mean([case["stage22"] for case in cases]))
        result[name] = dict(mean_cost=means, cases=cases)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--items", type=int, default=32)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = run(repeats=args.repeats, n=args.items)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    for name, value in result.items():
        print(name, value["mean_cost"])
