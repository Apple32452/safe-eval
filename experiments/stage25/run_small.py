"""Small, exact-rational feasibility study; no dataset loaders are called."""
import csv, hashlib, json, platform, sys, time
from pathlib import Path
import numpy as np
from partial import run
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'stage24'))
from baselines import stage22
OUT=ROOT/'results_reference'
METHODS=('stage22','partial_hedge','joint_product','joint_mixture','peak_wor_adaptation','hedge_round_robin')
MASTER=20261030


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def sources():return {p.name:sha(p) for p in sorted(ROOT.iterdir()) if p.suffix in ('.py','.md')}


def previous_sources():
    return {p.relative_to(ROOT.parents[1]).as_posix():sha(p) for stage in ROOT.parent.iterdir()
            if stage.is_dir() and stage.name.startswith('stage') and stage!=ROOT
            for p in stage.iterdir() if p.suffix in ('.py','.md')}


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')


def prepare():
    OUT.mkdir(exist_ok=True);rng=np.random.default_rng(MASTER);fixtures={};cases=[]
    for n in (4,8):
        for family in ('extreme','reverse_extreme','correlated','independent','ties','antagonistic'):
            if family in ('extreme','reverse_extreme'):
                x=np.zeros((3,n),dtype=np.int64);x[0]=1
                if family=='reverse_extreme':x=1-x
            elif family=='ties':x=np.tile((np.arange(n)%2)[None,:],(3,1))
            elif family=='independent':x=(rng.random((3,n))<np.array([.8,.5,.2])[:,None]).astype(int)
            else:
                u=rng.random(n)
                x=np.array([(u if family=='correlated' or v%2==0 else 1-u)<p for v,p in enumerate((.8,.5,.2))],dtype=int)
            name=f'{n}_{family}';fixtures[name]=x
            for graph in ('star','complete'):cases.append(dict(matrix=name,graph=graph,n=n,m=3))
    np.savez_compressed(OUT/'fixtures.npz',**fixtures)
    lock=dict(master=MASTER,repeats=20,cases=cases,source_sha256=sources(),previous_source_sha256=previous_sources(),
              fixtures_sha256=sha(OUT/'fixtures.npz'),python=platform.python_version(),numpy=np.__version__)
    dump(OUT/'LOCK.json',lock);return lock


def content_hash(result):
    h=hashlib.sha256()
    for key in sorted(result):
        a=np.asarray(result[key]);h.update(key.encode());h.update(str(a.dtype).encode());h.update(a.tobytes())
    return h.hexdigest()


def main():
    lock=json.loads((OUT/'LOCK.json').read_text()) if (OUT/'LOCK.json').exists() else prepare()
    assert sources()==lock['source_sha256'];assert previous_sources()==lock['previous_source_sha256']
    assert sha(OUT/'fixtures.npz')==lock['fixtures_sha256']
    rows=[];budgets=[];reproduced=[];started=time.perf_counter()
    with np.load(OUT/'fixtures.npz') as fixtures:
        for ci,case in enumerate(lock['cases']):
            x=fixtures[case['matrix']];m,n=x.shape
            edges=np.array([[0,1],[0,2]] if case['graph']=='star' else [[0,1],[0,2],[1,2]])
            truth=np.sign(x.sum(axis=1)[edges[:,0]]-x.sum(axis=1)[edges[:,1]])
            for repeat in range(lock['repeats']):
                seed=int.from_bytes(hashlib.sha256(f'{MASTER}|{case["matrix"]}|{case["graph"]}|{repeat}'.encode()).digest()[:8],'little')
                rng=np.random.default_rng(seed);uniforms=rng.random((m,n));common=rng.permutation(n).astype(np.int32)
                for method in METHODS:
                    if method=='stage22':
                        r=stage22(x.T,edges,common,np.tile(np.arange(m),(n,1)))
                        cost=r['completion_cost'];decision=r['decision'];resolution=r['resolution_cost']
                        covered='';digest=hashlib.sha256(repr(r['acquired']).encode()).hexdigest()
                    else:
                        mode={'partial_hedge':'hedge','joint_product':'product','joint_mixture':'mixture',
                              'peak_wor_adaptation':'peak','hedge_round_robin':'hedge'}[method]
                        allocation='round_robin' if method=='hedge_round_robin' else 'anchor'
                        r=run(n,m,lambda v,i:x[v,i],edges,uniforms,mode,allocation)
                        cost=r['cost'];decision=r['decisions'];resolution=r['resolution']
                        idx=int(np.ravel_multi_index(tuple(x.sum(axis=1)),(n+1,)*m))
                        covered=int(np.unpackbits(r['masks'],axis=1)[:,idx].all());digest=content_hash(r)
                        if repeat==0:
                            duplicate=run(n,m,lambda v,i:x[v,i],edges,uniforms,mode,allocation)
                            assert content_hash(duplicate)==digest;reproduced.append(f'{case["matrix"]}|{case["graph"]}|{method}')
                    rows.append(dict(matrix=case['matrix'],graph=case['graph'],repeat=repeat,method=method,
                                     labels=cost,any_wrong=int(np.any(decision!=truth)),joint_covered=covered,trace_sha256=digest))
                    for fraction in (.25,.5,.75,1.):
                        budget=int(n*m*fraction);resolved=resolution<=budget
                        budgets.append(dict(matrix=case['matrix'],graph=case['graph'],repeat=repeat,method=method,
                             fraction=fraction,budget=budget,labels_used=min(cost,budget),
                             correct=int(np.sum(resolved&(decision==truth))),wrong=int(np.sum(resolved&(decision!=truth))),
                             unresolved=int(np.sum(~resolved))))
            print(f'{ci+1}/{len(lock["cases"])} {case["matrix"]} {case["graph"]}',flush=True)
    for name,data in (('trials.csv',rows),('budgets.csv',budgets)):
        with (OUT/name).open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    assert sources()==lock['source_sha256'];assert previous_sources()==lock['previous_source_sha256']
    dump(OUT/'VERIFICATION.json',dict(status='complete',trials=len(rows),budget_rows=len(budgets),
         seconds=time.perf_counter()-started,source_lock_verified=True,previous_sources_unchanged=True,
         replayed=reproduced,wrong_declarations=sum(r['any_wrong'] for r in rows),
         confidence_exclusions=sum(r['joint_covered']==0 for r in rows),wmt_data_accessed=False))


if __name__=='__main__':main()
