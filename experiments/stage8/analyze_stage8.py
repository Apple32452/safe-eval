"""Audit saved paths and replay model-free inference independently of the engine."""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from stage8_common import (STAGE7, METHODS, MIXTURES, PAIRS, SCENARIOS, METRICS, DELTA,
                           EPSILON, WEIGHT, verify_protocol, build_cases, read_csv,
                           unpack_curves, decisions, target_record, aggregate, write_csv)
from binary_control import log_ppr, ppr_interval
from analyze_stage7 import same_confidence_sets
from stage7_experiment import load_stage6_reference


def replay_model_free(selected, outcomes, seed=None, delta=DELTA):
    """Rebuild raw PPR and zero-trust capital; never call evaluate_matched.

    A provided seed additionally verifies the original uniform RNG ledger.
    With seed=None a fixed permutation ledger is accepted for exact enumeration.
    """
    selected = np.asarray(selected)
    n, repeats = selected.shape
    if not np.array_equal(np.sort(selected, axis=0), np.broadcast_to(np.arange(n)[:, None], selected.shape)):
        raise ValueError('Ledger is not a collection of complete unique permutations')
    grid = np.arange(n + 1) / n
    rng = np.random.default_rng(seed) if seed is not None else None
    rows = np.arange(repeats)
    unseen = np.ones((repeats, n), dtype=bool)
    successes = np.zeros(repeats, dtype=int)
    z_mean, z_m2 = np.zeros(repeats), np.zeros(repeats)
    plus, minus = np.zeros((repeats, n + 1)), np.zeros((repeats, n + 1))
    raw_current = {m: (np.zeros(repeats), np.ones(repeats)) for m in ('published_ppr95', 'ppr_reserve75')}
    zero_mask = np.ones((repeats, n + 1), dtype=bool)
    strict_mask, mixture_mask = zero_mask.copy(), zero_mask.copy()
    curves = {m: [] for m in ('published_ppr95', 'ppr_reserve75', 'raw_count_grid', 'raw_reserve75')}
    repaired = []
    threshold = math.log(1 / delta)

    def hull(mask):
        exists = mask.any(axis=1)
        low_index = mask.argmax(axis=1)
        high_index = n - mask[:, ::-1].argmax(axis=1)
        return np.where(exists, low_index / n, 1.), np.where(exists, high_index / n, 0.)

    for t in range(1, n + 1):
        remaining = n - t + 1
        index = selected[t - 1]
        if rng is not None:
            cdf = np.cumsum(unseen / remaining, axis=1)
            cdf[:, -1] = 1.
            expected = np.sum(cdf <= rng.random(repeats)[:, None], axis=1)
            if not np.array_equal(index, expected):
                raise ValueError('Saved ledger differs from the seeded uniform draw')
        low, high = successes / n, (successes / n) + remaining / n
        z = low + remaining / n * outcomes[index]
        eta = np.minimum(100., EPSILON / ((.25 + z_m2) / t + EPSILON ** 2))
        lambda_plus = np.minimum(eta[:, None], .9 / np.maximum(grid[None, :] - low[:, None], 1e-12))
        lambda_minus = np.minimum(eta[:, None], .9 / np.maximum(high[:, None] - grid[None, :], 1e-12))
        plus += np.log(1 + lambda_plus * (z[:, None] - grid[None, :]))
        minus += np.log(1 - lambda_minus * (z[:, None] - grid[None, :]))
        zero_wealth = np.logaddexp(plus, minus) - math.log(2)
        diff = z - z_mean
        z_mean += diff / t
        z_m2 += diff * (z - z_mean)
        successes += outcomes[index].astype(int)
        unseen[rows, index] = False
        values, inverse = np.unique(successes, return_inverse=True)
        for method, error in (('published_ppr95', delta), ('ppr_reserve75', delta * WEIGHT)):
            lo, hi = ppr_interval(values, t, n, error)
            previous_lo, previous_hi = raw_current[method]
            lo, hi = np.maximum(previous_lo, lo[inverse]), np.minimum(previous_hi, hi[inverse])
            if t == n:
                lo = successes / n
                hi = lo.copy()
            raw_current[method] = lo, hi
            curves[method].append(np.stack([lo, hi]))
        raw_wealth = log_ppr(successes, t, n)
        strict_mask &= raw_wealth < threshold - math.log(WEIGHT)
        possible = (np.arange(n + 1)[None, :] >= successes[:, None]) & (np.arange(n + 1)[None, :] <= successes[:, None] + n - t)
        zero_mask &= (zero_wealth < threshold) & possible
        mixture_wealth = np.logaddexp(math.log(WEIGHT) + raw_wealth, math.log(1 - WEIGHT) + zero_wealth)
        mixture_mask &= (mixture_wealth < threshold) & strict_mask
        zl, zu = hull(zero_mask)
        ml, mu = hull(mixture_mask)
        sl, su = hull(strict_mask)
        empty = ml > mu
        ml, mu = np.where(empty, sl, ml), np.where(empty, su, mu)
        if t == n:
            zl = ml = successes / n
            zu, mu = zl.copy(), ml.copy()
            empty = np.zeros(repeats, dtype=bool)
        curves['raw_count_grid'].append(np.stack([zl, zu]))
        curves['raw_reserve75'].append(np.stack([ml, mu]))
        repaired.append(empty)
    return {m: np.asarray(v).transpose(1, 0, 2) for m, v in curves.items()}, np.asarray(repaired)


