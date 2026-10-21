"""Audit Stage 21 and compare closure conclusions with Stage 18."""
from __future__ import annotations

import argparse,csv,hashlib,json,math,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"stage14"))
from shared_pilot import FRACTIONS
from run_stage21 import METHODS

FIELDS=("pairs","systems","items","budget","labels","correct","wrong","unresolved","resolved_pairs","direct_edges","closure_added","reached_prefix","complete_ranking")
def record(row): return {k:int(row[k]) for k in FIELDS}
def stats(values):
    mean=sum(values)/len(values);mcse=(sum((x-mean)**2 for x in values)/(len(values)-1)/len(values))**.5 if len(values)>1 else None
    return dict(mean=mean,conditional_repeat_mcse=round(mcse,12) if mcse is not None else None,wins=sum(x>0 for x in values),ties=sum(x==0 for x in values),losses=sum(x<0 for x in values),values=values)
def load_csv(path):
    payload=Path(path).read_bytes();return payload,list(csv.DictReader(payload.decode().splitlines()))


def summarize(directory,stage18_directory):
    directory=Path(directory); payload,rows=load_csv(directory/"replicates.csv");metadata=json.loads((directory/"metadata.json").read_text())
    control_payload,control_rows=load_csv(Path(stage18_directory)/"replicates.csv")
    if hashlib.sha256(control_payload).hexdigest()!=metadata["stage18_replicates_sha256"]:raise ValueError("Stage 18 reference mismatch")
    expected={(l,r,f,m) for l in metadata["languages"] for r in range(metadata["repeats"]) for f in FRACTIONS for m in METHODS}
    indexed={}
    for row in rows:
        key=(row["language"],int(row["repeat"]),float(row["fraction"]),row["method"])
        if key in indexed:raise ValueError("Duplicate candidate result")
        value=record(row)
        if value["correct"]+value["wrong"]+value["unresolved"]!=value["pairs"]:raise ValueError("Pair accounting failed")
        if value["resolved_pairs"]!=value["correct"]+value["wrong"] or value["closure_added"]!=value["resolved_pairs"]-value["direct_edges"]:raise ValueError("Closure accounting failed")
        if not 0<=value["labels"]<=value["budget"]:raise ValueError("Label accounting failed")
        indexed[key]=value
    if set(indexed)!=expected:raise ValueError("Incomplete candidate grid")
    control={}
    for row in control_rows:
        key=(row["language"],int(row["repeat"]),float(row["fraction"]))
        if row["method"]=="common_random_items" and key[:2] in {(l,r) for l in metadata["languages"] for r in range(metadata["repeats"])} and key[2] in FRACTIONS:control[key]=record({**row,"direct_edges":row["resolved_pairs"],"closure_added":"0","complete_ranking":str(int(int(row["correct"])==int(row["pairs"]) and int(row["wrong"])==0))})
    expected_control={(l,r,f) for l in metadata["languages"] for r in range(metadata["repeats"]) for f in FRACTIONS}
    if set(control)!=expected_control:raise ValueError("Control grid mismatch")
    for l in metadata["languages"]:
        for r in range(metadata["repeats"]):
            for m in METHODS:
                sequence=[indexed[l,r,f,m] for f in FRACTIONS]
                for field in ("labels","wrong","resolved_pairs","direct_edges","reached_prefix"):
                    values=[x[field] for x in sequence]
                    if values!=sorted(values):raise ValueError("Nonmonotone "+field)
    result=dict(status="passed",rows=len(rows),languages=metadata["languages"],repeats=metadata["repeats"],methods=list(METHODS),replicates_sha256=hashlib.sha256(payload).hexdigest(),stage18_replicates_sha256=hashlib.sha256(control_payload).hexdigest(),aggregate={},by_language={})
    for f in FRACTIONS:
        cell=result["aggregate"][str(f)]={}
        base_totals=[sum(control[l,r,f]["correct"] for l in metadata["languages"]) for r in range(metadata["repeats"])]
        base_mean=sum(base_totals)/len(base_totals)
        cell["common_random_items"]=dict(mean_correct_total=base_mean,wrong_count=sum(control[l,r,f]["wrong"] for l in metadata["languages"] for r in range(metadata["repeats"])))
        for m in METHODS:
            totals=[sum(indexed[l,r,f,m]["correct"] for l in metadata["languages"]) for r in range(metadata["repeats"])]
            mean=sum(totals)/len(totals);differences=[a-b for a,b in zip(totals,base_totals)]
            denominator=len(metadata["languages"])*metadata["repeats"]
            cell[m]=dict(
                mean_correct_total=mean,
                mean_direct_edges=sum(
                    indexed[l,r,f,m]["direct_edges"]
                    for l in metadata["languages"] for r in range(metadata["repeats"])
                )/denominator,
                mean_closure_added=sum(
                    indexed[l,r,f,m]["closure_added"]
                    for l in metadata["languages"] for r in range(metadata["repeats"])
                )/denominator,
                complete_ranking_count=sum(
                    indexed[l,r,f,m]["complete_ranking"]
                    for l in metadata["languages"] for r in range(metadata["repeats"])),
                wrong_count=sum(
                    indexed[l,r,f,m]["wrong"]
                    for l in metadata["languages"] for r in range(metadata["repeats"])))
            cell[m+"_minus_common"]=stats(differences);cell[m+"_relative_gain_percent"]=(100*(mean-base_mean)/base_mean if base_mean else math.inf)
    for l in metadata["languages"]:
        result["by_language"][l]={}
        for f in FRACTIONS:
            differences=[indexed[l,r,f,"selected_chain"]["correct"]-control[l,r,f]["correct"] for r in range(metadata["repeats"])]
            result["by_language"][l][str(f)]=stats(differences)
    primary=result["aggregate"]["0.75"];comparison=primary["selected_chain_minus_common"]
    positive=sum(result["by_language"][l]["0.75"]["mean"]>0 for l in metadata["languages"]);cw=primary["selected_chain"]["wrong_count"];bw=primary["common_random_items"]["wrong_count"];mcse=comparison["conditional_repeat_mcse"]
    gate=(comparison["mean"]>0 and mcse is not None and comparison["mean"]>2*mcse and positive>len(metadata["languages"])/2 and cw<=bw)
    result["development_gate"]=dict(passed=gate,comparison=comparison,exceeds_two_mcse=(mcse is not None and comparison["mean"]>2*mcse),positive_languages=positive,included_languages=len(metadata["languages"]),candidate_wrong=cw,baseline_wrong=bw)
    (directory/"SUMMARY.json").write_text(json.dumps(result,indent=2)+"\n");print(json.dumps(result["development_gate"],indent=2));return result


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--input",required=True);p.add_argument("--stage18",default="experiments/stage18/results_reference");a=p.parse_args();summarize(a.input,a.stage18)
