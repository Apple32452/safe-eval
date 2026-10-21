"""Descriptive sign-versus-significance diagnostic on existing WMT25 matrices.

The normal approximation models common items as an independent sample. It is
not a finite-population confidence sequence, a WMT official test, or a new
anytime-valid method. No held-out WMT24 data are read.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stage17"))
from prepare_scores import load_prepared


def paired_normal_pvalues(scores):
    """Return all-pair two-sided p-values from paired item differences."""
    scores = np.asarray(scores, dtype=float)
    if (scores.ndim != 2 or scores.shape[0] < 3 or scores.shape[1] < 30
            or not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1))):
        raise ValueError("Expected at least 3 systems and 30 bounded common items")
    systems, items = scores.shape
    pairs = np.asarray(list(combinations(range(systems), 2)), dtype=int)
    differences = scores[pairs[:, 0]] - scores[pairs[:, 1]]
    means = differences.mean(axis=1)
    standard_errors = differences.std(axis=1, ddof=1) / math.sqrt(items)
    pvalues = np.ones(len(pairs), dtype=float)
    nonzero = standard_errors > 0
    z = np.abs(means[nonzero] / standard_errors[nonzero])
    pvalues[nonzero] = np.fromiter(
        (math.erfc(float(value) / math.sqrt(2)) for value in z), float, len(z)
    )
    pvalues[~nonzero & (means != 0)] = 0.0
    return pairs, means, pvalues


def diagnose(matrices):
    rows = []
    for language, (scores, _names, items) in sorted(matrices.items()):
        systems = scores.shape[0]
        pairs, differences, pvalues = paired_normal_pvalues(scores)
        # Each of the S reference stars contains S-1 comparisons. Every
        # unordered pair occurs in two stars with the same Bonferroni cutoff.
        significant = pvalues <= 0.05 / (systems - 1)
        rows.append(dict(
            language=language, systems=systems, items=len(items),
            unordered_pairs=len(pairs), nonzero_full_pool_signs=int(np.count_nonzero(differences)),
            bonferroni_significant_pairs=int(significant.sum()),
            unresolved_pairs=int((~significant).sum()),
            illustrative_significant_fraction=float(significant.mean()),
        ))
    total_pairs = sum(row["unordered_pairs"] for row in rows)
    significant = sum(row["bonferroni_significant_pairs"] for row in rows)
    return rows, dict(
        languages=len(rows), unordered_pairs=total_pairs,
        nonzero_full_pool_signs=sum(row["nonzero_full_pool_signs"] for row in rows),
        bonferroni_significant_pairs=significant,
        unresolved_pairs=total_pairs - significant,
        pooled_significant_fraction=significant / total_pairs,
        mean_language_significant_fraction=float(np.mean([
            row["illustrative_significant_fraction"] for row in rows
        ])),
        diagnostic="Paired item normal approximation, two-sided, 0.05/(S-1) per reference star",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="results/stage17_data")
    parser.add_argument("--output", default="experiments/stage24/results_reference")
    args = parser.parse_args()
    matrices, provenance = load_prepared(args.data)
    rows, summary = diagnose(matrices)
    summary["source_sha256"] = provenance["source_sha256"]
    summary["matrix_sha256_by_language"] = {
        row["language"]: row["matrix_sha256"]
        for row in provenance["reports"] if row["included"]
    }
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    with (output / "by_language.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({key: value for key, value in summary.items()
                      if key not in ("matrix_sha256_by_language", "source_sha256")}, indent=2))


if __name__ == "__main__":
    main()
