"""Independent exhaustive audit of the Stage 23 synchronous-class theorem."""
from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class CaseResult:
    common_completion: int
    pruned_completion: int
    edge_checks: int


def _validate_graph(system_count, edges):
    if system_count < 2:
        raise ValueError("At least two systems are required")
    canonical = tuple(tuple(map(int, edge)) for edge in edges)
    if not canonical:
        raise ValueError("A nonempty requested graph is required")
    if len(set(canonical)) != len(canonical):
        raise ValueError("Requested edges must be unique")
    for a, b in canonical:
        if not 0 <= a < b < system_count:
            raise ValueError("Edges must be canonical system pairs")
    return canonical


def incident_vertices(edges):
    return frozenset(vertex for edge in edges for vertex in edge)


def check_itemwise_lower_bound(system_count, edges):
    """Enumerate every queried vertex set for one unresolved graph."""
    edges = _validate_graph(system_count, edges)
    required = incident_vertices(edges)
    feasible = []
    checked = 0
    for mask in range(1 << system_count):
        queried = frozenset(
            vertex for vertex in range(system_count) if mask & (1 << vertex)
        )
        checked += 1
        advances_all = all(a in queried and b in queried for a, b in edges)
        if advances_all:
            if not required.issubset(queried):
                raise AssertionError("A feasible query set omitted an incident vertex")
            feasible.append(queried)
    minimum = min(map(len, feasible))
    minimizers = [queried for queried in feasible if len(queried) == minimum]
    if minimum != len(required) or minimizers != [required]:
        raise AssertionError("Incident vertices were not the unique minimum query set")
    return checked


def check_resolution_schedule(system_count, edges, order, resolution_round):
    """Check completion and per-edge costs for an abstract outcome path.

    ``resolution_round[e]`` is the common-prefix round at which edge ``e``
    first obtains its irreversible declaration. It abstracts away the score
    values and confidence process, which are irrelevant to the label-accounting
    theorem.
    """
    edges = _validate_graph(system_count, edges)
    order = tuple(map(int, order))
    rounds = tuple(map(int, resolution_round))
    if sorted(order) != list(range(system_count)):
        raise ValueError("The within-item order must be a system permutation")
    if len(rounds) != len(edges) or any(round_index < 1 for round_index in rounds):
        raise ValueError("Every edge needs a positive resolution round")

    global_position = {vertex: position + 1 for position, vertex in enumerate(order)}
    final_round = max(rounds)
    common_before = 0
    pruned_before = 0
    common_edge_cost = [None] * len(edges)
    pruned_edge_cost = [None] * len(edges)

    for round_index in range(1, final_round + 1):
        active_indices = [
            edge_index for edge_index, resolved_at in enumerate(rounds)
            if resolved_at >= round_index
        ]
        active_edges = tuple(edges[edge_index] for edge_index in active_indices)
        active_vertices = incident_vertices(active_edges)
        restricted_order = tuple(
            vertex for vertex in order if vertex in active_vertices
        )
        restricted_position = {
            vertex: position + 1
            for position, vertex in enumerate(restricted_order)
        }

        for edge_index in active_indices:
            if rounds[edge_index] != round_index:
                continue
            a, b = edges[edge_index]
            common_edge_cost[edge_index] = common_before + max(
                global_position[a], global_position[b]
            )
            pruned_edge_cost[edge_index] = pruned_before + max(
                restricted_position[a], restricted_position[b]
            )

        if round_index < final_round:
            common_before += system_count
            pruned_before += len(active_vertices)
        else:
            common_completion = common_before + max(
                global_position[vertex] for vertex in active_vertices
            )
            pruned_completion = pruned_before + len(active_vertices)

    if any(value is None for value in common_edge_cost + pruned_edge_cost):
        raise AssertionError("Every edge must receive a resolution cost")
    if any(pruned > common for pruned, common in zip(
        pruned_edge_cost, common_edge_cost
    )):
        raise AssertionError("Per-edge pathwise label-cost dominance failed")
    if pruned_completion > common_completion:
        raise AssertionError("Pruned completion exceeded common completion")
    return CaseResult(
        common_completion=common_completion,
        pruned_completion=pruned_completion,
        edge_checks=len(edges),
    )


def exhaustive_audit(max_systems=4, max_rounds=3):
    if max_systems < 2 or max_rounds < 1:
        raise ValueError("Invalid exhaustive-audit limits")
    graph_cases = 0
    queried_subsets = 0
    schedule_cases = 0
    edge_checks = 0
    strict_completion_gains = 0

    for system_count in range(2, max_systems + 1):
        complete_edges = tuple(itertools.combinations(range(system_count), 2))
        for graph_mask in range(1, 1 << len(complete_edges)):
            edges = tuple(
                edge for edge_index, edge in enumerate(complete_edges)
                if graph_mask & (1 << edge_index)
            )
            graph_cases += 1
            queried_subsets += check_itemwise_lower_bound(system_count, edges)
            for order in itertools.permutations(range(system_count)):
                for rounds in itertools.product(
                    range(1, max_rounds + 1), repeat=len(edges)
                ):
                    result = check_resolution_schedule(
                        system_count, edges, order, rounds
                    )
                    schedule_cases += 1
                    edge_checks += result.edge_checks
                    strict_completion_gains += (
                        result.pruned_completion < result.common_completion
                    )

    return {
        "status": "passed",
        "max_systems": max_systems,
        "max_rounds": max_rounds,
        "graph_cases": graph_cases,
        "queried_vertex_subsets": queried_subsets,
        "resolution_schedule_cases": schedule_cases,
        "per_edge_dominance_checks": edge_checks,
        "strict_completion_gains": strict_completion_gains,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-systems", type=int, default=4)
    parser.add_argument("--max-rounds", type=int, default=3)
    parser.add_argument("--output")
    arguments = parser.parse_args()
    report = exhaustive_audit(arguments.max_systems, arguments.max_rounds)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        with open(arguments.output, "x") as stream:
            stream.write(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()

