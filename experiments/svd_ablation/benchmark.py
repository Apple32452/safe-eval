"""Time one original 100-repeat paired case per pool and check dense-run parity."""
from collections import Counter
import csv
import json
import time

import numpy as np

from run_ablation import ROOT, run_case, verify_protocol, build_cases, METRICS


def main():
    _, datasets = verify_protocol()
    cases = build_cases(datasets)
    with (ROOT / 'results_reference/per_trial.csv').open(newline='') as f:
        saved = {(r['case_id'], r['arm'], int(r['repeat'])): r for r in csv.DictReader(f)}
    counts = Counter(c['language_pair'] for c, _, _ in cases)
    timings = []
    for pair in sorted(counts):
        case, history, outcomes = next(job for job in cases if
            job[0]['scenario'] == 'aligned' and job[0]['language_pair'] == pair)
        start = time.perf_counter()
        _, rows, ledger_hash = run_case((case, history, outcomes, 100))
        elapsed = time.perf_counter() - start
        for row in rows:
            reference = saved[(row['case_id'], row['arm'], row['repeat'])]
            for field in METRICS:
                np.testing.assert_allclose(float(row[field]), float(reference[field]), rtol=0, atol=1e-12)
        record = dict(language_pair=pair, case_id=case['case_id'], n=case['n'],
                      paired_100_repeat_seconds=elapsed, total_cases=counts[pair],
                      dense_metric_records_matched=len(rows), ledger_sha256=ledger_hash)
        timings.append(record)
        print(json.dumps(record), flush=True)
    serial = sum(r['paired_100_repeat_seconds']*r['total_cases'] for r in timings)
    result = dict(timings=timings, projected_case_seconds_serial=serial,
                  ideal_two_worker_case_seconds=serial/2,
                  caveat='Three sampled cases only. Add certificate checks, worker startup, audit and CPU contention; history/target variation may change runtime.')
    (ROOT / 'BENCHMARK.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
