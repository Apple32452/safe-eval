"""Audit Stage 21 inputs, closure accounting, and repeat-zero replay."""
from __future__ import annotations
import argparse,csv,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent/"stage17"))
from prepare_scores import load_prepared
from run_stage21 import verify_lock
from summarize_stage21 import summarize
def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read_rows(path):
    with Path(path).open(newline="") as s:return list(csv.DictReader(s))
def audit(data_directory,result_directory,stage18_directory,replay_directory=None):
    verify_lock();result_directory=Path(result_directory);datasets,provenance=load_prepared(data_directory);metadata=json.loads((result_directory/"metadata.json").read_text())
    observed={r["language"]:r["matrix_sha256"] for r in provenance["reports"] if r["included"]}
    if metadata["source_sha256"]!=provenance["source_sha256"] or metadata["matrix_hashes"]!=observed or sorted(datasets)!=metadata["languages"]:raise ValueError("Data identity mismatch")
    summary=summarize(result_directory,stage18_directory);replay_rows=0
    if replay_directory:
        full=read_rows(result_directory/"replicates.csv");replay=read_rows(Path(replay_directory)/"replicates.csv");full_zero=[r for r in full if int(r["repeat"])==0];key=lambda r:(r["language"],r["method"],float(r["fraction"]))
        if {key(r):r for r in full_zero}!={key(r):r for r in replay}:raise ValueError("Repeat-zero replay mismatch")
        replay_rows=len(replay)
    verification=dict(status="passed",implementation_lock_verified=True,source_sha256=provenance["source_sha256"],languages=len(datasets),result_rows=summary["rows"],closure_and_grid_verified=True,stage18_reference_verified=True,repeat_zero_replay_rows=replay_rows,repeat_zero_exact_match=bool(replay_directory),development_gate=summary["development_gate"],replicates_sha256=sha256(result_directory/"replicates.csv"),metadata_sha256=sha256(result_directory/"metadata.json"),summary_sha256=sha256(result_directory/"SUMMARY.json"))
    (result_directory/"VERIFICATION.json").write_text(json.dumps(verification,indent=2)+"\n");print(json.dumps(verification,indent=2));return verification
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--data",required=True);p.add_argument("--input",required=True);p.add_argument("--stage18",default="experiments/stage18/results_reference");p.add_argument("--repeat-zero-replay");a=p.parse_args();audit(a.data,a.input,a.stage18,a.repeat_zero_replay)
