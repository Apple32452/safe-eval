from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/"stage8"))
from stage8_common import verify_protocol as verify_stage8, decisions, target_record, METRICS
from stage7_experiment import build_cases, write_csv
from stage9_engine import METHODS


def verify_protocol():
    lock=json.loads((ROOT/"PROTOCOL_LOCK.json").read_text())
    for relative,expected in lock["sha256"].items():
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=expected:
            raise ValueError("Stage 9 locked file changed: "+relative)
    _,datasets=verify_stage8()
    return lock,datasets


def records(case,y,trace):
    n,repeats=trace["selected"].shape
    truth=float(y.mean())
    targets=[];trials=[]
    for j,method in enumerate(METHODS):
        d=decisions(trace["counts"][j]/n,truth)
        repairs=np.zeros(repeats,dtype=int)
        if j:
            repairs=(trace["repaired"][j-1]&(np.arange(n)[:,None]<d["stop_queries"][None,:])).any(axis=0).astype(int)
        row=target_record(case,method,d,repairs)
        targets.append(row)
        for r in range(repeats):
            item={key:row[key] for key in ("case_id","scenario","language_pair","target_system","method","n")}
            item.update(repeat=r,true_mean=truth,repair_before_stop=int(repairs[r]))
            item.update({key:float(v[r]) if v.dtype.kind=="f" else int(v[r]) for key,v in d.items()})
            trials.append(item)
    return targets,trials


def aggregate(targets):
    output=[]
    for key in sorted({(r["scenario"],r["language_pair"],r["method"]) for r in targets}):
        rows=[r for r in targets if (r["scenario"],r["language_pair"],r["method"])==key]
        item=dict(scenario=key[0],language_pair=key[1],method=key[2],target_systems=len(rows),
                  trajectories=sum(r["paths"] for r in rows))
        item.update({field:float(np.mean([r[field] for r in rows])) for field in METRICS})
        output.append(item)
    return output
