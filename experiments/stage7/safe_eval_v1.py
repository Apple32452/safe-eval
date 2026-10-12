"""Synthetic finite-benchmark evaluation pilot. No external or private data.

Positive randomized sampling without replacement and predictable betting.
The predictor/policy are prototypes, not implementations of published baselines.
"""
from __future__ import annotations

import numpy as np

METHODS = ('uniform_raw', 'uniform_predict', 'adaptive_fixed', 'adaptive_monitor')


def corrected_draws(observed_sum, prediction, probability, outcomes, n_items):
    """All possible next Z values, for a *remaining* item pool.

    Its probability-weighted conditional expectation is the full benchmark mean.
    Do not apply the usual with-replacement IPW formula to a shrinking pool.
    """
    base = (observed_sum + np.sum(prediction, axis=-1)) / n_items
    return base[..., None] + (outcomes - prediction) / (n_items * probability)


def bet_factors(z, lower, upper, candidates, eta):
    """Candidate-specific, predictable stakes; factors are at least 0.5.

    Plus wealth decreases and minus wealth increases with the candidate mean.
    eta must be computed before observing z; bounds and caps are predictable.
    """
    pos = np.minimum(eta[..., None], 0.5 / np.maximum(candidates - lower[..., None], 1e-12))
    neg = np.minimum(eta[..., None], 0.5 / np.maximum(upper[..., None] - candidates, 1e-12))
    diff = z[..., None] - candidates
    return 1 + pos * diff, 1 - neg * diff


def outer_interval(log_plus, log_minus, grid, log_threshold):
    """Conservative outer brackets, not an assumption that Q is on the grid."""
    lower = np.max(np.where(log_plus >= log_threshold, grid, 0.0), axis=-1)
    upper = np.min(np.where(log_minus >= log_threshold, grid, 1.0), axis=-1)
    impossible = (log_plus[..., -1] >= log_threshold) | (log_minus[..., 0] >= log_threshold)
    lower = np.where(impossible, 1.0, lower)
    upper = np.where(impossible, 0.0, upper)
    return lower, upper


def reference_features(history, rank=3):
    """Only historical responses determine the feature and acquisition models."""
    mean = history.mean(axis=0)
    centered = history - mean
    _, _, vt = np.linalg.svd(centered, full_matrices=False)
    basis = vt[:rank].T * np.sqrt(history.shape[1])
    features = np.column_stack([np.ones(history.shape[1]), basis])
    residual = centered - (centered @ vt[:rank].T) @ vt[:rank]
    # A floor avoids a deterministic zero acquisition probability before mixing.
    scale = np.maximum(np.sqrt(np.mean(residual ** 2, axis=0)), 0.01)
    return mean, features, scale


