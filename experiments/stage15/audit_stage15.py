"""Post-run integrity checks for compact Stage 15 results."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from frontier_experiment import CONTROLS, verify_lock
from summarize_stage15 import summarize


def audit(directory):
    directory=Path(directory)
    lock=verify_lock()
    summary=summarize(directory)
    rows=list(csv.DictReader((directory/'replicates.csv').open()))
    stage14=Path(__file__).resolve().parent.parent/'stage14'/'results_reference'/'replicates.csv'
    reference=list(csv.DictReader(stage14.open()))

    def index(records,limit=None):
        answer={}
        for row in records:
            if row['method'] not in CONTROLS:
                continue
            if limit is not None and int(row['repeat'])>=limit:
                continue
            key=(row['language'],int(row['repeat']),row['method'],float(row['fraction']))
            if key in answer:
                raise ValueError('Duplicate control row')
            answer[key]=row
        return answer

    old=index(reference)
    new=index(rows,12)
    if old != new:
        raise ValueError('The first twelve control blocks do not reproduce Stage 14')
    result=dict(
        status='passed', locked_files=len(lock['sha256']),
        result_rows=len(rows), stage14_control_rows_reproduced=len(old),
        primary_gain=summary['aggregate']['0.5']['frontier_evidence_minus_evidence_first'],
        wrong_counts={fraction:{method:summary['aggregate'][fraction][method]['wrong_count']
                                for method in summary['methods']}
                      for fraction in summary['aggregate']},
        files={name:hashlib.sha256((directory/name).read_bytes()).hexdigest()
               for name in ('metadata.json','replicates.csv','SUMMARY.json')})
    (directory/'VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    print(f"Passed: {len(rows)} rows; reproduced {len(old)} Stage 14 controls")
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    args=parser.parse_args()
    audit(args.input)
