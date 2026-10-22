"""Exact acquisition audit and frozen synthetic comparison for Stage 28."""
from __future__ import annotations

import argparse
import csv
import hashlib
from itertools import product
import json
from pathlib import Path

import numpy as np

from joint_queries import (ALPHA, EDGES, EPSILON, METHODS, Q_FIXED, SCENARIOS,
                           SEED, bounds_for_edge, corrected_edge, run_experiment)


def selection_law(qb, qc, coupled):
    if not coupled:
        return [((zb, zc), (qb if zb else 1 - qb) * (qc if zc else 1 - qc))
                for zb, zc in product((0, 1), repeat=2)]
    cutpoints = sorted(set((0.0, float(qb), float(qc), 1.0)))
    return [((int((lo + hi) / 2 < qb), int((lo + hi) / 2 < qc)), hi - lo)
            for lo, hi in zip(cutpoints, cutpoints[1:])]


def exact_audit():
    cases = 0
    def verify(a, b, c, m, q, coupled):
        qb, qc = q[:, int(a)]
        bounds = [bounds_for_edge(e, m, q) for e in range(len(EDGES))]
        expected = np.zeros(len(EDGES))
        for (zb, zc), probability in selection_law(qb, qc, coupled):
            if probability <= 0:
                continue
            z = np.array((zb, zc))
            labels = np.array((b if zb else 0., c if zc else 0.))
            for e in range(len(EDGES)):
                g = corrected_edge(e, a, labels, z, m, q)
                low, high = bounds[e]
                if not -low - 1e-12 <= g <= high + 1e-12:
                    raise AssertionError("Pre-draw range violation")
                expected[e] += probability * g
        if not np.allclose(expected, (a - b, a - c, b - c), atol=1e-12):
            raise AssertionError("Query correction lost the pairwise mean")

    for a, b, c in product((0., 1.), repeat=3):
        for mb, mc in product((0., .5, 1.), repeat=2):
            for qb, qc in product((EPSILON, Q_FIXED, 1.), repeat=2):
                # Tables for both possible reference outcomes are fixed before
                # seeing this draw; this checks arbitrary predictable entries.
                m = np.array(((mb, mb), (mc, mc)))
                q = np.array(((qb, qb), (qc, qc)))
                for coupled in (False, True):
                    verify(a, b, c, m, q, coupled)
                    cases += 1

    # Exercise genuinely reference-dependent predictions and propensities:
    # the bet's bounds must include both possible strata before observing A.
    m_options = ((0., 1.), (1., 0.), (.25, .75), (.75, .25))
    q_options = ((EPSILON, 1.), (1., EPSILON), (.5, Q_FIXED), (Q_FIXED, .5))
    for a, b, c in product((0., 1.), repeat=3):
        for mb, mc in product(m_options, repeat=2):
            for qb, qc in product(q_options, repeat=2):
                for coupled in (False, True):
                    verify(a, b, c, np.array((mb, mc)), np.array((qb, qc)), coupled)
                    cases += 1

    # Both query mechanisms are mean-correct for a null population with the
    # same mean on every system; any precommitted legal linear bet has E=1.
    types = ((1., 1., 0.), (0., 0., 1.))
    q = np.array(((.25, .75), (.75, .25)))
    m = np.array(((.75, .25), (.25, .75)))
    null_means = {}
    for coupled in (False, True):
        mean = np.zeros(len(EDGES))
        for a, b, c in types:
            for (zb, zc), probability in selection_law(q[0, int(a)], q[1, int(a)], coupled):
                z = np.array((zb, zc))
                labels = np.array((b if zb else 0., c if zc else 0.))
                for e in range(len(EDGES)):
                    mean[e] += probability * corrected_edge(e, a, labels, z, m, q) / len(types)
        if not np.allclose(mean, 0, atol=1e-12):
            raise AssertionError("Null factor has positive expected drift")
        null_means["coupled" if coupled else "independent"] = mean.tolist()

    # Conditional variance of the candidate-candidate correction at equal q.
    # With residuals of the same sign, one shared coin reduces variance;
    # opposite signs reverse the advantage. This is a mechanism, not a claim
    # that the full stopping cost must have the same ordering.
    q0 = Q_FIXED
    def variances(x, y):
        independent = (1 / q0 - 1) * (x * x + y * y)
        coupled = (1 / q0 - 1) * (x - y) ** 2
        return dict(independent=independent, coupled=coupled)
    positive = variances(.6, .4)
    opposed = variances(.6, -.4)
    if not positive["coupled"] < positive["independent"]:
        raise AssertionError("Expected positive-residual covariance effect absent")
    if not opposed["coupled"] > opposed["independent"]:
        raise AssertionError("Expected opposing-residual covariance effect absent")
    return dict(enumerated_settings=cases, null_mean_signals=null_means,
                same_sign_residual_variance=positive,
                opposite_sign_residual_variance=opposed)


