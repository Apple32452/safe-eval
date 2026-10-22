"""A small, valid but elementary partial-label baseline for the method gate.

It keeps the Stage 17 paired evidence paths exactly unchanged. A separate
deterministic bound uses every already acquired system-item score. Dynamic
within-item pruning is compared both with and without this bound so that its
effect is not misattributed to statistical innovation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stage17"))
from run_stage17 import close_free


def exact_bounds(scores, seen, pairs):
    """Sharp contrast sum bounds for unknown scores in [0,1]."""
    observed = np.zeros_like(scores)
    observed[seen] = scores[seen]
    total = observed.sum(axis=1)
    missing = (~seen).sum(axis=1)
    a, b = pairs.T
    lower = total[a] - total[b] - missing[b]
    upper = total[a] - total[b] + missing[a]
    return lower, upper


def run_dynamic(scores, pairs, permutation, events, priority, *, partial_bounds):
    scores = np.asarray(scores, dtype=float)
    pairs = np.asarray(pairs, dtype=np.int16)
    permutation = np.asarray(permutation, dtype=np.int32)
    events = np.asarray(events, dtype=np.int8)
    priority = np.asarray(priority)
    systems, items = scores.shape
    assert np.all((0 <= scores) & (scores <= 1))
    assert np.all(permutation == permutation[0])
    seen = np.zeros_like(scores, dtype=bool)
    cursor = np.zeros(len(pairs), dtype=np.int32)
    decision = np.full(len(pairs), 2, dtype=np.int8)
    acquired = []
    deterministic = 0
    bound_decisions = []
    for item in permutation[0]:
        if not np.any(decision == 2):
            break
        active = np.unique(pairs[decision == 2].ravel())
        ordered = sorted(active, key=lambda system: priority[system, item])
        for system in ordered:
            if not np.any(decision == 2):
                break
            if not np.any((decision == 2) & np.any(pairs == system, axis=1)):
                continue
            assert not seen[system, item]
            seen[system, item] = True
            acquired.append((int(system), int(item)))
            close_free(seen, cursor, decision, pairs, permutation, events)
            if partial_bounds:
                lower, upper = exact_bounds(scores, seen, pairs)
                for edge in np.flatnonzero(decision == 2):
                    if lower[edge] > 0:
                        decision[edge] = 1
                        deterministic += 1
                        bound_decisions.append((edge, 1))
                    elif upper[edge] < 0:
                        decision[edge] = -1
                        deterministic += 1
                        bound_decisions.append((edge, -1))
                    elif lower[edge] == upper[edge] == 0:
                        decision[edge] = 0
                        deterministic += 1
                        bound_decisions.append((edge, 0))
        if np.any((decision == 2) & (cursor <= np.where(permutation[0] == item)[0][0])):
            raise AssertionError("An active edge missed the current paired item")
    truth = np.sign(scores[pairs[:, 0]].sum(axis=1) -
                    scores[pairs[:, 1]].sum(axis=1)).astype(np.int8)
    assert all(truth[edge] == sign for edge, sign in bound_decisions)
    assert not np.any(decision == 2)
    assert len(acquired) == len(set(acquired)) == int(seen.sum())
    return dict(cost=len(acquired), deterministic=deterministic, decision=decision,
                wrong=int(np.count_nonzero(decision != truth)))


def run_static(scores, pairs, permutation, events, priority):
    """Replicate the Stage 22 acquisition rule without asserting zero errors."""
    scores = np.asarray(scores, dtype=float)
    pairs = np.asarray(pairs, dtype=np.int16)
    seen = np.zeros_like(scores, dtype=bool)
    cursor = np.zeros(len(pairs), dtype=np.int32)
    decision = np.full(len(pairs), 2, dtype=np.int8)
    acquired = []
    item_position = 0
    committed = []
    position = 0
    close_free(seen, cursor, decision, pairs, permutation, events)
    while np.any(decision == 2):
        if position == len(committed):
            item = int(permutation[0, item_position])
            item_position += 1
            active = np.unique(pairs[decision == 2].ravel())
            committed = [(int(system), item) for system in
                         sorted(active, key=lambda system: priority[system, item])]
            position = 0
        label = committed[position]
        position += 1
        assert not seen[label]
        seen[label] = True
        acquired.append(label)
        close_free(seen, cursor, decision, pairs, permutation, events)
    truth = np.sign(scores[pairs[:, 0]].sum(axis=1) -
                    scores[pairs[:, 1]].sum(axis=1)).astype(np.int8)
    assert len(acquired) == len(set(acquired)) == int(seen.sum())
    return dict(cost=len(acquired), decision=decision,
                wrong=int(np.count_nonzero(decision != truth)))
