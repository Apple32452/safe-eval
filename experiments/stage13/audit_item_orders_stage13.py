"""Additional validation: enumerate item identities, not just ternary strings.

An outcome string represents several item orders when the historical features
differ across equal-outcome items. This check enumerates all N! permutations
for 80 fixed paired pools, with N=2,...,6. It changes no research rule.
"""
from __future__ import annotations
import argparse
from fractions import Fraction
import itertools
import json
import math
from pathlib import Path

import numpy as np

from paired_engine import Q, METHODS, PairOracle, evaluate, decisions
from stage13_common import verify_lock


def main(output):
    verify_lock()
    rng=np.random.default_rng(13137)
    pools=paths=decision_count=wrong_decisions=0
    largest=Fraction(0)
    for n in range(2,7):
        ledger=np.array(list(itertools.permutations(range(n))),dtype=int).T
        repeats=math.factorial(n)
        history=rng.integers(0,2,size=(5,n))
        histories=[history,history[:,::-1],1-history]
        for a in range(n+1):
            for b in range(n-a+1):
                population=np.array([1]*a+[-1]*b+[0]*(n-a-b))
                labels=np.stack([population==1,population==-1]).astype(int)
                equal=np.flatnonzero(population==0)
                labels[:,equal[::2]]=1
                trace=evaluate(histories,PairOracle(labels,repeats),ledger)
                result=decisions(trace,population,thresholds=np.array([10*Q,40*Q]))
                truth=int(np.sign(population.sum()))
                for method in range(len(METHODS)):
                    for level,limit in enumerate((Fraction(1,5),Fraction(1,20))):
                        wrong=int((result['direction'][method,level]!=truth).sum())
                        rate=Fraction(wrong,repeats)
                        if rate>limit:raise AssertionError((n,a,b,method,level,rate,limit))
                        largest=max(largest,rate)
                        wrong_decisions+=wrong
                pools+=1;paths+=repeats;decision_count+=int(result['stop'].size)
    report=dict(status='passed',fixed_pools=pools,fully_enumerated_item_orders=paths,
                checked_method_error_setting_decisions=decision_count,
                total_wrong_decisions=wrong_decisions,largest_observed_pool_error=str(largest),
                risk_checks=['two-sided 0.2','two-sided 0.05'],max_pool_size=6,
                distinction='All item permutations for these 80 fixed pools; not all possible historical matrices or target assignments')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    main(Path(args.output))
