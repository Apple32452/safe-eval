"""Data access and target exclusion shared by the public benchmark and tests."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from prepare_wmt24 import matrix_hash

# An explicitly named stress-test block; this is not an exhaustive model-family
# classification. Background systems may also use LLMs or share training data.
NAMED_GROUP = ('Aya23', 'Claude-3.5', 'CommandR-plus', 'GPT-4',
               'Gemini-1.5-Pro', 'Llama3-70B', 'Mistral-Large')
PROTOCOLS = ('leave_one_out', 'named_group_holdout')


def load_data(directory):
    directory = Path(directory)
    provenance = json.loads((directory / 'DATA_PROVENANCE.json').read_text())
    datasets = {}
    for record in provenance['datasets']:
        pair = record['language_pair']
        with np.load(directory / f'wmt24_{pair}_error_free.npz', allow_pickle=False) as z:
            scores, names, items = z['scores'], z['systems'], z['items']
        if matrix_hash(scores, names, items) != record['matrix_sha256']:
            raise ValueError(f'Derived matrix checksum failed: {pair}')
        if not np.isfinite(scores).all() or np.any((scores < 0) | (scores > 1)):
            raise ValueError('invalid bounded human scores')
        datasets[pair] = (scores, names, items)
    return datasets, provenance


def fold(history_matrix, names, target, protocol):
    names = np.asarray(names)
    indices = np.flatnonzero(names == target)
    if len(indices) != 1 or protocol not in PROTOCOLS:
        raise ValueError('unknown target or holdout protocol')
    if protocol == 'leave_one_out':
        keep = names != target
    else:
        if target not in NAMED_GROUP:
            raise ValueError('target is outside the named holdout group')
        keep = ~np.isin(names, NAMED_GROUP)
    if keep.sum() < 2 or keep[indices[0]]:
        raise ValueError('invalid target exclusion')
    return np.asarray(history_matrix)[keep].copy(), names[keep].copy(), int(indices[0])


def sampling_seed(pair, target, master_seed=20261012):
    # Identical uniform paths across the two holdout protocols are intentional.
    key = f'{master_seed}|{pair}|{target}'
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'little')


class QueryOracle:
    """Simulation-only score store; evaluation routines see __call__ only."""
    def __init__(self, outcomes, trials):
        self._outcomes = np.asarray(outcomes, dtype=float)
        self._seen = np.zeros((trials, len(outcomes)), dtype=bool)
        self._rows = np.arange(trials)
        self.calls = 0

    def __call__(self, indices):
        indices = np.asarray(indices)
        if indices.shape != (len(self._rows),) or not np.issubdtype(indices.dtype, np.integer):
            raise ValueError('one integer index is required per independent path')
        if np.any(indices < 0) or np.any(indices >= len(self._outcomes)):
            raise ValueError('query outside the benchmark')
        if self._seen[self._rows, indices].any():
            raise RuntimeError('target item queried twice on a path')
        self._seen[self._rows, indices] = True
        self.calls += 1
        return self._outcomes[indices].copy()
