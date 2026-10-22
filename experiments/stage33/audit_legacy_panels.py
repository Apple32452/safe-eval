"""Descriptive crossover audit for WMT-style raw five-system ranking CSVs."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


REQUIRED = {"srclang", "trglang", "srcIndex", "judgeId"}
REQUIRED |= {f"system{k}{suffix}" for k in range(1, 6)
             for suffix in ("Id", "rank")}


def interval(cells: list[tuple[tuple[str, str, str], float]],
             seed: int = 3301, draws: int = 2000) -> dict:
    """Item-cluster bootstrap; cells sharing an input resample together."""
    if not cells:
        return {"pair_items": 0, "source_items": 0, "mean": None,
                "cluster_bootstrap_95": None}
    if draws < 1:
        raise ValueError("draws must be positive")
    blocks = defaultdict(list)
    for item, delta in cells:
        blocks[item].append(delta)
    arrays = [np.asarray(x, dtype=float) for x in blocks.values()]
    sums = np.asarray([float(x.sum()) for x in arrays])
    counts = np.asarray([len(x) for x in arrays])
    rng = np.random.default_rng(seed)
    ids = rng.integers(len(sums), size=(draws, len(sums)))
    boot = sums[ids].sum(axis=1) / counts[ids].sum(axis=1)
    return {"pair_items": len(cells), "source_items": len(blocks),
            "mean": float(sums.sum() / counts.sum()),
            "cluster_bootstrap_95": [float(x) for x in np.quantile(
                boot, [0.025, 0.975])]}


def audit(path: Path, draws: int = 2000) -> dict:
    groups = defaultdict(list)
    rows = valid = 0
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not REQUIRED <= set(reader.fieldnames or ()):
            raise ValueError("expected raw five-system WMT ranking columns")
        for row in reader:
            rows += 1
            systems = [row[f"system{k}Id"] for k in range(1, 6)]
            try:
                ranks = [int(row[f"system{k}rank"]) for k in range(1, 6)]
            except (ValueError, TypeError):
                continue
            if (len(set(systems)) != 5 or any(
                    not s or s == "blank" for s in systems)
                    or any(rank not in (1, 2, 3, 4, 5) for rank in ranks)):
                continue
            valid += 1
            item = (row["srclang"], row["trglang"], row["srcIndex"])
            for i in range(5):
                for j in range(i + 1, 5):
                    if "_ref" in (systems[i], systems[j]):
                        continue
                    a, b = sorted((systems[i], systems[j]))
                    ra, rb = ranks[systems.index(a)], ranks[systems.index(b)]
                    sign = (rb > ra) - (rb < ra)  # +1 means A beats B.
                    companions = tuple(sorted(set(systems) - {a, b}))
                    groups[(item, a, b)].append((companions, row["judgeId"],
                                                 "_ref" in systems, sign))

    cross = cross_judges = cross_discordant = 0
    ref_cells, disjoint_cells = [], []
    for (item, _a, _b), obs in groups.items():
        if len({o[0] for o in obs}) >= 2:
            cross += 1
            if len({o[1] for o in obs}) >= 2:
                cross_judges += 1
            if any(x[0] != y[0] and x[3] * y[3] == -1
                   for k, x in enumerate(obs) for y in obs[k + 1:]):
                cross_discordant += 1
        ref = [o for o in obs if o[2]]
        no_ref = [o for o in obs if not o[2]]
        if not ref or not no_ref:
            continue
        diff = (sum(o[3] for o in ref) / len(ref)
                - sum(o[3] for o in no_ref) / len(no_ref))
        ref_cells.append((item, diff))
        if {o[1] for o in ref}.isdisjoint(o[1] for o in no_ref):
            disjoint_cells.append((item, diff))
    return {
        "rankings": rows, "complete_five_way": valid,
        "pair_item_groups": len(groups),
        "different_companion_panel_pair_items": cross,
        "different_panel_with_multiple_raters": cross_judges,
        "opposite_nontied_signs_across_panels": cross_discordant,
        "reference_presence_within_pair_item": interval(ref_cells, draws=draws),
        "reference_presence_disjoint_raters": interval(disjoint_cells, draws=draws),
        "analysis": "descriptive retrospective association; not a causal panel effect",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--draws", type=int, default=2000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.input, draws=args.draws)
    data = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data)
    print(data)
