"""One controlled predictor-law baseline; no candidate acceleration."""
import ast
import hashlib
import inspect
import json
import time
from screen import HERE,ROOT
import two_system as adapter
import numpy as np

def main():
    out=HERE/'results'
    if (out/'fixed_law.json').exists() and not (out/'fixed_law_initial_direction_mismatch.json').exists():
        (out/'fixed_law_initial_direction_mismatch.json').write_bytes((out/'fixed_law.json').read_bytes())
    paths=['experiments/method_screening/FIXED_LAW_PROTOCOL.md','experiments/method_screening/fixed_law.py']
    (out/'fixed_law_lock.json').write_text(json.dumps({p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},indent=2))
    mod=adapter.controls
    original=mod.paired_update
    tree=ast.parse(inspect.getsource(original.__wrapped__))
    tree.body[0].decorator_list=[]
    changed=0
    for node in ast.walk(tree):
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='alt' for t in node.targets):
            node.value=ast.Name(id='prior',ctx=ast.Load());changed+=1
    assert changed==1
    namespace=dict(mod.__dict__)
    exec(compile(ast.fix_missing_locations(tree),'<fixed-law evaluation adapter>','exec'),namespace)
    mod.paired_update=namespace['paired_update']
    paired_tree=ast.parse(inspect.getsource(adapter.paired))
    replacements=0
    for node in ast.walk(paired_tree):
        if isinstance(node,ast.comprehension) and isinstance(node.iter,ast.Call) and isinstance(node.iter.func,ast.Name) and node.iter.func.id=='enumerate':
            node.iter.args[0]=ast.parse('((pa,pb),(1-pb,1-pa))',mode='eval').body
            replacements+=1
    assert replacements==1
    paired_namespace=dict(adapter.paired.__globals__)
    exec(compile(ast.fix_missing_locations(paired_tree),'<matched directional-law adapter>','exec'),paired_namespace)
    adapter.paired=paired_namespace['paired']
    data=json.loads((out/'two_system.json').read_text());rows=[]
    for row in data['rows']:
        name,rep=row['scenario'],row['repeat']
        a,b,pa,pb={'aligned_strong':(.9,.1,.9,.1),'aligned_moderate':(.7,.3,.7,.3),
                   'shifted_opposite':(.3,.7,.9,.1)}[name]
        rng=np.random.default_rng(20261024+rep+100*len(name))
        scores=(rng.random((2,32))<np.array([[a],[b]])).astype(np.int8)
        mod.null_histograms.cache_clear()
        start=time.perf_counter();result=adapter.paired(scores,pa,pb,row['order']);elapsed=time.perf_counter()-start
        assert result['decision']==result['truth'] and len(set(result['purchased']))==result['cost']
        rows.append(dict(scenario=name,repeat=rep,cost=result['cost'],full=row['full']['cost'],
                         partial=row['partial']['cost'],wall_s=elapsed))
    checks=0
    import itertools
    for bits in itertools.product((0,1),repeat=6):
        scores=np.array(bits).reshape(2,3)
        for order in itertools.permutations(range(3)):
            r=adapter.paired(scores,.9,.1,order)
            assert r['decision']==r['truth'] and len(set(r['purchased']))==r['cost'];checks+=1
    summary={};rng=np.random.default_rng(48173)
    for scenario in dict.fromkeys(r['scenario'] for r in rows):
        group=[r for r in rows if r['scenario']==scenario]
        base=np.array([r['cost'] for r in group]);comparisons={}
        for method in ('full','partial'):
            a=np.array([r[method] for r in group]);ids=rng.integers(10,size=(10000,10))
            ci=np.quantile(1-a[ids].mean(1)/base[ids].mean(1),[.025,.975])
            comparisons[method]=dict(saving=1-float(a.mean()/base.mean()),ci95=ci.tolist(),
                wins=int((a<base).sum()),ties=int((a==base).sum()),losses=int((a>base).sum()))
        summary[scenario]=dict(mean_cost=float(base.mean()),mean_wall_s=float(np.mean([r['wall_s'] for r in group])),comparisons=comparisons)
    result=dict(rows=rows,summary=summary,exhaustive_paths=checks)
    (out/'fixed_law.json').write_text(json.dumps(result,indent=2));print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
