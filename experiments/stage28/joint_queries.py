"""Exploratory coupled-query baseline for prospective, shared-pair ranking.

This combines known propensity correction with predictable betting. It is not
claimed to be a new statistical procedure.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

ALPHA = 0.05
SEED = 20261022
EPSILON = 0.25
Q_FIXED = 0.75
RHOS = np.array((0.10, 0.25, 0.50, 0.85))
EDGES = ((0, 1), (0, 2), (1, 2))
METHODS = ("paired_fixed", "paired_adaptive", "independent_fixed",
           "coupled_fixed", "independent_adaptive", "coupled_adaptive",
           "coupled_allocation")
SCENARIOS = ("aligned", "weak", "reversed", "anti_residual", "tie")


def populations(scenario: str) -> np.ndarray:
    """Fixed synthetic potential scores, systems x items x raters."""
    if scenario not in SCENARIOS:
        raise ValueError(scenario)
    rng = np.random.default_rng(SEED + SCENARIOS.index(scenario))
    latent = rng.random((32, 6))
    item = rng.uniform(-0.10, 0.10, size=(32, 1))
    rater = rng.uniform(-0.05, 0.05, size=(1, 6))
    if scenario == "tie":
        row = (latent < 0.5 + item + rater).astype(float)
        return np.repeat(row[None], 3, axis=0)
    if scenario == "anti_residual":
        # Conditional candidate residuals tend to oppose one another.
        ref = (rng.random((32, 6)) < 0.85 + item + rater).astype(float)
        b = (latent < 0.39 + item + rater).astype(float)
        c = (latent > 0.75 + item + rater).astype(float)
        return np.stack((ref, b, c))
    levels = {"aligned": (0.80, 0.20, 0.10),
              "weak": (0.55, 0.50, 0.45),
              "reversed": (0.45, 0.80, 0.70)}[scenario]
    return np.stack([(latent < np.clip(level + item + rater, 0, 1)).astype(float)
                     for level in levels])


def query_probabilities(residual_squares, seen, reference_counts, allocation):
    """History-only two-stratum probabilities with floor and target 0.75."""
    if not allocation:
        return np.full((2, 2), Q_FIXED)
    rms = np.sqrt((residual_squares + 1.0) / (seen + 4.0))
    weights = (reference_counts + 2.0) / (np.sum(reference_counts) + 4.0)
    low, high = 0.0, 1.0
    while float(np.sum(np.clip(high * rms, EPSILON, 1.0) * weights)) < 2 * Q_FIXED:
        high *= 2
    for _ in range(32):
        scale = (low + high) / 2
        q = np.clip(scale * rms, EPSILON, 1.0)
        if float(np.sum(q * weights)) < 2 * Q_FIXED:
            low = scale
        else:
            high = scale
    return np.clip(high * rms, EPSILON, 1.0)


def bounds_for_edge(edge, predictions, probabilities):
    """Worst possible signed corrected outcomes before drawing the pair."""
    i, j = EDGES[edge]
    minimum, maximum = math.inf, -math.inf
    for a in (0, 1):
        if i == 0:
            m, q = predictions[j - 1, a], probabilities[j - 1, a]
            lo = a - m - (1 - m) / q
            hi = a - m + m / q
        else:
            mi, mj = predictions[i - 1, a], predictions[j - 1, a]
            qi, qj = probabilities[i - 1, a], probabilities[j - 1, a]
            lo = mi - mj - mi / qi - (1 - mj) / qj
            hi = mi - mj + (1 - mi) / qi + mj / qj
        minimum, maximum = min(minimum, lo), max(maximum, hi)
    return max(-minimum, 1e-12), max(maximum, 1e-12)


def corrected_edge(edge, reference, candidates, selected, predictions, probabilities):
    """Use only acquired candidate scores; an unqueried entry is irrelevant."""
    i, j = EDGES[edge]
    a = int(reference)
    if i == 0:
        c = j - 1
        m, q = predictions[c, a], probabilities[c, a]
        return reference - m - selected[c] * (candidates[c] - m) / q
    x, y = i - 1, j - 1
    mx, my = predictions[x, a], predictions[y, a]
    qx, qy = probabilities[x, a], probabilities[y, a]
    return (mx - my + selected[x] * (candidates[x] - mx) / qx
            - selected[y] * (candidates[y] - my) / qy)


class Evidence:
    """Familywise union over two directions on three predeclared edges."""

    def __init__(self, adaptive):
        self.adaptive = adaptive
        self.log_wealth = np.zeros((len(EDGES), 2, len(RHOS) + int(adaptive)))
        self.decisions = np.zeros(len(EDGES), dtype=np.int8)
        self.n = np.zeros(len(EDGES), dtype=int)
        self.sums = np.zeros(len(EDGES))
        self.squares = np.zeros(len(EDGES))
        self.threshold = math.log(2 * len(EDGES) / ALPHA)

    def prepare(self, bounds):
        """Commit all bets before looking at this round's reference score."""
        bets = np.zeros_like(self.log_wealth)
        for edge in range(len(EDGES)):
            if self.decisions[edge]:
                continue
            for direction, lower_bound in enumerate(bounds[edge]):
                bets[edge, direction, :len(RHOS)] = RHOS / lower_bound
                if self.adaptive:
                    mean_sign = (1 if direction == 0 else -1) * self.sums[edge]
                    # History-only regularized Kelly approximation. Validity
                    # requires predictability and a bound, not this formula.
                    candidate = max(0.0, mean_sign) / (self.squares[edge] + 8 * lower_bound**2)
                    bets[edge, direction, -1] = min(0.95 / lower_bound, candidate)
        return bets

    def update(self, edge, outcome, bounds, bets):
        if self.decisions[edge]:
            return
        if not -bounds[edge][0] - 1e-10 <= outcome <= bounds[edge][1] + 1e-10:
            raise AssertionError("Observed outcome exceeds pre-draw bounds")
        self.log_wealth[edge, 0] += np.log1p(bets[edge, 0] * outcome)
        self.log_wealth[edge, 1] += np.log1p(-bets[edge, 1] * outcome)
        wealth = np.logaddexp.reduce(self.log_wealth[edge], axis=1) - math.log(self.log_wealth.shape[2])
        if wealth[0] >= self.threshold and wealth[1] >= self.threshold:
            raise AssertionError("Opposite declarations on one round")
        if wealth[0] >= self.threshold:
            self.decisions[edge] = 1
        elif wealth[1] >= self.threshold:
            self.decisions[edge] = -1
        self.n[edge] += 1
        self.sums[edge] += outcome
        self.squares[edge] += outcome**2


