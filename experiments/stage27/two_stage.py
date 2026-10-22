"""Two-stage population-ranking sanity baseline, not a proposed new method."""
from __future__ import annotations

import numpy as np

ALPHA = 0.05
EPSILON = 0.25
RHOS = (0.05, 0.1, 0.2, 0.4, 0.8)
MAX_ROUNDS = 800
SEED = 20261022
SCENARIOS = ("aligned", "weak", "reversed", "tie")


def corrected_signal(reference, candidate, prediction, probability, selected):
    """Unbiased for this drawn (item, rater) pair over the query coin."""
    if not 0 <= reference <= 1 or not 0 <= candidate <= 1:
        raise ValueError("Scores must lie in [0, 1]")
    if not 0 <= prediction <= 1 or not EPSILON <= probability <= 1:
        raise ValueError("Invalid prediction or query probability")
    return reference - prediction - selected * (candidate - prediction) / probability


def potential_scores(scenario):
    """One fixed synthetic population of 32 items and 6 raters."""
    if scenario not in SCENARIOS:
        raise ValueError("Unknown scenario")
    rng = np.random.default_rng(SEED + SCENARIOS.index(scenario))
    latent = rng.random((32, 6))
    item = rng.uniform(-0.10, 0.10, size=(32, 1))
    rater = rng.uniform(-0.05, 0.05, size=(1, 6))
    if scenario == "tie":
        row = (latent < 0.5 + item + rater).astype(float)
        return np.repeat(row[None, :, :], 3, axis=0)
    levels = {"aligned": (0.80, 0.20, 0.10),
              "weak": (0.55, 0.50, 0.45),
              "reversed": (0.45, 0.80, 0.70)}[scenario]
    return np.stack([(latent < np.clip(level + item + rater, 0, 1)).astype(float)
                     for level in levels])


class DirectionalEvidence:
    def __init__(self, edges, normalization):
        self.forward = np.zeros((edges, len(RHOS)))
        self.reverse = np.zeros((edges, len(RHOS)))
        self.decisions = np.full(edges, 2, dtype=np.int8)
        self.normalization = normalization
        self.log_threshold = np.log(2 * edges / ALPHA)

    def update(self, edge, signal):
        if self.decisions[edge] != 2:
            return
        stake = np.asarray(RHOS) * signal / self.normalization
        self.forward[edge] += np.log1p(stake)
        self.reverse[edge] += np.log1p(-stake)
        log_f = np.logaddexp.reduce(self.forward[edge]) - np.log(len(RHOS))
        log_r = np.logaddexp.reduce(self.reverse[edge]) - np.log(len(RHOS))
        if log_f >= self.log_threshold:
            self.decisions[edge] = 1
        elif log_r >= self.log_threshold:
            self.decisions[edge] = -1


def run_one(scores, items, raters, coins, corrected):
    """A paired or corrected star, both on the same iid item/rater ledger."""
    edges = scores.shape[0] - 1
    evidence = DirectionalEvidence(edges, 1 / EPSILON if corrected else 1)
    seen = np.zeros((edges, 2), dtype=int)
    sum_candidate = np.zeros_like(seen, dtype=float)
    cost = 0
    for t, (item, rater) in enumerate(zip(items, raters), 1):
        if np.all(evidence.decisions != 2):
            break
        ref = float(scores[0, item, rater])
        stratum = int(ref)
        cost += 1  # the current reference judgment is shared by all active edges
        for edge in np.flatnonzero(evidence.decisions == 2):
            if corrected:
                probability = 1.0 if ref == 1 else EPSILON
                prediction = ((sum_candidate[edge, stratum] + 2.0) /
                              (seen[edge, stratum] + 4.0))
                selected = int(coins[t - 1, edge] < probability)
                candidate = 0.0  # arbitrary placeholder if no label is bought
                if selected:
                    candidate = float(scores[edge + 1, item, rater])
                signal = corrected_signal(ref, candidate, prediction,
                                          probability, selected)
                if selected:
                    cost += 1
                    seen[edge, stratum] += 1
                    sum_candidate[edge, stratum] += candidate
            else:
                cost += 1
                candidate = float(scores[edge + 1, item, rater])
                signal = ref - candidate
            evidence.update(edge, signal)
    truth = np.sign(scores[0].mean() - scores[1:].mean(axis=(1, 2))).astype(np.int8)
    reported = evidence.decisions != 2
    return dict(cost=cost, completed=bool(np.all(reported)),
                wrong=int(np.sum(reported & (evidence.decisions != truth))),
                unresolved=int(np.sum(~reported)))


def run_synthetic(repeats=100, max_rounds=MAX_ROUNDS):
    if repeats <= 0 or max_rounds <= 0:
        raise ValueError("Positive repeats and round cap required")
    rows = []
    for scenario in SCENARIOS:
        scores = potential_scores(scenario)
        truth = np.sign(scores[0].mean() - scores[1:].mean(axis=(1, 2)))
        for repeat in range(repeats):
            rng = np.random.default_rng(SEED + 10000 * SCENARIOS.index(scenario) + repeat)
            items = rng.integers(scores.shape[1], size=max_rounds)
            raters = rng.integers(scores.shape[2], size=max_rounds)
            coins = rng.random((max_rounds, scores.shape[0] - 1))
            paired = run_one(scores, items, raters, coins, corrected=False)
            adaptive = run_one(scores, items, raters, coins, corrected=True)
            rows.append(dict(scenario=scenario, repeat=repeat,
                             population_signs=truth.astype(int).tolist(),
                             paired=paired, two_stage=adaptive))
    return rows
