"""Compute the frozen 48 acquisition problems and save exact certificates."""
import argparse
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

import numpy as np
import scipy

from optimal_acquisition import GRAPHS, KINDS, PRIORS, Model, solve

HERE=Path(__file__).resolve().parent


def summarize(records):
    result={}
    for prior in PRIORS:
        result[prior]={}
        for graph in GRAPHS:
            result[prior][graph]={}
            for alpha in ('0','1/20'):
                group={r['kind']:r for r in records
                       if (r['prior'],r['graph'],r['alpha'])==(prior,graph,alpha)}
                if len(group)!=3: raise AssertionError('Missing acquisition class')
                costs={k:{'lower':r['lower'],'upper':r['upper'],
                          'mean_cost':float(F(r['upper'])),
                          'certificate_gap':float(F(r['certified_gap']))}
                       for k,r in group.items()}
                u=F(group['cell']['upper'])
                separated=all(u<F(group[k]['lower']) for k in KINDS[1:])
                for k in KINDS[1:]:
                    costs[k]['certified_minimum_cell_saving']=float(1-u/F(group[k]['lower']))
                result[prior][graph][alpha]={'costs':costs,'strict_separation':separated}
                if prior=='independent':
                    if abs(float(u-F(group['row_uniform']['upper'])))>1e-6:
                        raise AssertionError('Independent-row symmetry prediction failed')
                if any(F(group['cell']['lower'])>F(group[k]['upper']) for k in KINDS[1:]):
                    raise AssertionError('Cell acquisition class inclusion failed')
    result['dependent_separation_exists']=any(result[p][g]['1/20']['strict_separation']
                                             for p in PRIORS[1:] for g in GRAPHS)
    return result


def run(output):
    if output.exists(): raise ValueError('Use a new output directory')
    output.mkdir(parents=True)
    models={(g,k):Model(n=2,graph=g,kind=k) for g in GRAPHS for k in KINDS}
    records=[]
    for prior in PRIORS:
        for graph in GRAPHS:
            for alpha in (F(0),F(1,20)):
                for kind in KINDS:
                    record=solve(models[graph,kind],prior,alpha)
                    records.append(record)
                    print('completed',prior,graph,str(alpha),kind,
                          'cost',round(float(F(record['upper'])),8),
                          'gap',float(F(record['certified_gap'])),flush=True)
                    (output/'certificates.json').write_text(json.dumps(records,separators=(',',':'))+'\n')
    summary=summarize(records)
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'metadata.json').write_text(json.dumps({
        'date':'2026-10-26','systems':3,'items':2,'fixed_matrices':64,'problems':48,
        'status':'exact tiny acquisition-class diagnostic; no ICML originality claim',
        'protocol_sha256':hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest(),
        'numpy':np.__version__,'scipy':scipy.__version__,
        'human_judgments':0,'WMT_data_used':False},indent=2)+'\n')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); run(args.output)