def summarize(rows):
    result = []
    for scenario in SCENARIOS:
        group = [x for x in rows if x["scenario"] == scenario]
        for method in METHODS:
            selected = [x["methods"][method] for x in group]
            both = [(x["methods"]["paired_adaptive"], x["methods"][method])
                    for x in group if x["methods"]["paired_adaptive"]["complete"]
                    and x["methods"][method]["complete"]]
            result.append(dict(scenario=scenario, method=method, repeats=len(group),
                               population_signs=group[0]["signs"],
                               completed=sum(x["complete"] for x in selected),
                               wrong_runs=sum(x["wrong"] > 0 for x in selected),
                               mean_cost_stop_or_cap=float(np.mean([x["cost"] for x in selected])),
                               mean_rounds_stop_or_cap=float(np.mean([x["rounds"] for x in selected])),
                               jointly_completed_with_paired_adaptive=len(both),
                               mean_cost_on_jointly_completed=(float(np.mean([x[1]["cost"] for x in both]))
                                                               if both else None),
                               paired_adaptive_cost_on_jointly_completed=(float(np.mean([x[0]["cost"] for x in both]))
                                                                   if both else None)))
    return result


def run(output, repeats=100, rounds=1600):
    audit = exact_audit()
    rows = run_experiment(repeats, rounds)
    payload = dict(protocol=dict(seed=SEED, alpha=ALPHA, minimum_propensity=EPSILON,
                                 fixed_propensity=Q_FIXED, rounds=rounds, repeats=repeats,
                                 item_count=32, rater_count=6, system_count=3,
                                 estimand="All three mean score differences under iid uniform item and independent iid uniform rater draws",
                                 cost="One fresh blinded system-item-rater judgment, without caching"),
                   exact_audit=audit, summary=summarize(rows), replicates=rows)
    write_results(payload, output)
    print(json.dumps(dict(exact_audit=audit, summary=payload["summary"]), indent=2))
    return payload


def write_results(payload, output):
    """Release every method trajectory in a compact, audit-friendly CSV."""
    path = Path(output)
    path.mkdir(parents=True, exist_ok=False)
    columns = ("scenario", "repeat", "method", "cost", "rounds", "d01",
               "d02", "d12", "complete", "wrong", "unresolved")
    replicate_path = path / "REPLICATES.csv"
    with replicate_path.open("w", newline="") as stream:
        # Keep the saved digest identical after Git checkout on each OS.
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in payload["replicates"]:
            for method in METHODS:
                result = row["methods"][method]
                writer.writerow(dict(scenario=row["scenario"], repeat=row["repeat"],
                                     method=method, cost=result["cost"], rounds=result["rounds"],
                                     d01=result["decisions"][0], d02=result["decisions"][1],
                                     d12=result["decisions"][2], complete=int(result["complete"]),
                                     wrong=result["wrong"], unresolved=result["unresolved"]))
    manifest = {key: payload[key] for key in ("protocol", "exact_audit", "summary")}
    manifest["replicates_sha256"] = hashlib.sha256(replicate_path.read_bytes()).hexdigest()
    (path / "SUMMARY.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeats", type=int, default=100)
    parser.add_argument("--rounds", type=int, default=1600)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.output, args.repeats, args.rounds)
