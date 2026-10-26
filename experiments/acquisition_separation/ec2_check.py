"""Post-result, exact EC2 acquisition comparison and independent edge audit."""
import argparse
import hashlib
import json
from collections import defaultdict
from fractions import Fraction as F
from itertools import combinations
from pathlib import Path

from optimal_acquisition import GRAPHS, PRIORS, Model, solve
from audit_exact import audit_record


def ec2_model(prior, graph):
    model=Model(n=2,graph=graph,kind='cell')
    p=model.probabilities(prior)
    mass=model.masses(p)
    weights=[]
    for ids in model.compatible:
        groups=defaultdict(F)
        for w in ids: groups[model.truth[w]]+=p[w]
        total=sum(groups.values())
        weights.append((total*total-sum(x*x for x in groups.values()))/2)
    restricted=[]
    for s,actions in enumerate(model.actions):
        stops=[a for a in actions if a.answer is not None]
        if len(stops)==1:
            restricted.append(tuple(stops)); continue
        # Equivalent to maximizing the expected cut of original-prior edges.
        score=[(sum(mass[c]/mass[s]*weights[c] for c,_ in a.children),a.name[1],a)
               for a in actions if a.answer is None]
        selected=min(score,key=lambda x:(x[0],x[1]))[2]
        restricted.append(tuple([selected]+stops))
    model.actions=tuple(restricted)
    model.kind='ec2_acquisition'
    return model


def audit_edge_choices(model, prior):
    p=model.probabilities(prior)
    checked=0
    for s,state in enumerate(model.states):
        ids=model.compatible[s]
        selected=[a for a in model.actions[s] if a.answer is None]
        if len({model.truth[w] for w in ids})==1:
            if selected: raise AssertionError('EC2 should stop at a resolved class')
            continue
        total=sum(p[w] for w in ids)
        candidates=[]
        for cell,x in enumerate(state[0]):
            if x!=-1: continue
            remaining=F(0)
            for value in (0,1):
                after=[w for w in ids if model.worlds[w][cell]==value]
                weight=sum((p[a]*p[b] for a,b in combinations(after,2)
                            if model.truth[a]!=model.truth[b]),F(0))
                remaining+=sum(p[w] for w in after)/total*weight
            candidates.append((remaining,cell))
        expected=min(candidates)[1]
        if len(selected)!=1 or selected[0].name!=('cell',expected):
            raise AssertionError('EC2 differs from literal hypothesis-edge enumeration')
        checked+=1
    return checked


def run(source, output):
    if output.exists(): raise ValueError('Use a new output directory')
    original=json.loads((source/'certificates.json').read_text())
    records=[]; checked_edges=checked_worlds=0
    summary={}
    for prior in PRIORS:
        summary[prior]={}
        for graph in GRAPHS:
            model=ec2_model(prior,graph)
            checked_edges+=audit_edge_choices(model,prior)
            summary[prior][graph]={}
            for alpha in (F(0),F(1,20)):
                record=solve(model,prior,alpha)
                report=audit_record(model,record)
                checked_worlds+=report['fixed_worlds']
                records.append(record)
                cell=next(r for r in original if (r['prior'],r['graph'],r['alpha'],r['kind'])
                          ==(prior,graph,str(alpha),'cell'))
                candidate=F(cell['upper']); lower=F(record['lower'])
                summary[prior][graph][str(alpha)]={
                    'optimal_cell_cost':float(candidate),'ec2_acquisition_cost':float(F(record['upper'])),
                    'certified_minimum_cell_saving':float(1-candidate/lower),
                    'cell_strictly_better':candidate<lower,
                    'ec2_lower':record['lower'],'ec2_upper':record['upper']}
                print('checked EC2',prior,graph,str(alpha),float(F(record['upper'])),flush=True)
    output.mkdir(parents=True)
    (output/'certificates.json').write_text(json.dumps(records,separators=(',',':'))+'\n')
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (output/'audit.json').write_text(json.dumps({'status':'passed','problems':16,
        'literal_edge_choice_checks':checked_edges,'exact_fixed_matrix_policy_checks':checked_worlds,
        'comparison_status':'post-result prior-work check; original gate unchanged',
        'protocol_sha256':hashlib.sha256((Path(__file__).parent/'PRIOR_WORK_CHECK.md').read_bytes()).hexdigest()},indent=2)+'\n')
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); run(args.source,args.output)
