"""Valid inference fallbacks on a single uniform query stream.

The primary gate is predictable and shared across candidate means. A fixed
wealth mixture pays an explicit log-budget penalty. All target scores enter
through the query-only oracle; no true target mean enters this module.
"""
from __future__ import annotations

import numpy as np
from safe_eval_v1 import reference_features, outer_interval
from safe_eval_v2 import directional_factors

METHODS = ('uniform_raw', 'stage2_trust', 'mixture50', 'mixture75',
           'predictable_gate', 'raw_reserve75', 'raw_cap90', 'raw_targeted')


def mixture_log_wealth(log_raw, log_prediction, raw_weight):
    if not 0 < raw_weight < 1:
        raise ValueError('mixture weight must be between zero and one')
    return np.logaddexp(np.log(raw_weight) + log_raw,
                        np.log1p(-raw_weight) + log_prediction)


def predictable_gate(score_sum, score_sq, score_y, y_sum, count,
                     anchors=12, slope_threshold=.5):
    """Past-only gate; no positive prior covariance is added to its score."""
    if count == 0:
        slope = np.zeros_like(score_sum)
        return ((count >= anchors) & (slope >= slope_threshold)).astype(float), slope
    if count < anchors:
        return np.zeros_like(score_sum), np.zeros_like(score_sum)
    sxx = np.maximum(0, score_sq - score_sum ** 2 / count)
    sxy = score_y - score_sum * y_sum / count
    slope = sxy / (.25 + sxx)
    return (slope >= slope_threshold).astype(float), slope


