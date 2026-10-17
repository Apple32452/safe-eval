"""Outcome-independent fine calibration and exact repaired-path counting."""
from __future__ import annotations
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "stage9"))
from certify_stage9 import (pointwise_intervals, risk_record, exact_risk,
                           state_sha, load_certificate as load_stage9)

ROUNDS = 12
MAX_STATES = 100_000
MAX_TRANSITIONS = 5_000_000
TARGET = Fraction(1, 20)


def count_record(n, threshold, table, survivors, **extra):
    risks = [Fraction(math.comb(n, k) - a, math.comb(n, k))
             for k, a in enumerate(survivors)]
    worst = max(risks)
    return dict(n=n, threshold=float(threshold), state_sha256=state_sha(table),
                risk_numerator=str(worst.numerator), risk_denominator=str(worst.denominator),
                risk_decimal=float(worst), worst_k=[k for k, r in enumerate(risks) if r == worst],
                surviving_strings=[str(a) for a in survivors], **extra)


def repaired_counts(calibrated, raw, max_states=MAX_STATES,
                    max_transitions=MAX_TRANSITIONS):
    """Count all full binary strings by their surviving coverage interval.

    Before fallback the survival interval is the calibrated running set.
    Afterwards it retains the last calibrated restriction and all subsequent
    raw restrictions. Past raw restrictions are redundant because the earlier
    calibrated intersection was contained in all of them. Empty survival
    states contribute no passing full strings and can be dropped.
    """
    n = len(raw) - 1
    if calibrated.shape != raw.shape:
        raise ValueError("Mismatched gate tables")
    for t in range(n + 1):
        if np.any(calibrated[t, :t+1, 0] < raw[t, :t+1, 0]) or np.any(
                calibrated[t, :t+1, 1] > raw[t, :t+1, 1]):
            raise ValueError("Nested calibrated/raw gates are required")
    cal = calibrated.tolist(); parent = raw.tolist()
    # Integer keys avoid retaining millions of Python tuple components.
    base = n + 1
    def encode(s, lo, hi, phase):
        return ((s * base + lo) * base + hi) * 2 + phase
    states = {encode(0, 0, n, 0): 1}
    transitions = 0; peak = 1
    for t in range(1, n + 1):
        new = {}
        for key, mass in states.items():
            rest, phase = divmod(key, 2)
            rest, hi = divmod(rest, base)
            s, lo = divmod(rest, base)
            for outcome in (0, 1):
                transitions += 1
                if transitions > max_transitions:
                    return dict(status="capped", reason="transition_limit", completed_layers=t-1,
                                transitions=transitions-1, peak_states=max(peak, len(new)))
                ns = s + outcome
                nl, nu = max(lo, cal[t][ns][0]), min(hi, cal[t][ns][1])
                next_phase = phase
                if phase or nl > nu:
                    next_phase = 1
                    nl, nu = max(lo, parent[t][ns][0]), min(hi, parent[t][ns][1])
                if nl > nu:
                    continue
                target = encode(ns, nl, nu, next_phase)
                new[target] = new.get(target, 0) + mass
                if len(new) > max_states:
                    return dict(status="capped", reason="state_limit", completed_layers=t-1,
                                transitions=transitions, peak_states=len(new))
        states = new
        peak = max(peak, len(states))
    survivors = [0] * (n + 1)
    for key, mass in states.items():
        rest, phase = divmod(key, 2)
        rest, hi = divmod(rest, base)
        s, lo = divmod(rest, base)
        if not lo == hi == s:
            raise AssertionError("Full evaluation did not identify the total")
        survivors[s] += mass
    return dict(status="complete", completed_layers=n, transitions=transitions,
                peak_states=peak, surviving_strings=[str(a) for a in survivors])


def fine_search(n, integer_threshold, rounds=ROUNDS):
    """Twelve fixed dyadic bisections on monotone UNREPAIRED risk only."""
    low = Fraction(integer_threshold - 1)
    high = Fraction(integer_threshold)
    evaluated = []
    def evaluate(h):
        record, table = risk_record(n, float(h))
        evaluated.append({k: v for k, v in record.items() if k != "surviving_strings"})
        print(f"N={n} H={float(h):.9f} unrepaired risk={record['risk_decimal']:.12f}", flush=True)
        return record, table
    unsafe, unsafe_table = evaluate(low)
    safe, safe_table = evaluate(high)
    if exact_risk(unsafe) <= TARGET or exact_risk(safe) > TARGET:
        raise ValueError("The integer bracket does not straddle the target error")
    for _ in range(rounds):
        mid = (low + high) / 2
        rec, table = evaluate(mid)
        if exact_risk(rec) <= TARGET:
            high, safe, safe_table = mid, rec, table
        else:
            low, unsafe, unsafe_table = mid, rec, table
    assert high - low == Fraction(1, 2**rounds)
    return dict(safe=safe, unsafe=unsafe, safe_fraction=str(high),
                unsafe_fraction=str(low), rounds=rounds, evaluated=evaluated), safe_table, unsafe_table


