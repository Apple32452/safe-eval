"""Binary finite-pool wealth reserve with an explicit empty-set fallback.

Fixed-weight mixtures of valid e-processes are standard constructions, not a
novelty claim. Raw capital is the published binary PPR process; prediction
capital averages the two unchanged Stage 2 directional betting processes.

On the SAME uniform query stream, each output is a subset of the stricter raw
CS at error level delta*w. If the mixture set becomes empty we return that raw
CS, preserving a superset of the mixture confidence set. This gives both
nominal 1-delta anytime coverage and an all-path precision-stop bound against
the stricter raw control. It does NOT bound extra queries versus raw at delta.
"""
from __future__ import annotations
import math
import numpy as np
from binary_control import log_ppr
from safe_eval_v1 import reference_features, outer_interval
from safe_eval_v2 import directional_factors
from safe_eval_v3 import mixture_log_wealth, predictable_gate

WEIGHTS = (.5, .75, .9)
METHODS = ('published_ppr95', 'legacy_trust201', 'legacy_gate201', 'prediction_count_grid',
           'reserve_mix50', 'reserve_mix75', 'reserve_mix90',
           'ppr_reserve50', 'ppr_reserve75', 'ppr_reserve90')


def candidate_hull(accepted, grid):
    """The hull contains every accepted discrete count, including disconnected sets."""
    accepted = np.asarray(accepted, dtype=bool)
    grid = np.asarray(grid)
    if accepted.ndim != 2 or accepted.shape[1] != len(grid):
        raise ValueError('candidate mask and grid shape mismatch')
    lower = np.min(np.where(accepted, grid, np.inf), axis=1)
    upper = np.max(np.where(accepted, grid, -np.inf), axis=1)
    nonempty = accepted.any(axis=1)
    return np.where(nonempty, lower, 1.), np.where(nonempty, upper, 0.)


def repair_empty_interval(mix_lower, mix_upper, raw_lower, raw_upper):
    """A superset of the mixture set and a subset of the reserved raw interval.

    No true target mean is inspected. Output intervals can widen at a repair;
    nestedness is not required for simultaneous coverage.
    """
    empty = mix_upper < mix_lower
    return (np.where(empty, raw_lower, mix_lower),
            np.where(empty, raw_upper, mix_upper), empty)


