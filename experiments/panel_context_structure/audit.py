"""Exact combinatorial audit of uniform-context raw panel reuse."""
from __future__ import annotations

import itertools
import json


def eligible_panels(systems, panel_size, edges):
    edges = {tuple(sorted(edge)) for edge in edges}
    if not 2 <= panel_size <= systems or not edges:
        raise ValueError("Require panels with requested edges")
    return tuple(panel for panel in itertools.combinations(range(systems), panel_size)
                 if any(set(edge).issubset(panel) for edge in edges))


def components(panels, edges):
    """Panels are neighbors if both reveal at least one same requested edge."""
    parent = list(range(len(panels)))

    def root(j):
        while parent[j] != j:
            parent[j] = parent[parent[j]]
            j = parent[j]
        return j

    for edge in edges:
        members = [j for j, panel in enumerate(panels)
                   if set(edge).issubset(panel)]
        for j in members[1:]:
            parent[root(j)] = root(members[0])
    groups = {}
    for j in range(len(panels)):
        groups.setdefault(root(j), []).append(j)
    return tuple(tuple(group) for group in groups.values())


def direct_compatibility(panels, edges, integer_weights):
    """Check Q(S)/p_e = 1/d_e with integer arithmetic for every edge."""
    if len(panels) != len(integer_weights) or any(w <= 0 for w in integer_weights):
        raise ValueError("Each eligible panel needs a positive weight")
    for edge in edges:
        members = [j for j, panel in enumerate(panels)
                   if set(edge).issubset(panel)]
        if not members:
            raise ValueError("A requested edge cannot be observed")
        total = sum(integer_weights[j] for j in members)
        if any(len(members) * integer_weights[j] != total for j in members):
            return False
    return True


def component_compatibility(panels, edges, integer_weights):
    if len(panels) != len(integer_weights) or any(w <= 0 for w in integer_weights):
        raise ValueError("Each eligible panel needs a positive weight")
    return all(len({integer_weights[j] for j in group}) == 1
               for group in components(panels, edges))


def audit():
    all_edges = tuple(itertools.combinations(range(4), 2))
    graphs = states = compatible = 0
    for mask in range(1, 1 << len(all_edges)):
        edges = tuple(edge for j, edge in enumerate(all_edges) if mask & (1 << j))
        panels = eligible_panels(4, 3, edges)
        graphs += 1
        for weights in itertools.product((1, 2, 3), repeat=len(panels)):
            actual = direct_compatibility(panels, edges, weights)
            proposed = component_compatibility(panels, edges, weights)
            if actual != proposed:
                raise AssertionError("The component characterization failed")
            states += 1
            compatible += actual

    full_edges = tuple(itertools.combinations(range(7), 2))
    complete_panels = eligible_panels(7, 5, full_edges)
    complete_components = components(complete_panels, full_edges)
    assert len(complete_panels) == 21 and len(complete_components) == 1
    sparse_edges = ((0, 1), (4, 5))
    sparse_panels = eligible_panels(6, 3, sparse_edges)
    sparse_components = components(sparse_panels, sparse_edges)
    assert sorted(map(len, sparse_components)) == [4, 4]
    sparse_weights = [0] * len(sparse_panels)
    for weight, group in enumerate(sparse_components, start=1):
        for j in group:
            sparse_weights[j] = weight
    assert direct_compatibility(sparse_panels, sparse_edges, sparse_weights)

    # A bounded context effect for one pair: its preference is 1 in the
    # oversampled panel and 0 (a tie) in its other three panels.
    six_edges = tuple(itertools.combinations(range(6), 2))
    five_panels = eligible_panels(6, 5, six_edges)
    heavy = five_panels.index((0, 1, 2, 3, 4))
    weights = [2 if j == heavy else 1 for j in range(len(five_panels))]
    e_members = [j for j, panel in enumerate(five_panels) if {0, 1} <= set(panel)]
    target = 1 / len(e_members)
    observed = weights[heavy] / sum(weights[j] for j in e_members)
    assert len(e_members) == 4 and target == .25 and observed == .4
    assert not direct_compatibility(five_panels, six_edges, weights)
    return dict(graphs=graphs, positive_weight_states=states,
                compatible_states=compatible,
                complete_panels=len(complete_panels),
                complete_components=len(complete_components),
                sparse_eligible_panels=len(sparse_panels),
                sparse_components=len(sparse_components),
                context_witness=dict(target=target, unweighted_adaptive=observed,
                                     bias=observed-target))


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
