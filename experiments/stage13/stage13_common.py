from __future__ import annotations

import hashlib
import json
from itertools import combinations
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent
sys.path.insert(0, str(ROOT.parent / 'stage7'))
from prepare_wmt23 import load_data


def keyed_seed(*parts):
    return int.from_bytes(hashlib.sha256('|'.join(map(str, parts)).encode()).digest()[:8], 'little')


def exclude_pair(scores, names, a, b):
    scores, names = np.asarray(scores), np.asarray(names)
    if scores.ndim != 2 or names.shape != (len(scores),) or a == b or min(a, b) < 0 or max(a, b) >= len(scores):
        raise ValueError('Two distinct target rows required')
    keep = np.ones(len(names), dtype=bool)
    keep[[a, b]] = False
    if keep.sum() < 2:
        raise ValueError('Insufficient historical systems')
    return scores[keep].copy(), names[keep].copy()


def build_cases(directory=None, master=20261021):
    datasets, provenance = load_data(directory or ROOT.parent / 'stage7' / 'data')
    cases = []
    for language, (scores, names, items) in sorted(datasets.items()):
        for a, b in combinations(range(len(names)), 2):
            background, background_names = exclude_pair(scores, names, a, b)
            permutation = np.random.default_rng(keyed_seed(master, language, 'history_permutation')).permutation(scores.shape[1])
            histories = [background, background[:, permutation].copy(), 1 - background]
            meta = dict(language_pair=language, system_a=str(names[a]), system_b=str(names[b]),
                        n=scores.shape[1], background_systems=background_names.tolist(),
                        seed=keyed_seed(master, language, names[a], names[b]))
            meta['case_id'] = hashlib.sha256(f'{language}|{names[a]}|{names[b]}'.encode()).hexdigest()[:16]
            meta['history_hashes'] = [hashlib.sha256(np.asarray(h, dtype='<f8').tobytes()).hexdigest() for h in histories]
            cases.append((meta, histories, scores[[a, b]].copy()))
    return cases, provenance


def ledger_for(n, repeats, seed):
    rng = np.random.Generator(np.random.PCG64(seed))
    return np.stack([rng.permutation(n) for _ in range(repeats)], axis=1)


def verify_lock():
    lock = json.loads((ROOT / 'PROTOCOL_LOCK.json').read_text())
    for path, expected in lock['sha256'].items():
        if hashlib.sha256((REPO / path).read_bytes()).hexdigest() != expected:
            raise ValueError('Locked file changed: ' + path)
    return lock
