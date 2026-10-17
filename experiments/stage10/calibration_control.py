"""Model-free calibrated controls on an existing, uniform query ledger."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"stage7"))
from binary_control import ppr_interval


def evaluate_control(outcomes, ledger, raw, calibrated):
    y = np.asarray(outcomes)
    ledger = np.asarray(ledger)
    n, repeats = ledger.shape
    if len(y) != n or np.any((y != 0) & (y != 1)):
        raise ValueError("Exact binary outcomes required")
    if not np.array_equal(np.sort(ledger, axis=0), np.broadcast_to(np.arange(n)[:,None], ledger.shape)):
        raise ValueError("Ledger must contain full unique queries")
    s = np.zeros(repeats, dtype=int)
    lo = np.zeros(repeats, dtype=int); hi = np.full(repeats, n, dtype=int)
    rl = lo.copy(); ru = hi.copy()
    counts = np.empty((2,n,repeats), dtype=np.int16)
    repaired = np.empty((n,repeats), dtype=bool)
    for t in range(1,n+1):
        s += y[ledger[t-1]].astype(int)
        rl = np.maximum(rl, raw[t,s,0]); ru = np.minimum(ru, raw[t,s,1])
        lo = np.maximum(lo, calibrated[t,s,0]); hi = np.minimum(hi, calibrated[t,s,1])
        empty = lo > hi
        counts[0,t-1] = np.where(empty, np.where(rl>ru,n,rl), lo)
        counts[1,t-1] = np.where(empty, np.where(rl>ru,0,ru), hi)
        repaired[t-1] = empty
    counts[:,-1] = s[None,:]
    repaired[-1] = False
    return counts, repaired


def parent_gates(n, threshold):
    """Independent route: invoke the original float-interval implementation.

    Cache every feasible state once instead of recomputing identical raw PPR
    arrays separately for each benchmark path. No new gate formula is used.
    """
    table = np.full((n+1,n+1,2), -1, dtype=np.int16)
    table[0,0] = (0,n)
    delta = 1/float(threshold)
    # 1/(1/h) can round differently from h. Preserve the original ppr_interval
    # route only when its log gate equals the certified threshold's log gate.
    import math
    target = math.log(float(threshold))
    if math.log(1/delta) != target:
        candidates = [delta]
        down=up=delta
        for _ in range(4):
            down=float(np.nextafter(down,0.));up=float(np.nextafter(up,1.))
            candidates.extend((down,up))
        matches=[value for value in candidates if math.log(1/value)==target]
        if not matches:
            raise ValueError("Cannot match the certified boundary through the parent delta API")
        delta=matches[0]
    for t in range(1,n+1):
        lo,hi = ppr_interval(np.arange(t+1), t, n, delta)
        table[t,:t+1,0] = np.rint(lo*n).astype(int)
        table[t,:t+1,1] = np.rint(hi*n).astype(int)
    return table


def replay_control(outcomes, ledger, raw, calibrated):
    """Replay interval maxima/minima by cumulative array reductions."""
    y = np.asarray(outcomes, dtype=int)
    n,repeats = ledger.shape
    success = np.cumsum(y[ledger], axis=0)
    time = np.arange(1,n+1)[:,None]
    cl = np.maximum.accumulate(calibrated[time,success,0], axis=0)
    cu = np.minimum.accumulate(calibrated[time,success,1], axis=0)
    rl = np.maximum.accumulate(raw[time,success,0], axis=0)
    ru = np.minimum.accumulate(raw[time,success,1], axis=0)
    raw_lo,raw_hi = np.where(rl>ru,n,rl),np.where(rl>ru,0,ru)
    repair = cl > cu
    curves = np.stack([np.where(repair,raw_lo,cl),np.where(repair,raw_hi,cu)])
    curves[:,-1] = success[-1][None,:]
    repair[-1] = False
    return curves.astype(np.int16), repair
