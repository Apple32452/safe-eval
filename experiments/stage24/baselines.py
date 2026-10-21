"""Existing Stage 22 unchanged; exact scalar PPR CS as another existing baseline."""
from fractions import Fraction
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
for stage in ('stage17', 'stage22'):
    sys.path.insert(0, str(HERE.parent/stage))
from continuous_engine import make_paths
from run_stage22 import simulate_graph


def priority_for(path, orders, m, n):
    priority = np.empty((m, n), dtype=np.int64)
    for t, item in enumerate(path):
        for j, system in enumerate(orders[t]): priority[system, item] = t*m+j
    return priority


def simulate(x, edges, path, orders, events):
    m, n = x.shape[1], x.shape[0]
    return simulate_graph(x.T, edges, np.tile(path, (len(edges), 1)), events,
                          priority_for(path, orders, m, n), 'star_pruned', fractions=(1.,))


def stage22(x, edges, path, orders):
    permutations = np.tile(path, (len(edges), 1, 1))
    events, _ = make_paths(x.T, edges, permutations, threshold=40*len(edges))
    return simulate(x, edges, path, orders, events[:, 0])


def per_system(x, edges, path, orders):
    n, m = x.shape
    wealth = [[Fraction(1) for _ in range(n+1)] for _ in range(m)]
    alive = np.ones((m, n+1), dtype=bool); successes = np.zeros(m, dtype=int)
    events = np.full((len(edges), n), 2, dtype=np.int8)
    for t, item in enumerate(path):
        y = x[item]
        for v in range(m):
            alternative = Fraction(int(successes[v])+1, t+2) if y[v] else Fraction(t-int(successes[v])+1, t+2)
            for total in np.flatnonzero(alive[v]):
                null_num = int(total-successes[v]) if y[v] else int(n-t-total+successes[v])
                if null_num<=0:
                    alive[v, total] = False
                else:
                    wealth[v][total] *= alternative/Fraction(null_num, n-t)
                    if wealth[v][total] >= 20*m: alive[v, total] = False
        successes += y
        alive &= (np.arange(n+1)[None, :]>=successes[:, None]) & (np.arange(n+1)[None, :]<=successes[:, None]+n-t-1)
        for e, (a, b) in enumerate(edges):
            aa, bb = np.flatnonzero(alive[a]), np.flatnonzero(alive[b])
            if len(aa) and len(bb):
                if aa.min()>bb.max(): events[e, t] = 1
                elif aa.max()<bb.min(): events[e, t] = -1
                elif len(aa)==len(bb)==1 and aa[0]==bb[0]: events[e, t] = 0
        if t==n-1: events[:, t] = np.sign(successes[edges[:, 0]]-successes[edges[:, 1]])
    return simulate(x, edges, path, orders, events)
