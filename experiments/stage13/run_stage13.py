"""Reproduce the frozen paired-comparison development experiment."""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np

from paired_engine import METHODS, LEVELS, PairOracle, evaluate, decisions
from stage13_common import build_cases, ledger_for, verify_lock


def run_case(task):
    meta, histories, labels, repeats, directory = task
    n = meta['n']
    ledger = ledger_for(n, repeats, meta['seed'])
    trace = evaluate(histories, PairOracle(labels, repeats), ledger)
    decision = decisions(trace, labels[0] - labels[1])
    output = Path(directory) / 'traces' / (meta['case_id'] + '.npz')
    np.savez_compressed(output, **trace, **decision)
    return dict(**meta, full_difference_total=int((labels[0] - labels[1]).sum()),
                trace_sha256=hashlib.sha256(output.read_bytes()).hexdigest())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeats', type=int, default=50)
    parser.add_argument('--workers', type=int, default=2)
    parser.add_argument('--output', default='results/stage13_reference')
    parser.add_argument('--max-cases', type=int, default=None, help='Software checks only; not the reference experiment')
    args = parser.parse_args()
    if args.repeats < 1 or args.workers < 1 or (args.max_cases is not None and args.max_cases < 1):
        parser.error('Positive counts required')
    lock = verify_lock()
    cases, provenance = build_cases()
    if len(cases) != 237:
        raise ValueError('Expected every one of the 237 system pairs')
    if args.max_cases:
        cases = cases[:args.max_cases]
    directory = Path(args.output).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    if (directory / 'run_metadata.json').exists() or list(directory.glob('traces/*.npz')):
        raise ValueError('Use a new output directory; existing results are preserved')
    (directory / 'traces').mkdir()
    tasks = [(*case, args.repeats, str(directory)) for case in cases]
    start = time.time()
    records = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_case, task) for task in tasks]
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            print(f"{len(records):3}/{len(cases)} {record['language_pair']} {record['system_a']} / {record['system_b']} ({time.time()-start:.1f}s)", flush=True)
    order = {case[0]['case_id']: i for i, case in enumerate(cases)}
    records.sort(key=lambda item: order[item['case_id']])
    metadata = dict(stage=13, repeats=args.repeats, methods=METHODS, levels=LEVELS,
                    frozen_protocol=lock, cases=records, data_provenance=provenance,
                    complete_reference=(len(cases) == 237 and args.repeats == 50),
                    python=sys.version, numpy=np.__version__, platform=platform.platform(),
                    elapsed_seconds=time.time()-start)
    (directory / 'run_metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(f'Finished {len(records)} pairs; full ledger/wealth traces: {directory}', flush=True)


if __name__ == '__main__':
    main()
