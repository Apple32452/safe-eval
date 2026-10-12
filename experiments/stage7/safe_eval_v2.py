"""Stage-two uniform-sampling ablations; fixed finite populations in [0,1].

All predictor and betting updates are predictable. The stronger controls use
the same changes as prediction-assisted methods. No transfer assumption enters
coverage. This is a prototype built from standard betting ideas, not a new
theorem or a reproduction of a published baseline.
"""
from __future__ import annotations

import numpy as np
from safe_eval_v1 import reference_features, outer_interval


def directional_factors(z, lower, upper, candidates, eta, cap_fraction):
    if not 0 < cap_fraction < 1:
        raise ValueError('cap_fraction must be strictly between zero and one')
    lp = np.minimum(eta[..., None], cap_fraction /
                    np.maximum(candidates - lower[..., None], 1e-12))
    lm = np.minimum(eta[..., None], cap_fraction /
                    np.maximum(upper[..., None] - candidates, 1e-12))
    diff = z[..., None] - candidates
    return 1 + lp * diff, 1 - lm * diff


def evaluate_uniform_many(history, oracle, trials, seed=1, delta=0.05,
                          epsilon=0.05, grid_size=201, prediction_strength=1.0,
                          cap_fraction=0.9, stake_rule='targeted', learn_trust=False):
    """Uniform sampling, with a predictable ridge predictor and bet ablations.

The targeted rule epsilon/(past_variance + epsilon**2) follows the quadratic
approximation to log-wealth growth at alternatives epsilon from the mean. It
is an efficiency heuristic; coverage follows from predictability and support
caps, regardless of the quality of the variance estimate or predictions.
"""
    history = np.asarray(history, dtype=float)
    if (history.ndim != 2 or min(history.shape) < 2 or
            not np.isfinite(history).all() or np.any((history < 0) | (history > 1))):
        raise ValueError('history must be a finite matrix in [0,1]')
    if not (0 < delta < 1 and 0 < epsilon < 0.5 and trials > 0 and grid_size >= 3):
        raise ValueError('invalid evaluation configuration')
    if not (0 <= prediction_strength <= 1 and 0 < cap_fraction < 1):
        raise ValueError('invalid prediction strength or cap fraction')
    if stake_rule not in ('legacy', 'targeted'):
        raise ValueError('unknown stake rule')
    n = history.shape[1]
    mean, x, _ = reference_features(history)
    d = x.shape[1]
    rows = np.arange(trials)
    rng = np.random.default_rng(seed)
    grid = np.linspace(0, 1, grid_size)
    threshold = np.log(2 / delta)
    unseen = np.ones((trials, n), dtype=bool)
    observed_sum = np.zeros(trials)
    a_ridge = np.broadcast_to(np.diag([0.25] + [1.0] * (d - 1)),
                              (trials, d, d)).copy()
    b_ridge = np.zeros((trials, d))
    plus = np.zeros((trials, grid_size))
    minus = plus.copy()
    running_l, running_u = np.zeros(trials), np.ones(trials)
    z_sum, z_mean, z_m2 = np.zeros(trials), np.zeros(trials), np.zeros(trials)
    # Prequential regression sufficient statistics. Predictions are recorded
    # before their corresponding outcomes; no in-sample fitted residuals enter.
    score_sum, score_sq, y_sum, score_y = (np.zeros(trials) for _ in range(4))
    stop = np.zeros(trials, dtype=int)
    stop_l, stop_u = np.full(trials, np.nan), np.full(trials, np.nan)
    saved = {k: [] for k in ('estimate', 'lower', 'upper', 'selected',
                             'support_span', 'variance_estimate',
                             'lower_probe_stake', 'upper_probe_stake',
                             'lower_probe_capped', 'upper_probe_capped',
                             'prediction_strength')}
    for t in range(1, n + 1):
        remaining = n - t + 1
        strength = np.full(trials, prediction_strength)
        if learn_trust and t > 1:
            count = t - 1
            sxx = np.maximum(0, score_sq - score_sum ** 2 / count)
            sxy = score_y - score_sum * y_sum / count
            # 0.25 pseudo sum-of-squares favors the predetermined initial trust.
            strength = np.clip((0.25 * prediction_strength + sxy) /
                               (0.25 + sxx), 0, prediction_strength)
        if prediction_strength == 0:
            mu = np.zeros((trials, n))
        else:
            beta = np.linalg.solve(a_ridge, b_ridge[..., None])[..., 0]
            full_mu = np.clip(mean + beta @ x.T, 0, 1)
            mu = 0.5 + strength[:, None] * (full_mu - 0.5)
        base = (observed_sum + np.sum(unseen * mu, axis=1)) / n
        lo = base - remaining / n * np.max(np.where(unseen, mu, -np.inf), axis=1)
        hi = base + remaining / n * np.max(np.where(unseen, 1 - mu, -np.inf), axis=1)
        # Same variance prior and horizon as the original pilot.
        past_var = (0.25 + z_m2) / t
        if stake_rule == 'legacy':
            eta = np.minimum(100, np.sqrt(2 * threshold / (t * past_var)))
        else:
            eta = np.minimum(100, epsilon / (past_var + epsilon ** 2))
        # Probes depend on the past, and are diagnostics only.
        center = np.full(trials, 0.5) if t == 1 else np.clip(z_mean, 0, 1)
        cap_lo = cap_fraction / np.maximum(center - epsilon - lo, 1e-12)
        cap_hi = cap_fraction / np.maximum(hi - center - epsilon, 1e-12)
        p = unseen / remaining
        cdf = np.cumsum(p, axis=1)
        cdf[:, -1] = 1.0
        idx = np.sum(cdf <= rng.random(trials)[:, None], axis=1)
        if not unseen[rows, idx].all():
            raise RuntimeError('attempted duplicate query')
        y = np.asarray(oracle(idx), dtype=float)
        if y.shape != (trials,) or not np.isfinite(y).all() or np.any((y < 0) | (y > 1)):
            raise ValueError('oracle must return one score in [0,1] per trial')
        z = base + remaining / n * (y - mu[rows, idx])
        fp, fm = directional_factors(z, lo, hi, grid, eta, cap_fraction)
        if min(fp.min(), fm.min()) < 1 - cap_fraction - 1e-10:
            raise RuntimeError('betting factor violates its support bound')
        plus += np.log(fp)
        minus += np.log(fm)
        new_l, new_u = outer_interval(plus, minus, grid, threshold)
        # No outcome from this round affects its own prediction or stake.
        xi = x[idx]
        a_ridge += xi[:, :, None] * xi[:, None, :]
        b_ridge += xi * (y - mean[idx])[:, None]
        if learn_trust and prediction_strength > 0:
            score = full_mu[rows, idx]
            score_sum += score
            score_sq += score ** 2
            y_sum += y
            score_y += score * y
        unseen[rows, idx] = False
        observed_sum += y
        deterministic_l = observed_sum / n
        deterministic_u = (observed_sum + n - t) / n
        running_l = np.maximum.reduce([running_l, new_l, deterministic_l])
        running_u = np.minimum.reduce([running_u, new_u, deterministic_u])
        z_sum += z
        difference = z - z_mean
        z_mean += difference / t
        z_m2 += difference * (z - z_mean)
        estimate = z_sum / t
        if t == n:
            running_l = deterministic_l.copy()
            running_u = deterministic_l.copy()
            estimate = deterministic_l.copy()
        valid = running_u >= running_l
        new_stop = (stop == 0) & valid & (running_u - running_l <= 2 * epsilon + 1e-12)
        stop[new_stop] = t
        stop_l[new_stop], stop_u[new_stop] = running_l[new_stop], running_u[new_stop]
        values = dict(estimate=estimate, lower=running_l, upper=running_u, selected=idx,
                      support_span=hi - lo, variance_estimate=past_var,
                      lower_probe_stake=np.minimum(eta, cap_lo),
                      upper_probe_stake=np.minimum(eta, cap_hi),
                      lower_probe_capped=eta > cap_lo, upper_probe_capped=eta > cap_hi,
                      prediction_strength=strength)
        for key, value in values.items():
            saved[key].append(value.copy())
    result = {key: np.asarray(values) for key, values in saved.items()}
    result.update(stop=stop, stop_lower=stop_l, stop_upper=stop_u)
    return result
