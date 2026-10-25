"""Evidence checks, not algorithm-validity tests."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=HERE/'results'
manifest=json.loads((OUT/'manifest.json').read_text())
raw=[json.loads(line) for line in (OUT/'raw.jsonl').read_text().splitlines()]
checks={}
checks['expected_rows']=len(raw)==len(manifest['matrix'])*manifest['repeats']
checks['no_errors_or_timeouts']=all('error' not in r and 'timeout_s' not in r for r in raw)
good=[r for r in raw if 'wall_s' in r]
checks['all_plain_instrumented_outputs_equal']=all(r['parity'] for r in good)
checks['selection_count_equals_steps']=all(r['phases']['selection']['calls']==r['steps'] for r in good)
checks['inference_count_equals_steps']=all(r['phases']['inference']['calls']==r['steps'] for r in good)
checks['nonnegative_disjoint_other']=all(r['phases']['other']['total_s']>=0 for r in good)
checks['source_hashes_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
                                     for p,h in manifest['source_hashes'].items())
checks['deterministic_repeats']=all(len({r['output_digest'] for r in good if r['case']==case})==1
                                   for case in range(len(manifest['matrix'])))
hotspot=json.loads((OUT/'exact_hotspot.json').read_text())
reference=next(r for r in good if r['config']==dict(kind='exact',s=2,n=32,q=.5,scenario='strong',method='exact'))
checks['hotspot_output_equal']=hotspot['output_digest']==reference['output_digest']
preprocessing=json.loads((OUT/'preprocessing_cpu.json').read_text())
checks['preprocessing_supplement_complete']=len(preprocessing)==24
checks['preprocessing_reproducible']=all(len({r['output_digest'] for r in preprocessing
    if r['config']==config})==1 for config in manifest['matrix']
    if config['kind']=='stage22' and config['method']=='star_pruned')
git=['git','-c','safe.directory='+ROOT.as_posix()]
changes=subprocess.check_output(git+['diff','--name-only','ecdd7e6','--'],cwd=ROOT,text=True).splitlines()
checks['no_existing_tracked_files_changed']=all(p.startswith('experiments/computational_profile/') for p in changes)
checks['local_main_preserved']=subprocess.check_output(git+['rev-parse','main'],cwd=ROOT,text=True).strip().startswith('50a64e42')
report=dict(checks=checks,passed=all(checks.values()),measurements=len(good),
            capped_runs=sum(not r['complete'] for r in good),existing_tracked_changes=changes)
(OUT/'verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
assert report['passed']