def check_value(actual, expected, name):
    if isinstance(expected, (int, float, np.integer, np.floating)):
        if not math.isclose(float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError('Saved value differs: ' + name)
    elif actual != expected:
        raise ValueError('Saved metadata differs: ' + name)


def audit_output(output):
    output = Path(output)
    lock, datasets = verify_protocol()
    meta = json.loads((output / 'run_metadata.json').read_text())
    if meta['status'] != 'complete' or meta['protocol_lock'] != lock or tuple(meta['methods']) != METHODS:
        raise ValueError('Run or protocol is incomplete or changed')
    repeats = meta['repeats']
    expected_cases = {c['case_id']: (c, h, y) for c, h, y in build_cases(datasets)}
    if len(meta['cases']) != len(expected_cases) or {c['case_id'] for c in meta['cases']} != set(expected_cases):
        raise ValueError('Wrong case set')
    trials = read_csv(output / 'per_trial.csv')
    grouped = defaultdict(list)
    for row in trials:
        grouped[(row['case_id'], row['method'])].append(row)
    if len(trials) != len(expected_cases) * repeats * len(METHODS) or len(grouped) != len(expected_cases) * len(METHODS):
        raise ValueError('Missing or duplicated method paths')
    old = {(r['case_id'], r['method']): r for r in read_csv(STAGE7 / 'results_reference/by_target.csv')}
    reference, comparator = load_stage6_reference()
    reference_cases = {c['case_id']: c for c in reference['cases']}
    raw_cache, targets, all_decisions = {}, [], {}
    checked = bounds = paired = old_values = 0
    maximum_history_extra = maximum_raw_extra = 0
    for case in meta['cases']:
        expected, history, outcomes = expected_cases[case['case_id']]
        if case != expected:
            raise ValueError('Case or target-excluded history differs')
        with np.load(output / 'curves' / (case['case_id'] + '.npz'), allow_pickle=False) as saved:
            trace = {name: saved[name] for name in saved.files}
        curves = unpack_curves(trace)
        selected = trace['selected']
        if selected.shape != (case['n'], repeats):
            raise ValueError('Wrong query dimensions')
        key = case['language_pair'], case['target_system']
        if key not in raw_cache:
            rebuilt, repaired = replay_model_free(selected, outcomes, case['raw_seed'])
            raw_cache[key] = selected.copy(), rebuilt, repaired
        cached_selected, rebuilt, repaired = raw_cache[key]
        if not np.array_equal(selected, cached_selected):
            raise ValueError('Query stream changes with historical scenario')
        for method, reconstructed in rebuilt.items():
            if not same_confidence_sets(curves[method], reconstructed):
                raise ValueError('Independent model-free replay differs: ' + method)
        if not np.array_equal(trace['repaired'][0], repaired):
            raise ValueError('Model-free repair flags differ')
        digest = hashlib.sha256(np.asarray(selected, dtype='<i4').tobytes()).hexdigest()
        if digest != meta['raw_stream_sha256'][case['case_id']]:
            raise ValueError('Saved query hash differs')
        if repeats == 100 and digest != reference_cases[case['case_id']]['raw_stream_sha256']:
            raise ValueError('Stage 6/7 query path differs')
        truth = float(outcomes.mean())
        case_decisions = {method: decisions(curves[method], truth) for method in METHODS}
        raw_stop = case_decisions['published_ppr95']['stop_queries']
        if repeats == 100:
            np.testing.assert_array_equal(raw_stop, [comparator[(case['case_id'], j)]['raw95'] for j in range(repeats)])
            paired += repeats
        strict = curves['ppr_reserve75']
        for method in MIXTURES:
            if np.any(curves[method][0] < strict[0] - 1e-12) or np.any(curves[method][1] > strict[1] + 1e-12):
                raise ValueError('Reserved raw containment failed')
            if np.any(case_decisions[method]['stop_queries'] > case_decisions['ppr_reserve75']['stop_queries']):
                raise ValueError('Reserved stopping bound failed')
            bounds += repeats
        maximum_raw_extra = max(maximum_raw_extra, int((case_decisions['reserve_mix75']['stop_queries'] - raw_stop).max()))
        maximum_history_extra = max(maximum_history_extra, int((case_decisions['reserve_mix75']['stop_queries'] - case_decisions['raw_reserve75']['stop_queries']).max()))
        for method in METHODS:
            decision = case_decisions[method]
            repair = np.zeros(repeats, dtype=int)
            if method in MIXTURES:
                flags = trace['repaired'][MIXTURES.index(method)]
                repair = (flags & (np.arange(case['n'])[:, None] < decision['stop_queries'][None, :])).any(axis=0).astype(int)
            saved = sorted(grouped[(case['case_id'], method)], key=lambda r: int(r['repeat']))
            if [int(r['repeat']) for r in saved] != list(range(repeats)):
                raise ValueError('Repeated trial identifier')
            for j, row in enumerate(saved):
                for field, values in decision.items():
                    check_value(row[field], values[j], field)
                for field, expected_value in dict(true_mean=truth, repair_before_stop=repair[j], n=case['n']).items():
                    check_value(row[field], expected_value, field)
                for field in ('case_id', 'scenario', 'language_pair', 'target_system'):
                    check_value(row[field], case[field], field)
                checked += 1
            record = target_record(case, method, decision, repair)
            targets.append(record)
            all_decisions[(case['case_id'], method)] = decision
            if repeats == 100 and method in ('published_ppr95', 'ppr_reserve75', 'prediction_count_grid', 'reserve_mix75'):
                previous = old[(case['case_id'], method)]
                for field in METRICS:
                    check_value(previous[field], record[field], field)
                    old_values += 1
    lookup = {(r['case_id'], r['method']): r for r in targets}
    saved_targets = read_csv(output / 'by_target.csv')
    if len(saved_targets) != len(targets) or len({(r['case_id'], r['method']) for r in saved_targets}) != len(targets):
        raise ValueError('Wrong aggregate target identifiers')
    for row in saved_targets:
        for field, expected_value in lookup[(row['case_id'], row['method'])].items():
            check_value(row[field], expected_value, field)
    summary = aggregate(targets)
    summary_lookup = {(r['scenario'], r['language_pair'], r['method']): r for r in summary}
    saved_summary = read_csv(output / 'summary.csv')
    if len(saved_summary) != len(summary):
        raise ValueError('Wrong scenario summary count')
    for row in saved_summary:
        for field, expected_value in summary_lookup[(row['scenario'], row['language_pair'], row['method'])].items():
            check_value(row[field], expected_value, field)
    verification = dict(all_checks_passed=True, saved_decisions_checked=checked,
                        reserved_stopping_bounds_checked=bounds, model_free_target_streams_replayed=len(raw_cache),
                        full_case_curves_audited=len(meta['cases']), stage6_paired_raw_stops_checked=paired,
                        stage7_target_metric_values_checked=old_values,
                        largest_primary_extra_vs_raw95=maximum_raw_extra,
                        largest_primary_extra_vs_matched_zero=maximum_history_extra,
                        scope='Fixed WMT23 development pools and query randomizations; no new method or untouched validation')
    return meta, all_decisions, verification


def comparisons(meta, all_decisions):
    output = []
    repeats = meta['repeats']
    pairs = sorted({c['language_pair'] for c in meta['cases']})
    for scenario in SCENARIOS:
        for predicted, control in PAIRS:
            family = 'reserve75' if predicted == 'reserve_mix75' else 'standalone'
            language_arrays = []
            for pair in pairs:
                cases = [c for c in meta['cases'] if c['scenario'] == scenario and c['language_pair'] == pair]
                stacks = [np.stack([all_decisions[(c['case_id'], m)]['stop_queries'] for c in cases])
                          for m in ('published_ppr95', control, predicted)]
                language_arrays.append(tuple(array.mean(axis=0) for array in stacks))
                output.append(comparison_row(scenario, pair, family, stacks, repeats))
            stacks = [np.stack([a[index] for a in language_arrays]) for index in range(3)]
            output.append(comparison_row(scenario, 'equal_language_overall', family, stacks, repeats))
    return output


def comparison_row(scenario, pair, family, arrays, repeats):
    raw, zero, pred = arrays
    raw_mean, zero_mean, pred_mean = (float(a.mean()) for a in arrays)
    difference = (pred - zero).mean(axis=0)
    mcse = float(difference.std(ddof=1) / math.sqrt(repeats)) if repeats > 1 else float('nan')
    return dict(scenario=scenario, language_pair=pair, family=family,
                raw95_mean_queries=raw_mean, zero_mean_queries=zero_mean, prediction_mean_queries=pred_mean,
                history_increment_labels=pred_mean - zero_mean,
                history_increment_percent_vs_zero=100 * (pred_mean / zero_mean - 1),
                model_free_change_percent_vs_raw95=100 * (zero_mean / raw_mean - 1),
                history_increment_percent_vs_raw95=100 * (pred_mean - zero_mean) / raw_mean,
                total_prediction_change_percent_vs_raw95=100 * (pred_mean / raw_mean - 1),
                conditional_query_randomization_mcse_labels=mcse,
                mcse_scope='Query randomization on fixed pools; unavailable for one-repeat software checks')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='results/stage8_local')
    args = parser.parse_args()
    output = Path(args.input)
    meta, audited, verification = audit_output(output)
    write_csv(output / 'comparison.csv', comparisons(meta, audited))
    (output / 'VERIFICATION.json').write_text(json.dumps(verification, indent=2))
    from plot_stage8 import plot
    plot(output)
    print(f"Checked {verification['saved_decisions_checked']} saved decisions and {verification['reserved_stopping_bounds_checked']} reserved stopping bounds; "
          f"replayed {verification['model_free_target_streams_replayed']} model-free target streams and matched {verification['stage7_target_metric_values_checked']} Stage 7 metrics; wrote comparisons and figures.")


if __name__ == '__main__':
    main()
