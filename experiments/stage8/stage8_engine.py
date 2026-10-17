"""Matched count-grid and 75% reserve controls on one uniform query ledger.

The prediction branch preserves the Stage 7 arithmetic. The zero-trust branch
uses the identical betting rule with the constant predictor cancelled exactly:
Z=S/N + remaining*Y/N, support [S/N, (S+remaining)/N]. Each branch updates its
own past-Z variance. Rules match; realized stakes need not match after Z changes.
"""
from __future__ import annotations

import math
import numpy as np
from stage8_common import METHODS, MIXTURES, WEIGHT
from binary_control import log_ppr
from safe_eval_v1 import reference_features
from safe_eval_v2 import directional_factors
from safe_eval_v3 import mixture_log_wealth
from reserve_fallback import candidate_hull, repair_empty_interval


def evaluate_matched(history, oracle, trials, seed=1, delta=.05, epsilon=.05):
    history = np.asarray(history, dtype=float)
    if (history.ndim != 2 or min(history.shape) < 2 or not np.isfinite(history).all()
            or np.any((history < 0) | (history > 1))):
        raise ValueError('Historical matrix must be finite and bounded')
    if trials < 1 or not 0 < delta < 1 or not 0 < epsilon < .5:
        raise ValueError('Invalid inference configuration')
    n = history.shape[1]
    mean, x, _ = reference_features(history)
    d = x.shape[1]
    grid = np.arange(n + 1) / n
    threshold = math.log(1 / delta)
    rng = np.random.default_rng(seed)
    rows = np.arange(trials)
    unseen = np.ones((trials, n), dtype=bool)
    successes = np.zeros(trials, dtype=int)
    a_ridge = np.broadcast_to(np.diag([.25] + [1.] * (d - 1)), (trials, d, d)).copy()
    b_ridge = np.zeros((trials, d))
    score_sum, score_sq, score_y, y_sum = (np.zeros(trials) for _ in range(4))
    pred_mean, pred_m2, zero_mean, zero_m2 = (np.zeros(trials) for _ in range(4))
    plus = {name: np.zeros((trials, n + 1)) for name in ('prediction_count_grid', 'raw_count_grid')}
    minus = {name: np.zeros((trials, n + 1)) for name in plus}
    masks = {name: np.ones((trials, n + 1), dtype=bool) for name in METHODS}
    runs = {name: dict(stop=np.zeros(trials, dtype=int), stop_lower=np.full(trials, np.nan),
                       stop_upper=np.full(trials, np.nan), lower=[], upper=[]) for name in METHODS}
    diag = {key: [] for key in ('selected', 'prediction_strength', 'prediction_mu',
                                'prediction_eta', 'zero_eta', 'prediction_lower', 'prediction_upper')}
    repairs = {name: [] for name in MIXTURES}
    for t in range(1, n + 1):
        count, remaining = t - 1, n - t + 1
        strength = np.full(trials, .5)
        if count:
            sxx = np.maximum(0, score_sq - score_sum ** 2 / count)
            sxy = score_y - score_sum * y_sum / count
            strength = np.clip((.125 + sxy) / (.25 + sxx), 0, .5)
        beta = np.linalg.solve(a_ridge, b_ridge[..., None])[..., 0]
        full_mu = np.clip(mean + beta @ x.T, 0, 1)
        mu = .5 + strength[:, None] * (full_mu - .5)
        base = (successes + np.sum(unseen * mu, axis=1)) / n
        lo = base - remaining / n * np.max(np.where(unseen, mu, -np.inf), axis=1)
        hi = base + remaining / n * np.max(np.where(unseen, 1 - mu, -np.inf), axis=1)
        past_var = (.25 + pred_m2) / t
        eta = np.minimum(100, epsilon / (past_var + epsilon ** 2))
        zero_var = (.25 + zero_m2) / t
        zero_eta = np.minimum(100, epsilon / (zero_var + epsilon ** 2))
        raw_base = successes / n
        probabilities = unseen / remaining
        cdf = np.cumsum(probabilities, axis=1)
        cdf[:, -1] = 1.
        indices = np.sum(cdf <= rng.random(trials)[:, None], axis=1)
        if not unseen[rows, indices].all():
            raise RuntimeError('Repeated query')
        y = np.asarray(oracle(indices), dtype=float)
        if y.shape != (trials,) or np.any((y != 0) & (y != 1)):
            raise ValueError('Exact binary target outcomes required')
        z = base + remaining / n * (y - mu[rows, indices])
        raw_z = raw_base + remaining / n * y
        for name, value, lower, upper, stake in (
                ('prediction_count_grid', z, lo, hi, eta),
                ('raw_count_grid', raw_z, raw_base, raw_base + remaining / n, zero_eta)):
            fp, fm = directional_factors(value, lower, upper, grid, stake, .9)
            if min(fp.min(), fm.min()) < .1 - 1e-10:
                raise RuntimeError('Factor positivity failed')
            plus[name] += np.log(fp)
            minus[name] += np.log(fm)
        wealth = {name: np.logaddexp(plus[name], minus[name]) - math.log(2) for name in plus}

        # All updates using the new label occur after the current prediction/stakes.
        xi = x[indices]
        a_ridge += xi[:, :, None] * xi[:, None, :]
        b_ridge += xi * (y - mean[indices])[:, None]
        score = full_mu[rows, indices]
        score_sum += score
        score_sq += score ** 2
        score_y += score * y
        y_sum += y
        diff = z - pred_mean
        pred_mean += diff / t
        pred_m2 += diff * (z - pred_mean)
        diff = raw_z - zero_mean
        zero_mean += diff / t
        zero_m2 += diff * (raw_z - zero_mean)
        successes += y.astype(int)
        unseen[rows, indices] = False
        log_raw = log_ppr(successes, t, n)
        masks['published_ppr95'] &= log_raw < threshold
        masks['ppr_reserve75'] &= log_raw < threshold - math.log(WEIGHT)
        possible = ((np.arange(n + 1)[None, :] >= successes[:, None]) &
                    (np.arange(n + 1)[None, :] <= successes[:, None] + n - t))
        for name in plus:
            masks[name] &= (wealth[name] < threshold) & possible
        current = {name: candidate_hull(masks[name], grid) for name in
                   ('published_ppr95', 'ppr_reserve75', 'prediction_count_grid', 'raw_count_grid')}
        strict_lo, strict_hi = current['ppr_reserve75']
        for mixture, branch in (('reserve_mix75', 'prediction_count_grid'), ('raw_reserve75', 'raw_count_grid')):
            log_mix = mixture_log_wealth(log_raw, wealth[branch], WEIGHT)
            masks[mixture] &= (log_mix < threshold) & masks['ppr_reserve75']
            mix_lo, mix_hi = candidate_hull(masks[mixture], grid)
            lower, upper, repaired = repair_empty_interval(mix_lo, mix_hi, strict_lo, strict_hi)
            repairs[mixture].append(repaired.copy() if t < n else np.zeros(trials, dtype=bool))
            current[mixture] = lower, upper
        for name, (lower, upper) in current.items():
            if t == n:
                lower = successes / n
                upper = lower.copy()
            run = runs[name]
            stop_now = ((run['stop'] == 0) & (upper >= lower) & (upper - lower <= 2 * epsilon + 1e-12))
            run['stop'][stop_now] = t
            run['stop_lower'][stop_now] = lower[stop_now]
            run['stop_upper'][stop_now] = upper[stop_now]
            run['lower'].append(lower.copy())
            run['upper'].append(upper.copy())
        for key, value in dict(selected=indices, prediction_strength=strength,
                               prediction_mu=mu[rows, indices], prediction_eta=eta,
                               zero_eta=zero_eta, prediction_lower=lo, prediction_upper=hi).items():
            diag[key].append(value.copy())
    for run in runs.values():
        run['lower'], run['upper'] = np.asarray(run['lower']), np.asarray(run['upper'])
    strict = runs['ppr_reserve75']
    for mixture in MIXTURES:
        run = runs[mixture]
        if (np.any(run['lower'] < strict['lower'] - 1e-12) or np.any(run['upper'] > strict['upper'] + 1e-12)
                or np.any(run['stop'] > strict['stop'])):
            raise RuntimeError('Reserved raw guarantee failed')
    diag = {key: np.asarray(value) for key, value in diag.items()}
    diag['repaired'] = np.stack([np.asarray(repairs[name]) for name in MIXTURES])
    return runs, diag
