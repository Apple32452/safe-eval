"""Independent replay of every saved paired decision and capital update."""
from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path

import numpy as np

from paired_engine import Q, P, CAP, METHODS, LEVELS
from paired_reference import raw_at_modes, rational_factors
from stage13_common import build_cases, ledger_for, verify_lock


def replay_capital(saved, differences, states):
    """Reconstruct factors independently, with Python-object integer products."""
    n, repeats = differences.shape
    wealth = np.full((4, 2, 8, repeats), Q, dtype=object)
    cumulative = np.zeros(repeats, dtype=np.int64)
    quantum_checks = 0
    for time in range(n):
        r = n - time
        summary = np.concatenate([
            np.stack([P * cumulative, np.zeros(repeats, dtype=np.int64),
                      np.zeros(repeats, dtype=np.int64), np.zeros(repeats, dtype=np.int64)])[None],
            states[:, :, time]], axis=0)
        for method in range(4):
            center, minimum, maximum, queried = summary[method]
            z = center + r * (P * differences[time] - queried)
            lower = center - r * (P + maximum)
            upper = center + r * (P - minimum)
            if np.any(z < lower) or np.any(z > upper):
                raise AssertionError('Invalid predictable support')
            for side, sign in enumerate((1, -1)):
                bound = lower if side == 0 else -upper
                numerator = (2 ** np.arange(8, dtype=np.int64))[:, None]
                denominator = np.full((8, repeats), 8, dtype=np.int64)
                active_cap = (bound < 0) & (2 * numerator * (-bound) > denominator * n * P)
                numerator = np.where(active_cap, n * P, numerator)
                denominator = np.where(active_cap, -2 * bound, denominator)
                # Deliberately use Python big integers and unreduced rational
                # stakes instead of the engine's fixed-width factor form.
                top = denominator.astype(object) * n * P + numerator.astype(object) * sign * z
                bottom = denominator.astype(object) * n * P
                old = wealth[method, side]
                updated = old * top // bottom
                wealth[method, side] = np.where(old >= CAP, CAP, np.minimum(CAP, updated))
            average = np.asarray(wealth[method].sum(axis=1) // 8, dtype=np.int64)
            np.testing.assert_array_equal(average, saved[method, :, time])
            # Exact Fraction spot checks exercise both signs and all stake experts.
            if time in {0, n // 3, 2 * n // 3, n - 1}:
                ref = rational_factors(int(z[0]), int(lower[0]), int(upper[0]), n, P)
                if any(f < .5 for row in ref for f in row):
                    raise AssertionError('Invalid factor cap')
                quantum_checks += 16
        cumulative += differences[time]
    return 4 * 2 * 8 * n * repeats, quantum_checks


def check_predictions(trace, histories, labels):
    labels = np.asarray(labels, dtype=np.int64)
    ledger, states = trace['ledger'], trace['states']
    n, repeats = ledger.shape
    rows = np.arange(repeats)
    unseen = np.ones((repeats, n), dtype=bool)
    sums = np.zeros(repeats, dtype=np.int64)
    matrices, vectors = [], []
    for j in range(3):
        np.testing.assert_array_equal(trace['feature_means'][j], histories[j].mean(axis=0))
        x = trace['feature_matrices'][j]
        np.testing.assert_array_equal(x[:, 0], 1)
        # Validate the retained right-singular subspace without relying on SVD signs.
        centered = histories[j] - histories[j].mean(axis=0)
        basis = x[:, 1:] / np.sqrt(n)
        np.testing.assert_allclose(basis.T @ basis, np.eye(basis.shape[1]), atol=1e-10)
        eigenvalues = np.linalg.eigvalsh(centered @ centered.T)[::-1][:basis.shape[1]]
        np.testing.assert_allclose(np.linalg.eigvalsh((centered @ basis).T @ (centered @ basis))[::-1],
                                   np.maximum(eigenvalues, 0), atol=1e-8)
        matrices.append(np.broadcast_to(np.diag([.25] + [1.] * (x.shape[1] - 1)),
                                       (repeats, x.shape[1], x.shape[1])).copy())
        vectors.append(np.zeros((repeats, x.shape[1], 2)))
    for time, index in enumerate(ledger):
        for j in range(3):
            x, mean = trace['feature_matrices'][j], trace['feature_means'][j]
            coefficients = np.linalg.solve(matrices[j], vectors[j])
            raw = np.clip(mean[None, :, None] + np.einsum('id,rdk->rik', x, coefficients), 0, 1)
            quantized = np.rint(P * .5 * (raw[:, :, 0] - raw[:, :, 1])).astype(np.int64)
            expected = np.stack([P * sums + (quantized * unseen).sum(axis=1),
                                 np.where(unseen, quantized, P + 1).min(axis=1),
                                 np.where(unseen, quantized, -P - 1).max(axis=1),
                                 quantized[rows, index]])
            np.testing.assert_array_equal(expected, states[j, :, time])
            current = labels[:, index].T
            xi = x[index]
            matrices[j] += xi[:, :, None] * xi[:, None, :]
            vectors[j] += xi[:, :, None] * (current - mean[index, None])[:, None, :]
        sums += labels[0, index] - labels[1, index]
        unseen[rows, index] = False


def replay_decisions(trace, observed):
    n, repeats = observed.shape
    expected_stop = np.full((6, 2, repeats), n, dtype=np.int16)
    expected_direction = np.zeros((6, 2, repeats), dtype=np.int8)
    accumulated = np.zeros(repeats, dtype=int)
    undecided = np.ones((6, 2, repeats), dtype=bool)
    for time in range(n):
        accumulated += observed[time]
        certainty = np.where(accumulated > n-time-1, 1,
                             np.where(accumulated < -(n-time-1), -1, 2))
        if time == n - 1:
            certainty = np.sign(accumulated)
        for method in range(6):
            if method:
                evidence = trace['raw'][:, time] if method == 1 else (
                    3 * trace['raw'][:, time] + trace['bets'][method-2, :, time]) // 4
            for level, threshold in enumerate((40 * Q, CAP)):
                result = certainty.copy()
                if method:
                    first = (evidence[0] >= threshold) & (evidence[1] < threshold)
                    second = (evidence[1] >= threshold) & (evidence[0] < threshold)
                    result = np.where((result == 2) & first, 1, result)
                    result = np.where((result == 2) & second, -1, result)
                newly = undecided[method, level] & (result != 2)
                expected_stop[method, level, newly] = time + 1
                expected_direction[method, level, newly] = result[newly]
                undecided[method, level, newly] = False
    np.testing.assert_array_equal(expected_stop, trace['stop'])
    np.testing.assert_array_equal(expected_direction, trace['direction'])
    if undecided.any():
        raise AssertionError('Unresolved at complete evaluation')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    args = parser.parse_args()
    directory = Path(args.input)
    metadata = json.loads((directory / 'run_metadata.json').read_text())
    if metadata['frozen_protocol'] != verify_lock():
        raise ValueError('Protocol mismatch')
    cases, _ = build_cases()
    lookup = {case[0]['case_id']: case for case in cases}
    counts = dict(pairs=0, saved_decisions=0, raw_states=0, integer_expert_updates=0,
                  fraction_factor_checks=0, paired_query_steps=0)
    raw_reference = lru_cache(maxsize=200000)(raw_at_modes)
    compact = []
    for record in metadata['cases']:
        meta, histories, labels = lookup[record['case_id']]
        labels = labels.astype(np.int64)
        if any(record[key] != meta[key] for key in meta):
            raise ValueError('Case/history provenance mismatch')
        path = directory / 'traces' / (record['case_id'] + '.npz')
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['trace_sha256']:
            raise ValueError('Trace checksum mismatch')
        with np.load(path, allow_pickle=False) as z:
            trace = {key: z[key] for key in z.files}
        n, repeats = trace['ledger'].shape
        if repeats != metadata['repeats'] or n != meta['n']:
            raise ValueError('Wrong ledger dimensions')
        np.testing.assert_array_equal(trace['ledger'], ledger_for(n, repeats, meta['seed']))
        observed = labels[0, trace['ledger']] - labels[1, trace['ledger']]
        count_plus = np.cumsum(observed == 1, axis=0)
        count_minus = np.cumsum(observed == -1, axis=0)
        count_equal = np.cumsum(observed == 0, axis=0)
        for time in range(n):
            unique, inverse = np.unique(np.stack([count_plus[time], count_minus[time], count_equal[time]], axis=1),
                                        axis=0, return_inverse=True)
            expected = np.array([[raw_reference(n, int(a), int(b), int(c), Q, CAP),
                                  raw_reference(n, int(b), int(a), int(c), Q, CAP)] for a, b, c in unique]).T
            np.testing.assert_array_equal(trace['raw'][:, time], expected[:, inverse])
            counts['raw_states'] += 2 * len(unique)
        check_predictions(trace, histories, labels)
        updates, fractions = replay_capital(trace['bets'], observed, trace['states'])
        replay_decisions(trace, observed)
        checkpoints = np.maximum(1, (n * np.array([.25, .5, .75])).astype(int))
        np.testing.assert_array_equal(trace['checkpoints'], checkpoints)
        np.testing.assert_array_equal(trace['naive'], np.sign(np.cumsum(observed, axis=0)[checkpoints - 1]))
        truth = int(np.sign((labels[0] - labels[1]).sum()))
        if np.any(trace['direction'][trace['stop'] == n] != truth):
            raise AssertionError('Incorrect full-budget conclusion')
        compact.append({key: trace[key] for key in ('stop', 'direction', 'checkpoints', 'naive')})
        counts['pairs'] += 1
        counts['saved_decisions'] += int(trace['stop'].size)
        counts['integer_expert_updates'] += updates
        counts['fraction_factor_checks'] += fractions
        counts['paired_query_steps'] += n * repeats
        if counts['pairs'] % 20 == 0:
            print('Audited', counts['pairs'], 'pairs', flush=True)
    payload = {key: np.stack([case[key] for case in compact]) for key in compact[0]}
    payload.update(case_ids=np.array([case['case_id'] for case in metadata['cases']]),
                   methods=np.array(METHODS), levels=np.array(LEVELS))
    np.savez_compressed(directory / 'decisions.npz', **payload)
    verification = dict(status='passed', **counts, complete_reference=metadata['complete_reference'],
                        checks=['all trace hashes and deterministic ledgers', 'both-target exclusion and history hashes',
                                'all raw evidence via independent scalar exact optimization',
                                'all historical pre-query states via separate ridge replay',
                                'all expert updates via Python big integers', 'all first stopping decisions',
                                'fixed-budget sample-winner diagnostics', 'full-budget exact conclusions'],
                        decisions_sha256=hashlib.sha256((directory / 'decisions.npz').read_bytes()).hexdigest())
    (directory / 'VERIFICATION.json').write_text(json.dumps(verification, indent=2) + '\n')
    print(json.dumps(verification, indent=2), flush=True)


if __name__ == '__main__':
    main()
