"""Exhaustive boundary for joint deterministic finite-pool sign certificates.

The analytic endpoint calculation and brute-force completion enumeration are
independent implementations. No Stage 22 module or benchmark scores are used.
"""

from __future__ import annotations

import argparse
import itertools
import json


UNKNOWN = -1
EDGES = ((0, 1), (0, 2), (1, 2))


def sign(value: int) -> int:
    return (value > 0) - (value < 0)


def compatible(state: tuple[int, ...], matrix: tuple[int, ...]) -> bool:
    return all(observed == UNKNOWN or observed == truth
               for observed, truth in zip(state, matrix))


def full_signs(matrix: tuple[int, ...], systems: int, items: int):
    totals = tuple(sum(matrix[s * items:(s + 1) * items])
                   for s in range(systems))
    return tuple(sign(totals[a] - totals[b]) for a, b in EDGES)


def pair_signs_from_bounds(state: tuple[int, ...], items: int,
                           edge: tuple[int, int]) -> frozenset[int]:
    """Independent row intervals, with an exact integer difference range."""
    totals = []
    for system in edge:
        row = state[system * items:(system + 1) * items]
        lower = sum(value for value in row if value != UNKNOWN)
        upper = lower + row.count(UNKNOWN)
        totals.append((lower, upper))
    low = totals[0][0] - totals[1][1]
    high = totals[0][1] - totals[1][0]
    return frozenset(sign(delta) for delta in range(low, high + 1))


def audit(systems: int = 3, items: int = 2) -> dict[str, int | str]:
    if systems != 3 or not 1 <= items <= 3:
        raise ValueError("This exhaustive audit fixes three systems and 1–3 items")

    matrices = tuple(itertools.product((0, 1), repeat=systems * items))
    checked_pairs = 0
    compatible_state_matrix_checks = 0
    states_with_joint_restriction = 0
    states_with_certified_edge = 0
    any_joint_restriction_without_edge_certificate = False

    for state in itertools.product((UNKNOWN, 0, 1), repeat=systems * items):
        completions = tuple(matrix for matrix in matrices if compatible(state, matrix))
        if not completions:
            raise AssertionError("Every partial binary state has a completion")
        joint_sign_vectors = {full_signs(matrix, systems, items)
                              for matrix in completions}
        projected = tuple(
            frozenset(vector[index] for vector in joint_sign_vectors)
            for index in range(len(EDGES))
        )
        independent = tuple(pair_signs_from_bounds(state, items, edge)
                            for edge in EDGES)
        for empirical, analytic in zip(projected, independent):
            checked_pairs += 1
            if empirical != analytic:
                raise AssertionError((state, empirical, analytic))

        # A deterministic declaration is valid against every fixed completion,
        # hence under any outcome-adaptive acquisition order and stopping time.
        for matrix in completions:
            compatible_state_matrix_checks += 1
            truth = full_signs(matrix, systems, items)
            for index, possibilities in enumerate(projected):
                if len(possibilities) == 1 and truth[index] not in possibilities:
                    raise AssertionError("A certified sign was false")

        cartesian_size = 1
        for possibilities in projected:
            cartesian_size *= len(possibilities)
        restricted = len(joint_sign_vectors) < cartesian_size
        certified = any(len(possibilities) == 1 for possibilities in projected)
        states_with_joint_restriction += restricted
        states_with_certified_edge += certified
        any_joint_restriction_without_edge_certificate |= restricted and not certified

    if not any_joint_restriction_without_edge_certificate:
        raise AssertionError("Expected a genuine joint restriction at zero observations")
    return {
        "status": "passed",
        "systems": systems,
        "items": items,
        "full_matrices": len(matrices),
        "partial_states": 3 ** (systems * items),
        "pair_projection_checks": checked_pairs,
        "compatible_state_matrix_checks": compatible_state_matrix_checks,
        "states_with_joint_restriction": states_with_joint_restriction,
        "states_with_certified_edge": states_with_certified_edge,
        "joint_restriction_without_edge_certificate_exists":
            any_joint_restriction_without_edge_certificate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=int, choices=(1, 2, 3), default=2)
    args = parser.parse_args()
    print(json.dumps(audit(items=args.items), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
