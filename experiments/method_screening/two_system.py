"""Strong existing paired-factor baseline; no optimization of any method."""
import hashlib
import itertools
import json
from pathlib import Path
import time
from screen import load,read,ROOT,HERE
import numpy as np

controls=load('experiments/joint_order_controls/controls.py')
engine=load('experiments/stage17/continuous_engine.py')

def path(n,seed):
    rng=np.random.default_rng(seed);remaining=list(range(n));order=[]
    while remaining:
        item=int(rng.choice(remaining));remaining.remove(item);rng.random();order.append(item)
    return order

def paired(scores,pa,pb,order):
    n=scores.shape[1];counts=np.zeros((2,3),int);logs=np.zeros(2);d=0
    for t,item in enumerate(order):
        updates=[controls.paired_update(tuple(counts[direction]),prior,n)
                 for direction,prior in enumerate(((pa,pb),(pb,pa)))]
        value=int(scores[0,item])-int(scores[1,item]);d+=value
        for direction,update in enumerate(updates):
            event=(value if direction==0 else -value)+1
            logs[direction]+=np.log(update['factor'][event]);counts[direction,event]+=1
        m=n-t-1
        if d-m>0:decision=1
        elif d+m<0:decision=-1
        elif m==0:decision=int(np.sign(d))
        elif (logs[0]>=np.log(40)) != (logs[1]>=np.log(40)):
            decision=1 if logs[0]>=np.log(40) else -1
        else:continue
        return dict(cost=2*(t+1),decision=decision,truth=int(np.sign(scores[0].sum()-scores[1].sum())),
                    purchased=[(v,int(i)) for i in order[:t+1] for v in (0,1)])
    raise AssertionError('No full-pool decision')

def main():
    out=HERE/'results';out.mkdir(exist_ok=True)
    inputs=['experiments/method_screening/two_system.py','experiments/method_screening/SUPPLEMENT_PROTOCOL.md',
            'experiments/exact_sequential_probe/results_reference.json',
            'experiments/exact_sequential_probe/sequential_probe.py',
            'experiments/joint_order_controls/controls.py','experiments/stage17/continuous_engine.py']
    lock={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs}
    (out/'two_system_lock.json').write_text(json.dumps(lock,indent=2))
    archive=read(inputs[2]);rows=[]
    scenarios={'aligned_strong':(.9,.1,.9,.1),'aligned_moderate':(.7,.3,.7,.3),
               'shifted_opposite':(.3,.7,.9,.1)}
    for name,(true_a,true_b,pa,pb) in scenarios.items():
        for rep,case in enumerate(archive[name]['cases']):
            rng=np.random.default_rng(20261024+rep+100*len(name))
            scores=(rng.random((2,32))<np.array([[true_a],[true_b]])).astype(np.int8)
            assert int(scores[0].sum()-scores[1].sum())==case['true_gap']
            order=path(32,97531+rep)
            assert order[:len(case['methods']['1']['path'])]==[i for i,_,_ in case['methods']['1']['path']]
            controls.paired_update.cache_clear();controls.null_histograms.cache_clear()
            start=time.perf_counter();base=paired(scores,pa,pb,order);elapsed=time.perf_counter()-start
            assert len(set(base['purchased']))==base['cost']
            start=time.perf_counter()
            events,_=engine.make_paths(scores,np.array([[0,1]],dtype=np.int16),np.array(order)[None,None,:],40)
            first=int(np.flatnonzero(events[0,0]!=2)[0]);stage22_cost=2*(first+1)
            stage22_time=time.perf_counter()-start
            assert int(events[0,0,first])==base['truth']
            rows.append(dict(scenario=name,repeat=rep,order=order,paired=base,
                paired_wall_s=elapsed,stage22_uniform_cost=stage22_cost,stage22_wall_s=stage22_time,
                archived_stage22_cost=case['stage22'],full=case['methods']['1'],partial=case['methods']['0.5']))
    sequential=load('experiments/exact_sequential_probe/sequential_probe.py')
    replays=[]
    for name,(true_a,true_b,pa,pb) in scenarios.items():
        rng=np.random.default_rng(20261024+100*len(name))
        scores=(rng.random((2,32))<np.array([[true_a],[true_b]])).astype(np.int8)
        for q in (1.,.5):
            start,cpu=time.perf_counter(),time.process_time()
            result=sequential.certificate(scores,pa,pb,q,97531)
            wall,cpu=time.perf_counter()-start,time.process_time()-cpu
            expected=archive[name]['cases'][0]['methods']['1' if q==1 else '0.5']
            assert json.loads(json.dumps(result))==expected
            replays.append(dict(scenario=name,q=q,wall_s=wall,cpu_s=cpu,cost=result['cost'],parity=True))
    rng=np.random.default_rng(48173);summary={}
    for name in scenarios:
        group=[r for r in rows if r['scenario']==name]
        costs={m:np.array([r['paired']['cost'] if m=='paired' else r['stage22_uniform_cost'] if m=='stage22_uniform'
                           else r[m]['cost'] for r in group]) for m in ('paired','stage22_uniform','full','partial')}
        comparisons={}
        for candidate,control in [('full','paired'),('partial','paired'),('paired','stage22_uniform')]:
            a,b=costs[candidate],costs[control];ids=rng.integers(10,size=(10000,10))
            ci=np.quantile(1-a[ids].mean(1)/b[ids].mean(1),[.025,.975])
            comparisons[candidate+'_vs_'+control]=dict(saving=1-float(a.mean()/b.mean()),ci95=ci.tolist(),
                wins=int((a<b).sum()),ties=int((a==b).sum()),losses=int((a>b).sum()))
        summary[name]=dict(mean_cost={m:float(a.mean()) for m,a in costs.items()},comparisons=comparisons,
            wrong=sum(r['paired']['decision']!=r['paired']['truth'] for r in group),
            paired_mean_wall_s=float(np.mean([r['paired_wall_s'] for r in group])),
            stage22_mean_wall_s=float(np.mean([r['stage22_wall_s'] for r in group])),
            changed_stage22_costs=sum(r['stage22_uniform_cost']!=r['archived_stage22_cost'] for r in group))
    checked=0
    for bits in itertools.product((0,1),repeat=6):
        scores=np.array(bits).reshape(2,3)
        for order in itertools.permutations(range(3)):
            r=paired(scores,.9,.1,order)
            assert r['decision']==r['truth'] and len(set(r['purchased']))==r['cost']
            checked+=1
    result=dict(summary=summary,rows=rows,replays=replays,exhaustive_paths=checked,
                note='Adapter inherits factor validity; exhaustive correctness is not a coverage proof.')
    (out/'two_system.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(summary=summary,exhaustive_paths=checked),indent=2))

if __name__=='__main__':main()
