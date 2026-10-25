"""Independent integer-null and exhaustive tiny-tree audits."""
from __future__ import annotations

import argparse
import copy
import json
from itertools import product
from pathlib import Path

import numpy as np
from scipy.spatial import ConvexHull

from joint_order import (DIRECTED, IMPLIED, JOINT_NULLS, ORDERS, PAIRS,
                         PAIR_NULLS, Evidence, event_rows, state_update)


def integer_totals(s, m, relations):
    return np.asarray([t for t in product(*(range(int(a), int(a + b + 1))
                                           for a, b in zip(s, m)))
                       if all(t[a] <= t[b] for a, b in relations)],
                      dtype=int).reshape(-1, 3)


def integer_hull(points):
    if len(points) <= 1:
        return points
    shifted = points - points[0]
    _, singular, directions = np.linalg.svd(shifted, full_matrices=False)
    rank = int(np.count_nonzero(singular > 1e-9))
    coordinate = shifted @ directions[:rank].T
    if rank == 1:
        ids = [int(np.argmin(coordinate[:, 0])), int(np.argmax(coordinate[:, 0]))]
    else:
        ids = ConvexHull(coordinate).vertices
    return np.unique(points[ids], axis=0)


def audit_states(n=2):
    choices = [(s, m) for m in range(n + 1) for s in range(n - m + 1)]
    checked_states = checked_nulls = checked_expectations = 0
    largest = 0.
    prior = (.2, .5, .8)
    relations = [tuple(DIRECTED[i] for i in ids) for ids in IMPLIED]
    relations += [(pair,) for pair in DIRECTED]
    for state in product(choices, repeat=3):
        s, m = np.array(state).T
        checked_states += 1
        update = state_update(tuple(s), tuple(m), prior, n) if m.sum() else None
        for k, (null, relation) in enumerate(zip(JOINT_NULLS + PAIR_NULLS, relations)):
            enumerated = integer_totals(s, m, relation)
            vertices = null.vertices(s, m)
            if not np.array_equal(vertices, integer_hull(enumerated)):
                raise AssertionError("Vertex set differs from independent integer hull")
            checked_nulls += 1
            if not len(enumerated) or update is None:
                continue
            q = update["q"]
            factor = update["joint"][k] if k < 13 else update["pair"][k - 13]
            # Explicit event probabilities, independent of event_rows().
            for total in enumerated:
                expectation = 0.
                for v in range(3):
                    if m[v]:
                        successes_left = total[v] - s[v]
                        expectation += q[v] * (
                            (m[v] - successes_left) * factor[2*v] +
                            successes_left * factor[2*v+1]) / m[v]
                largest = max(largest, float(expectation))
                if expectation > 1 + 1e-10 or min(factor) < 0:
                    raise AssertionError("Invalid conditional factor")
                checked_expectations += 1
    return {"states": checked_states, "null_polytopes": checked_nulls,
            "conditional_expectations": checked_expectations,
            "largest_conditional_expectation": largest}


def audit_trees(n=2, alpha=.05):
    prior = (.2, .5, .8)
    rows, total_leaves = [], 0
    for total_tuple in product(range(n + 1), repeat=3):
        total = np.asarray(total_tuple)
        truth = np.array([np.sign(total[a] - total[b]) for a, b in PAIRS], int)
        error_mass = np.zeros(3)
        leaf_mass = 0.
        leaves = 0

        def visit(s, m, evidence, probability, wrong_before):
            nonlocal leaf_mass, leaves
            wrong = wrong_before | np.any((evidence.decisions != 2) &
                                           (evidence.decisions != truth), axis=1)
            if not m.sum():
                if np.any(evidence.decisions == 2):
                    raise AssertionError("Full evaluation did not resolve all pairs")
                error_mass[:] += probability * wrong
                leaf_mass += probability
                leaves += 1
                return
            update = state_update(tuple(s), tuple(m), prior, n)
            for v in range(3):
                if not m[v]:
                    continue
                for value in (0, 1):
                    left = total[v] - s[v] if value else m[v] - total[v] + s[v]
                    if left == 0:
                        continue
                    p = update["q"][v] * left / m[v]
                    next_s, next_m = s.copy(), m.copy()
                    next_s[v] += value; next_m[v] -= 1
                    updated = copy.deepcopy(evidence)
                    updated.advance(update, 2*v + value, next_s, next_m)
                    visit(next_s, next_m, updated, probability * p, wrong)

        visit(np.zeros(3, int), np.full(3, n), Evidence(alpha), 1., np.zeros(3, bool))
        if abs(leaf_mass - 1) > 1e-9 or np.any(error_mass > alpha + 1e-9):
            raise AssertionError("Exhaustive fixed-matrix familywise error failed")
        total_leaves += leaves
        rows.append({"totals": list(total_tuple), "error_probability": error_mass.tolist(),
                     "path_probability_sum": float(leaf_mass), "leaves": leaves})
    return {"total_triples": len(rows), "covered_binary_matrices": 2 ** (3*n),
            "decision_tree_leaves": total_leaves,
            "max_familywise_error": np.max([r["error_probability"] for r in rows], axis=0).tolist(),
            "cases": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {"status": "passed", "integer_state_audit": audit_states(),
              "exhaustive_tree_audit": audit_trees()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: (v if k != "exhaustive_tree_audit" else
                         {a: b for a, b in v.items() if a != "cases"})
                      for k, v in report.items()}, indent=2))
