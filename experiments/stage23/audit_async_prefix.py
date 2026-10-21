"""Independent label-accounting audit for asynchronous fixed-prefix schedules.

This audits a *fixed* per-edge stopping certificate on a common item order.
It does not audit a new statistical confidence sequence or an adaptive method.
"""
from __future__ import annotations

import itertools
import json


def _validate(vertex_count, edges, stopping_rounds):
    edges = tuple(tuple(edge) for edge in edges)
    stopping_rounds = tuple(stopping_rounds)
    if vertex_count < 2 or not edges or len(edges) != len(stopping_rounds):
        raise ValueError("A nonempty graph and one stopping round per edge are required")
    if len(set(edges)) != len(edges):
        raise ValueError("Duplicate edges")
    if any(not (0 <= u < v < vertex_count) for u, v in edges):
        raise ValueError("Edges must be canonical pairs")
    if any(not isinstance(n, int) or n < 1 for n in stopping_rounds):
        raise ValueError("Stopping rounds must be positive integers")
    return edges, stopping_rounds


def required_labels(vertex_count, edges, stopping_rounds):
    """Union of all endpoint prefixes needed by the fixed edge certificates."""
    edges, stopping_rounds = _validate(vertex_count, edges, stopping_rounds)
    return frozenset(
        (vertex, item_round)
        for (u, v), stop in zip(edges, stopping_rounds)
        for vertex in (u, v)
        for item_round in range(1, stop + 1)
    )


def pruned_labels(vertex_count, edges, stopping_rounds):
    """What the synchronous active-vertex rule purchases by completion."""
    edges, stopping_rounds = _validate(vertex_count, edges, stopping_rounds)
    acquired = set()
    for item_round in range(1, max(stopping_rounds) + 1):
        active = set()
        for (u, v), stop in zip(edges, stopping_rounds):
            if stop >= item_round:
                active.update((u, v))
        acquired.update((vertex, item_round) for vertex in active)
    return frozenset(acquired)


def asynchronous_labels(vertex_count, edges, stopping_rounds, schedule):
    """Interleave edge-prefix advances and charge cached labels only once."""
    edges, stopping_rounds = _validate(vertex_count, edges, stopping_rounds)
    progress = [0] * len(edges)
    acquired = set()
    for edge_index in schedule:
        if not isinstance(edge_index, int) or not 0 <= edge_index < len(edges):
            raise ValueError("Unknown edge")
        if progress[edge_index] == stopping_rounds[edge_index]:
            raise ValueError("An edge was advanced beyond its certificate")
        progress[edge_index] += 1
        u, v = edges[edge_index]
        acquired.add((u, progress[edge_index]))
        acquired.add((v, progress[edge_index]))
    if tuple(progress) != stopping_rounds:
        raise ValueError("The schedule left a requested edge unfinished")
    return frozenset(acquired)


def interleavings(counts):
    """Generate all distinct schedules with the prescribed edge counts."""
    remaining = list(counts)
    schedule = []

    def visit():
        if not any(remaining):
            yield tuple(schedule)
            return
        for edge_index, count in enumerate(remaining):
            if count:
                remaining[edge_index] -= 1
                schedule.append(edge_index)
                yield from visit()
                schedule.pop()
                remaining[edge_index] += 1

    yield from visit()


def exhaustive_audit(max_vertices=3, max_rounds=3):
    if not 2 <= max_vertices <= 3 or not 1 <= max_rounds <= 3:
        raise ValueError("The independent exhaustive audit is bounded at 3 vertices/rounds")
    graph_cases = assignment_cases = asynchronous_schedules = 0
    for vertex_count in range(2, max_vertices + 1):
        complete = tuple(itertools.combinations(range(vertex_count), 2))
        for mask in range(1, 1 << len(complete)):
            edges = tuple(e for i, e in enumerate(complete) if mask & (1 << i))
            graph_cases += 1
            for stops in itertools.product(range(1, max_rounds + 1), repeat=len(edges)):
                assignment_cases += 1
                expected = required_labels(vertex_count, edges, stops)
                if pruned_labels(vertex_count, edges, stops) != expected:
                    raise AssertionError("Synchronous rule missed or added a label")
                maxima = [max((n for e, n in zip(edges, stops) if v in e), default=0)
                          for v in range(vertex_count)]
                if len(expected) != sum(maxima):
                    raise AssertionError("Vertex-maximum cost identity failed")
                for schedule in interleavings(stops):
                    asynchronous_schedules += 1
                    if asynchronous_labels(vertex_count, edges, stops, schedule) != expected:
                        raise AssertionError("An asynchronous schedule changed the footprint")
    return dict(status="passed", max_vertices=max_vertices, max_rounds=max_rounds,
                graph_cases=graph_cases, stopping_assignments=assignment_cases,
                asynchronous_schedules=asynchronous_schedules)


if __name__ == "__main__":
    print(json.dumps(exhaustive_audit(), indent=2, sort_keys=True))
