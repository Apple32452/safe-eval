"""Run locked additional controls on previously published matrices."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import scipy

from controls import METHODS, run_block, run_rebalanced
from run_study import GRAPHS, SCENARIOS

HERE = Path(__file__).resolve().parent


def summarize(original, rows):
    rng = np.random.default_rng(20261027)
    result = {}
    for scenario in SCENARIOS:
        old = [c for c in original if c['scenario'] == scenario]
        new = [c for c in rows if c['scenario'] == scenario]
        if not old:
            continue
        if [(c['scenario'], c['repeat']) for c in old] != [(c['scenario'], c['repeat']) for c in new]:
            raise AssertionError('Unpaired cases')
        result[scenario] = {}
        for graph in GRAPHS:
            candidate = np.array([c['stops'][graph]['joint_order']['charged'] for c in old])
            ids = rng.integers(len(old), size=(10000, len(old)))
            group = {'joint_mean': float(candidate.mean()),
                     'stage22_mean': float(np.mean([c['stops'][graph]['stage22']['charged'] for c in old]))}
            for method in METHODS:
                stops = [c['stops'][graph][method] for c in new]
                base = np.array([c['charged'] for c in stops])
                boot = 1-candidate[ids].mean(axis=1)/base[ids].mean(axis=1)
                group[method] = {'mean_paid': float(np.mean([c['paid'] for c in stops])),
                                 'mean_charged': float(base.mean()),
                                 'wrong_paths': sum(c['wrong'] for c in stops),
                                 'candidate_relative_saving': float(1-candidate.mean()/base.mean()),
                                 'paired_bootstrap_95': np.quantile(boot, [.025, .975]).tolist()}
            result[scenario][graph] = group
    return result


def run(source, output, limit=None):
    if output.exists():
        raise ValueError('Use a new output directory')
    data = source.read_bytes()
    original = json.loads(data)
    if limit is not None:
        original = original[:limit]
    elif len(original) != 100:
        raise ValueError('The frozen study requires all 100 saved matrices')
    output.mkdir(parents=True)
    rows = []
    for i, case in enumerate(original):
        reb = run_rebalanced(case)
        row = {'scenario': case['scenario'], 'repeat': case['repeat'],
               'stops': {g: {'rebalanced_pair_order': reb['stops'][g]} for g in GRAPHS},
               'rebalanced_trace': reb['trace'], 'extra_prefix_cells': reb['extra_prefix_cells'],
               'rebalanced_fallbacks': reb['unit_fallbacks'],
               'rebalanced_failed_status': reb['solver_failed_status']}
        for graph in GRAPHS:
            for method in METHODS[1:]:
                row['stops'][graph][method] = run_block(
                    case['scores'], SCENARIOS[case['scenario']][1],
                    case['stage22_order'], graph, method)
        rows.append(row)
        if (i+1) % 10 == 0 or i+1 == len(original):
            print('finished', i+1, '/', len(original), case['scenario'], flush=True)
        (output/'cases.json').write_text(json.dumps(rows, separators=(',', ':'))+'\n')
    summary = summarize(original, rows)
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    (output/'metadata.json').write_text(json.dumps({
        'status': 'post-result diagnostic; original expansion gate remains failed',
        'cases': len(rows), 'source_sha256': hashlib.sha256(data).hexdigest(),
        'protocol_sha256': hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest(),
        'numpy': np.__version__, 'scipy': scipy.__version__,
        'new_matrices': 0, 'human_judgments': 0}, indent=2)+'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--limit', type=int, help='Software smoke check only')
    args = parser.parse_args()
    run(args.source, args.output, args.limit)