def evaluate_reserved(history, oracle, trials, seed=1, delta=.05, epsilon=.05):
    history = np.asarray(history, dtype=float)
    if (history.ndim != 2 or min(history.shape) < 2 or not np.isfinite(history).all()
            or np.any((history < 0) | (history > 1))):
        raise ValueError('historical matrix must be finite and bounded in [0,1]')
    if trials < 1 or not 0 < delta < 1 or not 0 < epsilon < .5:
        raise ValueError('invalid inference configuration')
    n = history.shape[1]
    mean, x, _ = reference_features(history)
    d = x.shape[1]
    grid = np.arange(n + 1) / n
    legacy_grid = np.linspace(0, 1, 201)
    threshold = math.log(1 / delta)
    legacy_threshold = math.log(2 / delta)
    rng = np.random.default_rng(seed); rows = np.arange(trials)
    unseen = np.ones((trials, n), dtype=bool)
    successes = np.zeros(trials, dtype=int)
    a_ridge = np.broadcast_to(np.diag([.25] + [1.] * (d - 1)), (trials, d, d)).copy()
    b_ridge = np.zeros((trials, d))
    score_sum, score_sq, score_y, y_sum = (np.zeros(trials) for _ in range(4))
    pred_mean, pred_m2 = np.zeros(trials), np.zeros(trials)
    raw_mean, raw_m2 = np.zeros(trials), np.zeros(trials)
    plus = np.zeros((trials, n + 1)); minus = plus.copy()
    legacy_plus = np.zeros((trials, 201)); legacy_minus = legacy_plus.copy()
    gate_plus = legacy_plus.copy(); gate_minus = legacy_plus.copy()
    masks = {method: np.ones((trials, n + 1), dtype=bool) for method in METHODS
             if method not in ('legacy_trust201', 'legacy_gate201')}
    intervals = {method: (np.zeros(trials), np.ones(trials)) for method in METHODS}
    runs = {method: dict(stop=np.zeros(trials, dtype=int), stop_lower=np.full(trials, np.nan),
                        stop_upper=np.full(trials, np.nan), lower=[], upper=[]) for method in METHODS}
    diag = {k: [] for k in ('selected', 'prediction_strength', 'legacy_gate', 'legacy_gate_slope')}
    repair_ever = {f'reserve_mix{int(100*w)}': np.zeros(trials, dtype=bool) for w in WEIGHTS}
    repairs = {name: np.zeros(trials, dtype=int) for name in repair_ever}
    repair_before_stop = {name: np.zeros(trials, dtype=bool) for name in repair_ever}
    for t in range(1, n + 1):
        count, remaining = t - 1, n - t + 1
        strength = np.full(trials, .5)
        if count:
            sxx = np.maximum(0, score_sq - score_sum ** 2 / count)
            sxy = score_y - score_sum * y_sum / count
            strength = np.clip((.125 + sxy) / (.25 + sxx), 0, .5)
        gate, slope = predictable_gate(score_sum, score_sq, score_y, y_sum, count, 12, .5)
        beta = np.linalg.solve(a_ridge, b_ridge[..., None])[..., 0]
        full_mu = np.clip(mean + beta @ x.T, 0, 1)
        mu = .5 + strength[:, None] * (full_mu - .5)
        base = (successes + np.sum(unseen * mu, axis=1)) / n
        lo = base - remaining / n * np.max(np.where(unseen, mu, -np.inf), axis=1)
        hi = base + remaining / n * np.max(np.where(unseen, 1 - mu, -np.inf), axis=1)
        past_var = (.25 + pred_m2) / t
        eta = np.minimum(100, epsilon / (past_var + epsilon ** 2))
        raw_var = (.25 + raw_m2) / t
        raw_eta = np.minimum(100, np.sqrt(2 * legacy_threshold / (t * raw_var)))
        raw_base = successes / n
        probabilities = unseen / remaining
        cdf = np.cumsum(probabilities, axis=1); cdf[:, -1] = 1.
        indices = np.sum(cdf <= rng.random(trials)[:, None], axis=1)
        if not unseen[rows, indices].all():
            raise RuntimeError('duplicate target query')
        y = np.asarray(oracle(indices), dtype=float)
        if y.shape != (trials,) or np.any((y != 0) & (y != 1)):
            raise ValueError('this reserve construction requires exact binary target outcomes')
        z = base + remaining / n * (y - mu[rows, indices])
        raw_z = raw_base + remaining / n * y
        fp, fm = directional_factors(z, lo, hi, grid, eta, .9)
        lfp, lfm = directional_factors(z, lo, hi, legacy_grid, eta, .9)
        rfp, rfm = directional_factors(raw_z, raw_base, raw_base + remaining / n,
                                     legacy_grid, raw_eta, .5)
        if min(fp.min(), fm.min(), lfp.min(), lfm.min()) < .1 - 1e-10:
            raise RuntimeError('prediction factor lost positivity')
        plus += np.log(fp); minus += np.log(fm)
        legacy_plus += np.log(lfp); legacy_minus += np.log(lfm)
        gate_plus += np.log((1 - gate[:, None]) * rfp + gate[:, None] * lfp)
        gate_minus += np.log((1 - gate[:, None]) * rfm + gate[:, None] * lfm)
        log_prediction = np.logaddexp(plus, minus) - math.log(2)

        # Current outcome changes model/stake statistics only for the next query.
        xi = x[indices]
        a_ridge += xi[:, :, None] * xi[:, None, :]
        b_ridge += xi * (y - mean[indices])[:, None]
        score = full_mu[rows, indices]
        score_sum += score; score_sq += score ** 2; score_y += score * y; y_sum += y
        diff = z - pred_mean; pred_mean += diff / t; pred_m2 += diff * (z - pred_mean)
        diff = raw_z - raw_mean; raw_mean += diff / t; raw_m2 += diff * (raw_z - raw_mean)
        successes += y.astype(int); unseen[rows, indices] = False
        deterministic_l, deterministic_u = successes / n, (successes + n - t) / n
        log_raw = log_ppr(successes, t, n)
        masks['published_ppr95'] &= log_raw < threshold
        possible = ((np.arange(n + 1)[None, :] >= successes[:, None]) &
                    (np.arange(n + 1)[None, :] <= successes[:, None] + n - t))
        masks['prediction_count_grid'] &= (log_prediction < threshold) & possible
        current = {name: candidate_hull(masks[name], grid) for name in ('published_ppr95', 'prediction_count_grid')}
        for weight in WEIGHTS:
            suffix = str(int(100 * weight)); raw_name = 'ppr_reserve' + suffix
            mix_name = 'reserve_mix' + suffix
            masks[raw_name] &= log_raw < threshold - math.log(weight)
            log_mix = mixture_log_wealth(log_raw, log_prediction, weight)
            # The raw-mask intersection is redundant in exact arithmetic and
            # preserves numerical containment at a floating-point boundary.
            masks[mix_name] &= (log_mix < threshold) & masks[raw_name]
            raw_l, raw_u = candidate_hull(masks[raw_name], grid)
            mix_l, mix_u = candidate_hull(masks[mix_name], grid)
            output_l, output_u, repaired = repair_empty_interval(mix_l, mix_u, raw_l, raw_u)
            if t < n:
                repair_ever[mix_name] |= repaired; repairs[mix_name] += repaired
                repair_before_stop[mix_name] |= repaired & (runs[mix_name]['stop'] == 0)
            current[raw_name] = raw_l, raw_u
            current[mix_name] = output_l, output_u
        for name, lp, lm in (('legacy_trust201', legacy_plus, legacy_minus), ('legacy_gate201', gate_plus, gate_minus)):
            new_l, new_u = outer_interval(lp, lm, legacy_grid, legacy_threshold)
            old_l, old_u = intervals[name]
            current[name] = (np.maximum.reduce([old_l, new_l, deterministic_l]),
                             np.minimum.reduce([old_u, new_u, deterministic_u]))
        for name, (lower, upper) in current.items():
            if t == n:
                lower, upper = deterministic_l.copy(), deterministic_l.copy()
            intervals[name] = lower, upper
            run = runs[name]
            stop_now = ((run['stop'] == 0) & (upper >= lower) & (upper - lower <= 2 * epsilon + 1e-12))
            run['stop'][stop_now] = t; run['stop_lower'][stop_now] = lower[stop_now]; run['stop_upper'][stop_now] = upper[stop_now]
            run['lower'].append(lower.copy()); run['upper'].append(upper.copy())
        for key, value in dict(selected=indices, prediction_strength=strength, legacy_gate=gate, legacy_gate_slope=slope).items():
            diag[key].append(value.copy())
    for name, run in runs.items():
        run['lower'], run['upper'] = np.asarray(run['lower']), np.asarray(run['upper'])
    for weight in WEIGHTS:
        suffix = str(int(100 * weight)); mix, raw = runs['reserve_mix' + suffix], runs['ppr_reserve' + suffix]
        if (np.any(mix['lower'] < raw['lower'] - 1e-12) or np.any(mix['upper'] > raw['upper'] + 1e-12)
                or np.any(mix['stop'] > raw['stop'])):
            raise RuntimeError('all-path reserved-raw interval or stopping bound failed')
    diag = {key: np.asarray(value) for key, value in diag.items()}
    diag['repair_ever'] = repair_ever; diag['repair_time_count'] = repairs
    diag['repair_before_stop_ever'] = repair_before_stop
    return runs, diag