def certify(n, parent_directory, output):
    start = time.perf_counter()
    parent, raw, integer = load_stage9(parent_directory, n, verify_runtime=True)
    result, fine, unsafe = fine_search(n, int(parent["calibrated"]["threshold"]))
    if exact_risk(result["evaluated"][1]) != exact_risk(parent["calibrated"]):
        raise ValueError("Parent calibrated certificate differs")
    probes = []
    chosen = fine; chosen_h = result["safe"]["threshold"]
    chosen_proof = "unrepaired_fine"
    def examine(h, table):
        rec = repaired_counts(table, raw)
        if rec["status"] == "complete":
            live = [int(v) for v in rec.pop("surviving_strings")]
            rec = count_record(n, h, table, live, **rec)
        else:
            rec.update(n=n, threshold=float(h), state_sha256=state_sha(table))
        probes.append(rec)
        print(f"N={n} repaired H={float(h):.9f}: {rec['status']} "
              f"peak={rec['peak_states']} transitions={rec['transitions']}", flush=True)
        return rec
    initial = examine(chosen_h, fine)
    if initial["status"] == "complete" and exact_risk(initial) > exact_risk(result["safe"]):
        raise AssertionError("Repair increased error relative to unrepaired coverage")
    lower_grid = [float(Fraction(result["safe_fraction"]) - d)
                  for d in (Fraction(1,2), Fraction(1,8), Fraction(1,64))]
    if initial["status"] == "complete":
        for h in lower_grid:
            table = pointwise_intervals(n, h)
            rec = examine(h, table)
            if rec["status"] == "complete" and exact_risk(rec) <= TARGET and h < chosen_h:
                chosen, chosen_h, chosen_proof = table, h, "repaired_exact"
    else:
        for h in lower_grid:
            probes.append(dict(n=n, threshold=h, status="skipped", reason="initial_repair_count_capped"))
    result.update(n=n, raw_threshold=20, integer_threshold=parent["calibrated"]["threshold"],
                  raw_state_sha256=state_sha(raw), integer_state_sha256=state_sha(integer),
                  repair_probes=probes, repair_threshold=chosen_h, repair_proof=chosen_proof,
                  repair_state_sha256=state_sha(chosen), max_states=MAX_STATES,
                  max_transitions=MAX_TRANSITIONS, runtime_seconds=time.perf_counter()-start,
                  parent_certificate_sha256=hashlib.sha256((Path(parent_directory)/f"certificate_{n}.json").read_bytes()).hexdigest())
    result["source_sha256"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in (Path(__file__), ROOT/"repair_reference.py")}
    out = Path(output); out.mkdir(parents=True, exist_ok=True)
    tables = dict(fine=fine, unsafe=unsafe)
    if not np.array_equal(chosen, fine):
        tables["repair"] = chosen
    np.savez_compressed(out/f"states_{n}.npz", **tables)
    (out/f"certificate_{n}.json").write_text(json.dumps(result, indent=2)+"\n")
    return result


def load_certificate(directory, n, verify_runtime=True):
    directory = Path(directory)
    rec = json.loads((directory/f"certificate_{n}.json").read_text())
    with np.load(directory/f"states_{n}.npz") as f:
        tables = {k: f[k] for k in f.files}
    tables.setdefault("repair", tables["fine"])
    for name, h, digest in (("fine", rec["safe"]["threshold"], rec["safe"]["state_sha256"]),
                            ("unsafe", rec["unsafe"]["threshold"], rec["unsafe"]["state_sha256"]),
                            ("repair", rec["repair_threshold"], rec["repair_state_sha256"])):
        if state_sha(tables[name]) != digest:
            raise ValueError("Stage 10 state checksum differs")
        if verify_runtime and not np.array_equal(tables[name], pointwise_intervals(n, h)):
            raise ValueError("Runtime gates differ; regenerate Stage 10 certificates")
    if exact_risk(rec["safe"]) > TARGET or exact_risk(rec["unsafe"]) <= TARGET:
        raise ValueError("Invalid fine calibration bracket")
    if Fraction(rec["safe_fraction"]) - Fraction(rec["unsafe_fraction"]) != Fraction(1, 4096):
        raise ValueError("Incorrect frozen calibration resolution")
    if rec["repair_proof"] == "repaired_exact":
        chosen = [p for p in rec["repair_probes"] if p.get("threshold") == rec["repair_threshold"] and p["status"] == "complete"]
        if len(chosen) != 1 or exact_risk(chosen[0]) > TARGET:
            raise ValueError("No completed valid repaired certificate")
    elif rec["repair_proof"] != "unrepaired_fine" or not np.array_equal(tables["repair"], tables["fine"]):
        raise ValueError("Invalid repaired-control fallback")
    return rec, tables


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage9-certificates", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    out = Path(args.output)
    if list(out.glob("certificate_*.json")):
        parser.error("Use a new output directory")
    for n in (154, 589, 820):
        certify(n, args.stage9_certificates, out)


if __name__ == "__main__":
    main()
