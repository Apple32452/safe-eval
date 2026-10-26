"""Validate exact certificates without solving or trusting numerical LP output."""
import argparse
import hashlib
import json
from collections import defaultdict
from fractions import Fraction as F
from functools import lru_cache
from itertools import product
from pathlib import Path

from optimal_acquisition import GRAPHS, KINDS, PRIORS, Model


def independent_probabilities(model, name):
    # In lexicographic 000,...,111 column order, directly from PROTOCOL.md.
    numerators={'independent':(4,16,4,16,1,4,1,4),
                'monotone':(77,113,5,113,5,5,5,77),
                'opposed':(5,5,5,293,77,5,5,5),
                'one_hot':(5,221,113,5,41,5,5,5)}
    denominator=50 if name=='independent' else 400
    cols={bits:F(v,denominator) for bits,v in zip(product((0,1),repeat=3),numerators[name])}
    result=[]
    for world in model.worlds:
        mass=F(1)
        for item in range(model.n): mass*=cols[tuple(world[v*model.n+item] for v in range(3))]
        result.append(mass)
    assert sum(result)==1 and min(result)>0
    return tuple(result)


def compatible(obs, world):
    return all(x==-1 or x==y for x,y in zip(obs,world))


def actual_transitions(model, state, action, world):
    obs,opened,active=state
    name=action.name
    if name[0]=='cell':
        options=[((name[1],),F(1),opened,active)]
    elif name[0]=='row':
        cells=[c for c in range(name[1]*model.n,(name[1]+1)*model.n) if obs[c]==-1]
        options=[((c,),F(1,len(cells)),opened,active) for c in cells]
    elif name[0]=='block':
        items=[i for i in range(model.n) if not opened & (1<<i)]
        rows=[v for v in range(3) if name[1] & (1<<v)]
        options=[(tuple(v*model.n+i for v in rows),F(1,len(items)),opened | (1<<i),name[1])
                 for i in items]
    else: raise AssertionError('Not a query action')
    result={}
    for cells,prob,new_open,new_active in options:
        changed=list(obs)
        if len(cells)!=action.cost or any(changed[c]!=-1 for c in cells):
            raise AssertionError('Bad cost or repurchased cell')
        for c in cells: changed[c]=world[c]
        target=model.index[(tuple(changed),new_open,new_active)]
        result[target]=result.get(target,F(0))+prob
    return result


def validate_action_class(model):
    checked=0
    for s,state in enumerate(model.states):
        obs,opened,active=state
        if model.kind=='cell': expected={('cell',c) for c,x in enumerate(obs) if x==-1}
        elif model.kind=='row_uniform':
            expected={('row',v) for v in range(3) if -1 in obs[v*model.n:(v+1)*model.n]}
        else:
            expected={('block',mask) for mask in range(1,8) if mask & active == mask}
            if opened==(1<<model.n)-1: expected=set()
        actions=model.actions[s]
        if {a.name for a in actions if a.answer is None}!=expected:
            raise AssertionError('Missing or extra legal acquisition action')
        worlds=[i for i,w in enumerate(model.worlds) if compatible(obs,w)]
        if tuple(worlds)!=model.compatible[s]: raise AssertionError('Wrong compatible set')
        if {a.answer for a in actions if a.answer is not None}!={model.truth[w] for w in worlds}:
            raise AssertionError('Missing terminal report')
        for action in actions:
            if action.answer is not None: continue
            for w in worlds:
                direct=actual_transitions(model,state,action,model.worlds[w])
                saved=defaultdict(F)
                for child,p in action.children:
                    if compatible(model.states[child][0],model.worlds[w]): saved[child]+=p
                if direct!=dict(saved) or sum(direct.values())!=1:
                    raise AssertionError('Action flow does not describe actual purchases')
                if any(c<=s for c in direct): raise AssertionError('Nonacyclic transition')
                checked+=1
    return checked


