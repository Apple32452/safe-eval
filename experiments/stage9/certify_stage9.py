"""Exact finite-state risk calculation for the implemented raw PPR intervals.

Each binary string with K successes has probability 1 / comb(N, K) under
uniform sampling without replacement. Integer dynamic programming counts the
strings which stay inside every pointwise acceptance interval. No simulation
or floating probability arithmetic enters the risk certificate.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "stage7"))
from binary_control import log_ppr


def pointwise_intervals(n, threshold=20):
    if n < 2 or n >= np.iinfo(np.int16).max or threshold <= 1:
        raise ValueError("2 <= N < 32767 and threshold > 1 required")
    out = np.full((n + 1, n + 1, 2), -1, dtype=np.int16)
    out[0, 0] = (0, n)
    k = np.arange(n + 1)
    boundary = math.log(threshold)
    for t in range(1, n + 1):
        mask = log_ppr(np.arange(t + 1), t, n) < boundary
        lo = np.min(np.where(mask, k, n + 1), axis=1)
        hi = np.max(np.where(mask, k, -1), axis=1)
        # Contiguity proves running-mask and running-interval implementations
        # coincide, and makes the table a complete record of the actual gate.
        reconstructed = (k[None, :] >= lo[:, None]) & (k[None, :] <= hi[:, None])
        if not np.array_equal(mask, reconstructed):
            raise ValueError("A raw acceptance set is disconnected")
        out[t, :t + 1, 0] = lo
        out[t, :t + 1, 1] = hi
    return out


def state_sha(table):
    return hashlib.sha256(np.asarray(table, dtype="<i2").tobytes()).hexdigest()


def surviving_counts(table):
    n = len(table) - 1
    lo = table[:, :, 0].tolist()
    hi = table[:, :, 1].tolist()
    # Use symmetry only after checking every reachable mirrored boundary.
    symmetric = all(lo[t][s] == n - hi[t][t-s] and hi[t][s] == n - lo[t][t-s]
                    for t in range(n + 1) for s in range(t + 1))
    survivors = [None] * (n + 1)
    for k in range(n // 2 + 1 if symmetric else n + 1):
        previous = [1] + [0] * k
        for t in range(1, n + 1):
            current = [0] * (k + 1)
            lower_s = max(0, t - (n - k))
            upper_s = min(t, k)
            lowrow, highrow = lo[t], hi[t]
            for s in range(lower_s, upper_s + 1):
                if lowrow[s] <= k <= highrow[s]:
                    current[s] = previous[s] + (previous[s - 1] if s else 0)
            previous = current
        survivors[k] = previous[k]
        if symmetric:
            survivors[n-k] = previous[k]
    return survivors, symmetric


def risk_record(n, threshold, table=None):
    start = time.perf_counter()
    table = pointwise_intervals(n, threshold) if table is None else table
    survivors, symmetry = surviving_counts(table)
    totals = [math.comb(n, k) for k in range(n + 1)]
    risks = [Fraction(total - live, total) for total, live in zip(totals, survivors)]
    worst = max(risks)
    record = dict(n=n, threshold=threshold, boundary_log_hex=math.log(threshold).hex(),
                  state_sha256=state_sha(table), symmetry_verified=symmetry,
                  worst_k=[k for k, r in enumerate(risks) if r == worst],
                  risk_numerator=str(worst.numerator), risk_denominator=str(worst.denominator),
                  risk_decimal=float(worst),
                  surviving_strings=[str(s) for s in survivors],
                  runtime_seconds=time.perf_counter()-start)
    return record, table


def exact_risk(record):
    return Fraction(int(record["risk_numerator"]), int(record["risk_denominator"]))


def certify(n, output, target=Fraction(1, 20)):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    evaluations = {}
    def evaluate(h):
        if h not in evaluations:
            record, table = risk_record(n, h)
            evaluations[h] = record, table
            print(f"N={n} threshold={h} exact worst risk={record['risk_decimal']:.9f} "
                  f"K={record['worst_k']} seconds={record['runtime_seconds']:.1f}", flush=True)
        return evaluations[h]
    raw, raw_table = evaluate(20)
    # A fixed integer search, independent of target data and prediction quality.
    low, high = 2, 20
    if exact_risk(raw) > target:
        raise ValueError("Implemented ordinary raw95 fails the desired risk limit")
    while low < high:
        mid = (low + high) // 2
        if exact_risk(evaluate(mid)[0]) <= target:
            high = mid
        else:
            low = mid + 1
    calibrated, calibrated_table = evaluate(low)
    if low > 2:
        assert exact_risk(evaluate(low - 1)[0]) > target
    raw_risk = exact_risk(raw)
    # Allocate only the downward-rounded certified spare risk allowance.
    spare = target - raw_risk
    scale = 1_000_000
    budget = Fraction((spare.numerator * scale) // spare.denominator, scale)
    result = dict(n=n, target_error=str(target), raw=raw, calibrated=calibrated,
                  prediction_error_numerator=budget.numerator,
                  prediction_error_denominator=budget.denominator,
                  prediction_error_decimal=float(budget),
                  calibration_grid="integers 2 through 20; smallest certified threshold",
                  evaluated_thresholds={str(h): {"risk_numerator":r["risk_numerator"],
                     "risk_denominator":r["risk_denominator"], "risk_decimal":r["risk_decimal"],
                     "worst_k":r["worst_k"]} for h,(r,_) in sorted(evaluations.items())},
                  python=platform.python_version(), numpy=np.__version__,
                  platform=platform.platform(),
                  probability_model="uniform without replacement; fixed binary pool",
                  certificate_scope="actual pointwise float gate on this runtime; exact integer path counts")
    np.savez_compressed(output / f"states_{n}.npz", raw=raw_table, calibrated=calibrated_table)
    (output / f"certificate_{n}.json").write_text(json.dumps(result, indent=2))
    return result


def load_certificate(directory, n, verify_runtime=True):
    directory = Path(directory)
    record = json.loads((directory / f"certificate_{n}.json").read_text())
    with np.load(directory / f"states_{n}.npz") as f:
        raw, calibrated = f["raw"], f["calibrated"]
    for name, table in (("raw", raw), ("calibrated", calibrated)):
        if state_sha(table) != record[name]["state_sha256"]:
            raise ValueError("Certificate state table checksum mismatch")
        if verify_runtime and not np.array_equal(table, pointwise_intervals(n, record[name]["threshold"])):
            raise ValueError("Raw gates differ on this runtime; regenerate certificates")
    risk = exact_risk(record["raw"])
    alpha = Fraction(record["prediction_error_numerator"], record["prediction_error_denominator"])
    if alpha < 0 or risk + alpha > Fraction(1,20) or exact_risk(record["calibrated"]) > Fraction(1,20):
        raise ValueError("Invalid error allocation")
    return record, raw, calibrated


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", nargs="+", type=int, default=[154, 589, 820])
    p.add_argument("--output", required=True)
    args = p.parse_args()
    out = Path(args.output)
    if out.exists() and list(out.glob("certificate_*.json")):
        p.error("Use a new certificate output directory")
    for n in args.sizes:
        result = certify(n, out)
        print(f"N={n}: certified prediction error allowance="
              f"{result['prediction_error_decimal']:.6f}; "
              f"calibrated raw threshold={result['calibrated']['threshold']}", flush=True)


if __name__ == "__main__":
    main()