@dataclass
class Ledger:
    items: np.ndarray
    raters: np.ndarray
    shared: np.ndarray
    independent: np.ndarray


def ledger_for(scenario, repeat, rounds):
    rng = np.random.default_rng(SEED + 10000 * SCENARIOS.index(scenario) + repeat)
    return Ledger(items=rng.integers(32, size=rounds),
                  raters=rng.integers(6, size=rounds),
                  shared=rng.random(rounds),
                  independent=rng.random((rounds, 2)))


def run_one(scores, ledger, method, record=False):
    if method not in METHODS:
        raise ValueError(method)
    paired = method.startswith("paired")
    coupled = method.startswith("coupled")
    allocation = method == "coupled_allocation"
    evidence = Evidence(adaptive=("adaptive" in method or allocation))
    seen = np.zeros((2, 2), dtype=int)
    candidate_sum = np.zeros((2, 2))
    residual_squares = np.zeros((2, 2))
    reference_counts = np.zeros(2, dtype=int)
    cost = 0
    processed = 0
    log = []
    for t in range(len(ledger.items)):
        active = np.flatnonzero(evidence.decisions == 0)
        if len(active) == 0:
            break
        processed += 1
        needs = np.array([any(j in EDGES[e] for e in active) for j in (1, 2)])
        if paired:
            bounds = [(1.0, 1.0)] * len(EDGES)
            bets = evidence.prepare(bounds)
            item, rater = int(ledger.items[t]), int(ledger.raters[t])
            # Paired control does not buy the reference if only edge (1,2) remains.
            buy_ref = bool(np.any(active < 2))
            ref = float(scores[0, item, rater]) if buy_ref else None
            labels = [float(scores[j + 1, item, rater]) if needs[j] else 0.0 for j in range(2)]
            cost += int(buy_ref) + int(sum(needs))
            outcomes = [((ref if i == 0 else labels[i - 1]) - labels[j - 1])
                        for e in active for i, j in (EDGES[e],)]
            for edge, outcome in zip(active, outcomes):
                evidence.update(edge, outcome, bounds, bets)
            if record:
                log.append((int(buy_ref), needs.astype(int).tolist(), len(active)))
            continue

        # Predictions, propensities, signed bounds and bets are frozen before
        # drawing or inspecting the current item/rater and its reference score.
        predictions = (candidate_sum + 2.0) / (seen + 4.0)
        probabilities = query_probabilities(residual_squares, seen, reference_counts, allocation)
        bounds = [bounds_for_edge(e, predictions, probabilities) for e in range(len(EDGES))]
        bets = evidence.prepare(bounds)
        item, rater = int(ledger.items[t]), int(ledger.raters[t])
        ref = float(scores[0, item, rater])
        if ref not in (0.0, 1.0):
            raise ValueError("The Stage 28 reference stratum requires binary scores")
        stratum = int(ref)
        cost += 1
        reference_counts[stratum] += 1
        selected = np.zeros(2, dtype=int)
        labels = np.zeros(2)
        for c in range(2):
            if not needs[c]:
                continue
            coin = ledger.shared[t] if coupled else ledger.independent[t, c]
            selected[c] = int(coin < probabilities[c, stratum])
            if selected[c]:
                labels[c] = float(scores[c + 1, item, rater])
                cost += 1
        outcomes = [corrected_edge(e, ref, labels, selected, predictions, probabilities)
                    for e in active]
        for edge, outcome in zip(active, outcomes):
            evidence.update(edge, outcome, bounds, bets)
        for c in range(2):
            if selected[c]:
                residual_squares[c, stratum] += (labels[c] - predictions[c, stratum]) ** 2
                candidate_sum[c, stratum] += labels[c]
                seen[c, stratum] += 1
        if record:
            log.append((1, selected.tolist(), len(active)))
    truth = [int(np.sign(scores[i].mean() - scores[j].mean())) for i, j in EDGES]
    result = dict(cost=int(cost), rounds=processed,
                  decisions=evidence.decisions.astype(int).tolist(),
                  complete=bool(np.all(evidence.decisions != 0)),
                  wrong=int(np.sum((evidence.decisions != 0) & (evidence.decisions != truth))),
                  unresolved=int(np.sum(evidence.decisions == 0)))
    if record:
        result["acquired"] = log
    return result


def run_experiment(repeats=100, rounds=1600):
    if repeats <= 0 or rounds <= 0:
        raise ValueError("Positive repeats and cap required")
    results = []
    for scenario in SCENARIOS:
        scores = populations(scenario)
        for repeat in range(repeats):
            ledger = ledger_for(scenario, repeat, rounds)
            methods = {name: run_one(scores, ledger, name) for name in METHODS}
            signs = [int(np.sign(scores[i].mean() - scores[j].mean())) for i, j in EDGES]
            results.append(dict(scenario=scenario, repeat=repeat, signs=signs, methods=methods))
    return results