def evaluate_fallbacks(history, oracle, trials, seed=1, delta=.05, epsilon=.05,
                       grid_size=201, anchors=12, slope_threshold=.5):
    """All six comparisons share queries and update before the next outcome.

The gate chooses the current directional betting factors, not whichever
already observed interval is narrower. Previous wealth is retained. It is
not a calibrated shift detector and does not guarantee cost noninferiority.
"""
    history = np.asarray(history, dtype=float)
    if (history.ndim != 2 or min(history.shape) < 2 or
            not np.isfinite(history).all() or np.any((history < 0) | (history > 1))):
        raise ValueError('history must be a finite matrix in [0,1]')
    if not (0 < delta < 1 and 0 < epsilon < .5 and trials > 0 and grid_size >= 3):
        raise ValueError('invalid evaluation configuration')
    if not (0 <= anchors < history.shape[1] and np.isfinite(slope_threshold)):
        raise ValueError('invalid gate configuration')
    n = history.shape[1]
    mean, x, _ = reference_features(history)
    d = x.shape[1]
    rows = np.arange(trials)
    rng = np.random.default_rng(seed)
    grid = np.linspace(0, 1, grid_size)
    threshold = np.log(2 / delta)
    unseen = np.ones((trials, n), dtype=bool)
    observed_sum = np.zeros(trials)
    a_ridge = np.broadcast_to(np.diag([.25] + [1.] * (d - 1)), (trials, d, d)).copy()
    b_ridge = np.zeros((trials, d))
    score_sum, score_sq, score_y, y_sum = (np.zeros(trials) for _ in range(4))
    raw_mean, raw_m2, raw_sum = (np.zeros(trials) for _ in range(3))
    pred_mean, pred_m2, pred_sum, gate_sum = (np.zeros(trials) for _ in range(4))
    raw_plus = np.zeros((trials, grid_size)); raw_minus = raw_plus.copy()
    pred_plus = raw_plus.copy(); pred_minus = raw_plus.copy()
    gate_plus = raw_plus.copy(); gate_minus = raw_plus.copy()
    cap_plus = raw_plus.copy(); cap_minus = raw_plus.copy()
    targeted_plus = raw_plus.copy(); targeted_minus = raw_plus.copy()
    runs = {m: dict(lower=np.zeros(trials), upper=np.ones(trials),
                   stop=np.zeros(trials, dtype=int), stop_lower=np.full(trials, np.nan),
                   stop_upper=np.full(trials, np.nan), saved={k: [] for k in ('lower', 'upper', 'estimate')})
            for m in METHODS}
    diag = {k: [] for k in ('selected', 'prediction_strength', 'gate_prediction',
                            'gate_slope', 'raw_variance', 'prediction_variance')}
    for t in range(1, n + 1):
        remaining = n - t + 1
        count = t - 1
        strength = np.full(trials, .5)
        if count:
            sxx = np.maximum(0, score_sq - score_sum ** 2 / count)
            sxy = score_y - score_sum * y_sum / count
            strength = np.clip((.125 + sxy) / (.25 + sxx), 0, .5)
        use_prediction, gate_slope = predictable_gate(score_sum, score_sq, score_y,
                                                     y_sum, count, anchors, slope_threshold)
        beta = np.linalg.solve(a_ridge, b_ridge[..., None])[..., 0]
        full_mu = np.clip(mean + beta @ x.T, 0, 1)
        mu = .5 + strength[:, None] * (full_mu - .5)
        raw_base = observed_sum / n
        pred_base = (observed_sum + np.sum(unseen * mu, axis=1)) / n
        raw_lo, raw_hi = raw_base, raw_base + remaining / n
        pred_lo = pred_base - remaining / n * np.max(np.where(unseen, mu, -np.inf), axis=1)
        pred_hi = pred_base + remaining / n * np.max(np.where(unseen, 1 - mu, -np.inf), axis=1)
        raw_var, pred_var = (.25 + raw_m2) / t, (.25 + pred_m2) / t
        raw_eta = np.minimum(100, np.sqrt(2 * threshold / (t * raw_var)))
        pred_eta = np.minimum(100, epsilon / (pred_var + epsilon ** 2))

        p = unseen / remaining
        cdf = np.cumsum(p, axis=1)
        cdf[:, -1] = 1.
        idx = np.sum(cdf <= rng.random(trials)[:, None], axis=1)
        if not unseen[rows, idx].all():
            raise RuntimeError('duplicate query')
        y = np.asarray(oracle(idx), dtype=float)
        if y.shape != (trials,) or not np.isfinite(y).all() or np.any((y < 0) | (y > 1)):
            raise ValueError('oracle must return one score in [0,1] per trial')
        raw_z = raw_base + remaining / n * y
        pred_z = pred_base + remaining / n * (y - mu[rows, idx])
        rf_plus, rf_minus = directional_factors(raw_z, raw_lo, raw_hi, grid, raw_eta, .5)
        pf_plus, pf_minus = directional_factors(pred_z, pred_lo, pred_hi, grid, pred_eta, .9)
        cf_plus, cf_minus = directional_factors(raw_z, raw_lo, raw_hi, grid, raw_eta, .9)
        targeted_eta = np.minimum(100, epsilon / (raw_var + epsilon ** 2))
        tf_plus, tf_minus = directional_factors(raw_z, raw_lo, raw_hi, grid, targeted_eta, .9)
        gate_fp = (1 - use_prediction[:, None]) * rf_plus + use_prediction[:, None] * pf_plus
        gate_fm = (1 - use_prediction[:, None]) * rf_minus + use_prediction[:, None] * pf_minus
        if min(rf_plus.min(), rf_minus.min(), pf_plus.min(), pf_minus.min(),
               gate_fp.min(), gate_fm.min()) < .1 - 1e-10:
            raise RuntimeError('factor not bounded away from zero')
        raw_plus += np.log(rf_plus); raw_minus += np.log(rf_minus)
        pred_plus += np.log(pf_plus); pred_minus += np.log(pf_minus)
        gate_plus += np.log(gate_fp); gate_minus += np.log(gate_fm)
        cap_plus += np.log(cf_plus); cap_minus += np.log(cf_minus)
        targeted_plus += np.log(tf_plus); targeted_minus += np.log(tf_minus)

        # Update sufficient statistics only after the current factors consume y.
        xi = x[idx]
        a_ridge += xi[:, :, None] * xi[:, None, :]
        b_ridge += xi * (y - mean[idx])[:, None]
        score = full_mu[rows, idx]
        score_sum += score; score_sq += score ** 2
        score_y += score * y; y_sum += y
        unseen[rows, idx] = False
        observed_sum += y
        deterministic_l = observed_sum / n
        deterministic_u = (observed_sum + n - t) / n
        raw_sum += raw_z; pred_sum += pred_z
        gate_sum += (1 - use_prediction) * raw_z + use_prediction * pred_z
        raw_diff = raw_z - raw_mean
        raw_mean += raw_diff / t
        raw_m2 += raw_diff * (raw_z - raw_mean)
        pred_diff = pred_z - pred_mean
        pred_mean += pred_diff / t
        pred_m2 += pred_diff * (pred_z - pred_mean)
        wealth = {
            'uniform_raw': (raw_plus, raw_minus, threshold, raw_sum / t),
            'stage2_trust': (pred_plus, pred_minus, threshold, pred_sum / t),
            'predictable_gate': (gate_plus, gate_minus, threshold, gate_sum / t),
            # Same raw stakes, stricter threshold: pathwise comparison for the
            # fixed mixture's wealth-reserve guarantee, not a new tuned baseline.
            'raw_reserve75': (raw_plus, raw_minus, threshold - np.log(.75), raw_sum / t),
            'raw_cap90': (cap_plus, cap_minus, threshold, raw_sum / t),
            'raw_targeted': (targeted_plus, targeted_minus, threshold, raw_sum / t),
        }
        for name, raw_weight in [('mixture50', .5), ('mixture75', .75)]:
            wealth[name] = (mixture_log_wealth(raw_plus, pred_plus, raw_weight),
                            mixture_log_wealth(raw_minus, pred_minus, raw_weight), threshold,
                            (raw_weight * raw_sum + (1 - raw_weight) * pred_sum) / t)
        for name, (lp, lm, cutoff, estimate) in wealth.items():
            run = runs[name]
            lo, hi = outer_interval(lp, lm, grid, cutoff)
            run['lower'] = np.maximum.reduce([run['lower'], lo, deterministic_l])
            run['upper'] = np.minimum.reduce([run['upper'], hi, deterministic_u])
            if t == n:
                run['lower'] = deterministic_l.copy()
                run['upper'] = deterministic_l.copy()
                estimate = deterministic_l.copy()
            valid = run['upper'] >= run['lower']
            new_stop = ((run['stop'] == 0) & valid &
                        (run['upper'] - run['lower'] <= 2 * epsilon + 1e-12))
            run['stop'][new_stop] = t
            run['stop_lower'][new_stop] = run['lower'][new_stop]
            run['stop_upper'][new_stop] = run['upper'][new_stop]
            for key, value in [('lower', run['lower']), ('upper', run['upper']), ('estimate', estimate)]:
                run['saved'][key].append(value.copy())
        for key, value in dict(selected=idx, prediction_strength=strength,
                               gate_prediction=use_prediction, gate_slope=gate_slope,
                               raw_variance=raw_var, prediction_variance=pred_var).items():
            diag[key].append(value.copy())
    result = {}
    for name, run in runs.items():
        result[name] = {key: np.asarray(value) for key, value in run['saved'].items()}
        for key in ('stop', 'stop_lower', 'stop_upper'):
            result[name][key] = run[key]
    return result, {key: np.asarray(value) for key, value in diag.items()}
