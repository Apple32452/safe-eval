"""Cost/variance feasibility diagnostic for partially observed reference stars.

This is a local variance calculation, not an anytime-valid stopping method.
The cross-fitted predictions use target labels for training without charging
their cost, so their reported efficiency is deliberately optimistic.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "stage17"))
from prepare_scores import load_prepared

Q = 0.75
FOLDS = 5
SEED = 20261022


def variance_terms(reference, candidate, predictions):
    """Exact variance V of a paired contrast and mean squared residual R."""
    a = np.asarray(reference, dtype=float)
    b = np.asarray(candidate, dtype=float)
    m = np.asarray(predictions, dtype=float)
    if a.shape != b.shape or a.shape != m.shape or a.ndim != 1 or not len(a):
        raise ValueError("Matching nonempty one-dimensional arrays are required")
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b)) and np.all(np.isfinite(m))):
        raise ValueError("All scores and predictions must be finite")
    if np.any((a < 0) | (a > 1) | (b < 0) | (b > 1) | (m < 0) | (m > 1)):
        raise ValueError("Scores and predictions must be in [0,1]")
    d = a - b
    return float(np.mean((d - d.mean()) ** 2)), float(np.mean((b - m) ** 2))


def local_cost_ratio(v, r, q, reference_share):
    """Variance x expected labels, relative to full paired scoring.

    reference_share=1/k amortizes one reference score over k active edges.
    It is only a local, fixed-active-set proxy, not a stopping-cost guarantee.
    """
    if v <= 0 or r < 0 or not 0 < q <= 1 or not 0 < reference_share <= 1:
        raise ValueError("Invalid variance, residual, propensity or cost share")
    return (q + reference_share) / (1 + reference_share) * (1 + (1 / q - 1) * r / v)


def threshold(q, reference_share):
    if not 0 < q <= 1 or not 0 < reference_share <= 1:
        raise ValueError("Invalid propensity or cost share")
    return q / (q + reference_share)


def fit_linear(reference, candidate, train, test):
    """Predict B from A using only the indicated training item labels."""
    x = np.column_stack((np.ones(len(train)), reference[train]))
    coefficients = np.linalg.lstsq(x, candidate[train], rcond=None)[0]
    return np.clip(coefficients[0] + coefficients[1] * reference[test], 0, 1)


def cross_fitted_linear(reference, candidate, heldout_folds):
    n = len(reference)
    prediction = np.empty(n, dtype=float)
    all_items = np.arange(n)
    for heldout in heldout_folds:
        train = np.setdiff1d(all_items, heldout, assume_unique=True)
        prediction[heldout] = fit_linear(reference, candidate, train, heldout)
    return prediction


def summarize(data):
    rows = []
    all_records = []
    for language_index, (language, (scores, systems, items)) in enumerate(sorted(data.items())):
        rng = np.random.default_rng(SEED + language_index)
        heldout = np.array_split(rng.permutation(scores.shape[1]), FOLDS)
        k = scores.shape[0] - 1
        records = []
        for reference in range(len(systems)):
            for candidate in range(len(systems)):
                if reference == candidate:
                    continue
                a, b = scores[reference], scores[candidate]
                predictions = cross_fitted_linear(a, b, heldout)
                v, r = variance_terms(a, b, predictions)
                if v == 0:
                    continue
                records.append((v, r))
        ratios = np.array([r / v for v, r in records])
        if not len(ratios):
            raise ValueError("No nonconstant pairwise contrasts: " + language)
        all_records.extend((float(v), float(r), k) for v, r in records)
        rows.append({
            "language": language,
            "systems": len(systems),
            "items": len(items),
            "ordered_pairs": len(records),
            "median_R_over_V": float(np.median(ratios)),
            "eligible_single_reference": int(np.sum(ratios < threshold(Q, 1))),
            "eligible_shared_reference": int(np.sum(ratios < threshold(Q, 1 / k))),
            "median_single_cost_ratio": float(np.median([
                local_cost_ratio(v, r, Q, 1) for v, r in records])),
            "median_shared_cost_ratio": float(np.median([
                local_cost_ratio(v, r, Q, 1 / k) for v, r in records])),
        })
    total = len(all_records)
    result = {
        "interpretation": "Exploratory local variance-times-label-cost proxy; no sequential stopping or train-label cost",
        "q": Q,
        "folds": FOLDS,
        "seed": SEED,
        "ordered_pairs": total,
        "single_threshold": threshold(Q, 1),
        "eligible_single": sum(x["eligible_single_reference"] for x in rows),
        "eligible_shared": sum(x["eligible_shared_reference"] for x in rows),
        "median_R_over_V": float(np.median([r / v for v, r, _ in all_records])),
        "median_single_cost_ratio": float(np.median([
            local_cost_ratio(v, r, Q, 1) for v, r, _ in all_records])),
        "median_shared_cost_ratio": float(np.median([
            local_cost_ratio(v, r, Q, 1 / k) for v, r, k in all_records])),
        "by_language": rows,
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="results/stage17_data")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    matrices, provenance = load_prepared(args.data)
    result = summarize(matrices)
    result["source_sha256"] = provenance["source_sha256"]
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "SUMMARY.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    with (output / "by_language.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(result["by_language"][0]),
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(result["by_language"])
    print(json.dumps({key: result[key] for key in (
        "ordered_pairs", "eligible_single", "eligible_shared",
        "median_R_over_V", "median_single_cost_ratio", "median_shared_cost_ratio")}, indent=2))


if __name__ == "__main__":
    main()