def audit_record(model, record):
    p=independent_probabilities(model,record['prior'])
    if p!=model.probabilities(record['prior']): raise AssertionError('Prior mismatch')
    alpha=F(record['alpha']); full=F(record['full_evaluation_mixture'])
    policy={int(s):tuple((a,F(q)) for a,q in acts) for s,acts in record['policy'].items()}
    costs,errors=[],[]
    for world_id,world in enumerate(model.worlds):
        sums=[sum(world[v*model.n:(v+1)*model.n]) for v in range(3)]
        truth=tuple((sums[a]>sums[b])-(sums[a]<sums[b]) for a,b in GRAPHS[model.graph])
        if truth!=model.truth[world_id]: raise AssertionError('Wrong fixed-pool target')
        @lru_cache(None)
        def walk(s):
            if s not in policy: raise AssertionError('Unspecified reachable policy state')
            choices=policy[s]
            if sum(q for _,q in choices)!=1 or min(q for _,q in choices)<=0:
                raise AssertionError('Invalid randomized policy')
            cost=error=terminal=F(0)
            for a,q in choices:
                action=model.actions[s][a]
                if action.answer is not None:
                    error+=q*int(action.answer!=truth); terminal+=q
                else:
                    cost+=q*action.cost
                    for child,t in actual_transitions(model,model.states[s],action,world).items():
                        c,e,done=walk(child)
                        cost+=q*t*c; error+=q*t*e; terminal+=q*t*done
            return cost,error,terminal
        c,e,done=walk(model.root)
        if done!=1: raise AssertionError('Nontermination')
        costs.append((1-full)*c+full*3*model.n)
        errors.append((1-full)*e)
    if not 0<=full<=1 or max(errors)>alpha:
        raise AssertionError('Per-fixed-matrix error bound violated')
    if list(map(str,costs))!=record['world_costs'] or list(map(str,errors))!=record['world_errors']:
        raise AssertionError('Saved per-world results differ from exact replay')
    upper=sum(q*c for q,c in zip(p,costs))
    masses=[sum(p[w] for w in ws) for ws in model.compatible]
    values=[None]*len(model.states)
    penalties=tuple(map(F,record['error_penalties']))
    if min(penalties)<0: raise AssertionError('Negative dual penalty')
    inequalities=0
    for s in reversed(range(len(model.states))):
        candidates=[]
        logical=len({model.truth[w] for w in model.compatible[s]})==1
        for action in model.actions[s]:
            if action.answer is not None:
                if alpha==0:
                    if logical: candidates.append(F(0))
                else:
                    candidates.append(sum(penalties[w] for w in model.compatible[s]
                                          if model.truth[w]!=action.answer))
            elif all(values[c] is not None for c,_ in action.children):
                candidates.append(masses[s]*action.cost+sum(t*values[c] for c,t in action.children))
            inequalities+=1
        if candidates: values[s]=min(candidates)
    lower=values[model.root]-(alpha*sum(penalties) if alpha else 0)
    if str(lower)!=record['lower'] or str(upper)!=record['upper'] or str(upper-lower)!=record['certified_gap']:
        raise AssertionError('Exact cost bounds differ from saved certificate')
    if lower>upper: raise AssertionError('Invalid dual bound')
    return {'fixed_worlds':len(model.worlds),'action_bounds_checked':inequalities,
            'maximum_error':max(errors),'certificate_gap':upper-lower}


def audit(folder):
    records=json.loads((folder/'certificates.json').read_text())
    keys={(r['prior'],r['graph'],r['alpha'],r['kind']) for r in records}
    expected={(p,g,a,k) for p in PRIORS for g in GRAPHS for a in ('0','1/20') for k in KINDS}
    if len(records)!=48 or keys!=expected: raise AssertionError('Incomplete frozen grid')
    models={(g,k):Model(n=2,graph=g,kind=k) for g in GRAPHS for k in KINDS}
    transitions=sum(validate_action_class(m) for m in models.values())
    reports=[audit_record(models[r['graph'],r['kind']],r) for r in records]
    metadata=json.loads((folder/'metadata.json').read_text())
    digest=hashlib.sha256((Path(__file__).parent/'PROTOCOL.md').read_bytes()).hexdigest()
    if metadata['protocol_sha256']!=digest: raise AssertionError('Changed frozen protocol')
    summary=json.loads((folder/'summary.json').read_text())
    separations=[]
    for prior in PRIORS:
        for graph in GRAPHS:
            for alpha in ('0','1/20'):
                r={x['kind']:x for x in records if (x['prior'],x['graph'],x['alpha'])==(prior,graph,alpha)}
                separated=all(F(r['cell']['upper'])<F(r[k]['lower']) for k in KINDS[1:])
                if separated: separations.append([prior,graph,alpha])
                group=summary[prior][graph][alpha]
                if separated!=group['strict_separation']: raise AssertionError('Wrong separation flag')
                for kind in KINDS:
                    for field in ('lower','upper'):
                        if group['costs'][kind][field]!=r[kind][field]: raise AssertionError('Summary bounds mismatch')
    return {'status':'passed','optimization_problems':len(records),
            'exact_fixed_matrix_policy_checks':sum(x['fixed_worlds'] for x in reports),
            'legal_action_world_transitions':transitions,
            'exact_action_bounds_checked':sum(x['action_bounds_checked'] for x in reports),
            'maximum_fixed_matrix_error':str(max(x['maximum_error'] for x in reports)),
            'largest_cost_certificate_gap':str(max(x['certificate_gap'] for x in reports)),
            'strict_separations':separations,'protocol_sha256':digest}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); report=audit(args.input)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