def evaluate_many(history, oracle, trials, method, seed=1, delta=0.05,
                  epsilon=0.05, anchors=12, grid_size=201):
    """Return full trajectories; the caller alone knows the true target mean.

    oracle(indices) returns the newly queried values for the batch of trials.
    Continuing after the first stopping decision is for simulation diagnostics.
    Every item is queried at most once; reported cost uses the first valid stop.
    Runtime O(T * R * (N * d + G)); memory O(R * (N + G + T) + M * N).
    d is the small predictor dimension, G the confidence grid size, T <= N.
    """
    if method not in METHODS:
        raise ValueError(method)
    if not (0 < delta < 1 and 0 < epsilon < 0.5):
        raise ValueError('delta and epsilon are outside their valid ranges')
    history = np.asarray(history, dtype=float)
    if history.ndim != 2 or not np.isfinite(history).all() or np.any((history < 0) | (history > 1)):
        raise ValueError('historical scores must be a finite matrix in [0,1]')
    _, n = history.shape
    mean, x, scale = reference_features(history)
    d = x.shape[1]
    rng = np.random.default_rng(seed)
    rows = np.arange(trials)
    grid = np.linspace(0, 1, grid_size)
    threshold = np.log(2 / delta)  # delta/2 for each directional wealth.
    unseen = np.ones((trials, n), dtype=bool)
    observed_sum = np.zeros(trials)
    a_ridge = np.broadcast_to(np.diag([0.25] + [1.0] * (d - 1)), (trials, d, d)).copy()
    b_ridge = np.zeros((trials, d))
    plus = np.zeros((trials, grid_size))
    minus = plus.copy()
    running_l = np.zeros(trials)
    running_u = np.ones(trials)
    z_sum = np.zeros(trials)
    z_mean = np.zeros(trials)
    z_m2 = np.zeros(trials)
    residual_monitor = np.full(trials, np.mean(scale ** 2))
    stop = np.zeros(trials, dtype=int)
    stop_l, stop_u = np.full(trials, np.nan), np.full(trials, np.nan)
    estimates, lows, highs, mixtures, selected = [], [], [], [], []

    for t in range(1, n + 1):
        remaining = n - t + 1
        if method == 'uniform_raw':
            mu = np.zeros((trials, n))
        else:
            beta = np.linalg.solve(a_ridge, b_ridge[..., None])[..., 0]
            mu = np.clip(mean + beta @ x.T, 0, 1)
        uniform = unseen / remaining
        if method in ('uniform_raw', 'uniform_predict') or t <= anchors:
            lam = np.ones(trials)
            p = uniform
        else:
            if method == 'adaptive_fixed':
                lam = np.full(trials, 0.2)
            else:
                reference_r2 = np.sum(unseen * scale ** 2, axis=1) / remaining
                ratio = np.sqrt(np.maximum(residual_monitor, 0) / np.maximum(reference_r2, 1e-6))
                lam = 0.2 + 0.8 * np.clip((ratio - 1) / 3, 0, 1)
            score = unseen * scale
            q = score / score.sum(axis=1, keepdims=True)
            p = (1 - lam[:, None]) * q + lam[:, None] * uniform
        assert np.all(p[unseen] > 0) and np.allclose(p.sum(axis=1), 1)

        # All quantities here are computed before the oracle reveals the draw.
        base = (observed_sum + np.sum(unseen * mu, axis=1)) / n
        inv_np = np.divide(1.0, n * p, out=np.zeros_like(p), where=unseen)
        bound_l = base + np.min(np.where(unseen, -mu * inv_np, np.inf), axis=1)
        bound_u = base + np.max(np.where(unseen, (1 - mu) * inv_np, -np.inf), axis=1)
        past_var = (0.25 + z_m2) / t
        eta = np.minimum(100, np.sqrt(2 * threshold / (t * past_var)))

        cdf = np.cumsum(p, axis=1)
        cdf[:, -1] = 1.0
        idx = np.sum(cdf <= rng.random(trials)[:, None], axis=1)
        assert unseen[rows, idx].all()
        y = np.asarray(oracle(idx), dtype=float)
        if y.shape != (trials,) or not np.isfinite(y).all() or np.any((y < 0) | (y > 1)):
            raise ValueError('oracle must return one bounded score per trial')
        residual = y - mu[rows, idx]
        z = base + residual * inv_np[rows, idx]
        assert np.all(z >= bound_l - 1e-10) and np.all(z <= bound_u + 1e-10)
        fp, fm = bet_factors(z, bound_l, bound_u, grid, eta)
        assert fp.min() >= 0.5 - 1e-10 and fm.min() >= 0.5 - 1e-10
        plus += np.log(fp)
        minus += np.log(fm)
        new_l, new_u = outer_interval(plus, minus, grid, threshold)

        # Update the predictor and diagnostic only after consuming the draw.
        xi = x[idx]
        a_ridge += xi[:, :, None] * xi[:, None, :]
        b_ridge += xi * (y - mean[idx])[:, None]
        correction = residual ** 2 / (remaining * p[rows, idx])
        residual_monitor = 0.85 * residual_monitor + 0.15 * correction
        unseen[rows, idx] = False
        observed_sum += y
        deterministic_l = observed_sum / n
        deterministic_u = (observed_sum + n - t) / n
        running_l = np.maximum.reduce([running_l, new_l, deterministic_l])
        running_u = np.minimum.reduce([running_u, new_u, deterministic_u])
        z_sum += z
        step = z - z_mean
        z_mean += step / t
        z_m2 += step * (z - z_mean)
        estimate = z_sum / t
        if t == n:
            # Complete evaluation identifies Q exactly, even after a rare CS failure.
            running_l = deterministic_l.copy()
            running_u = deterministic_l.copy()
            estimate = deterministic_l.copy()
        valid = running_u >= running_l
        new_stop = (stop == 0) & valid & (running_u - running_l <= 2 * epsilon + 1e-12)
        stop[new_stop] = t
        stop_l[new_stop], stop_u[new_stop] = running_l[new_stop], running_u[new_stop]
        estimates.append(estimate.copy()); lows.append(running_l.copy()); highs.append(running_u.copy())
        mixtures.append(lam.copy()); selected.append(idx.copy())

    return dict(estimate=np.asarray(estimates), lower=np.asarray(lows), upper=np.asarray(highs),
                mixture=np.asarray(mixtures), selected=np.asarray(selected), stop=stop,
                stop_lower=stop_l, stop_upper=stop_u)


def synthetic_populations(seed=20261011, n=256, historical=48, panels=4):
    """Fixed synthetic populations; randomized acquisition is repeated separately."""
    rng = np.random.default_rng(seed)
    mean = rng.uniform(0.2, 0.8, n)
    factors = rng.normal(size=(n, 3))
    factors /= np.maximum(np.linalg.norm(factors, axis=1, keepdims=True), 1e-9)
    # Historical uncertainty is deliberately heterogeneous to test acquisition.
    sigma = np.where(np.arange(n) < n // 2, 0.065, 0.012)
    ability = rng.normal(0, 0.065, (historical, 3))
    hist = np.clip(mean + ability @ factors.T + rng.normal(size=(historical, n)) * sigma, 0, 1)
    target_ability = rng.normal(0, 0.065, (panels, 3))
    good = np.clip(mean + target_ability @ factors.T + rng.normal(size=(panels, n)) * sigma, 0, 1)
    reversed_scores = 1 - good
    unrelated = rng.uniform(0.05, 0.95, (panels, n))
    localized = good.copy()
    shifted = rng.choice(np.arange(n // 2, n), size=n // 4, replace=False)
    localized[:, shifted] = np.clip(localized[:, shifted] + 0.45, 0, 1)
    return hist, dict(transferable=good, unrelated=unrelated,
                     reversed=reversed_scores, localized_shift=localized)
