"""Analysis of matched archives and bounded computational screening."""
import csv
import hashlib
import json
from pathlib import Path
import statistics as st
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from screen import HERE,ROOT,read

OUT=HERE/'results'
raw=[json.loads(x) for x in (OUT/'timings.jsonl').read_text().splitlines()]
summary=[]
for case in range(28):
    rows=[r for r in raw if r['case']==case]
    good=[r for r in rows if 'wall_s' in r]
    if not good:continue
    config=good[0]['config'];f=config['fixture']
    row=dict(case=case,fixture=f['tag'],scenario=f['scenario'],n=len(f['order']),
             graph=config['graph'],method=config['method'],repeats=len(good),paid=good[0]['paid'])
    for metric in ('wall_s','cpu_s','cpu_core_percent','peak_mib','inference_s'):
        row[metric]=st.median(r[metric] for r in good)
    row['wall_min_s']=min(r['wall_s'] for r in good);row['wall_max_s']=max(r['wall_s'] for r in good)
    row['inference_fraction']=sum(r['inference_s'] for r in good)/sum(r['wall_s'] for r in good)
    row['serial_compute_percent_30s']=100*row['wall_s']/(row['wall_s']+30*row['paid'])
    row['serial_compute_percent_10s']=100*row['wall_s']/(row['wall_s']+10*row['paid'])
    row['ideal100_compute_percent_30s']=100*row['wall_s']/(row['wall_s']+.3*row['paid'])
    row['output_repeat_parity']=len({json.dumps([r[k] for k in ('paid','charged','wrong','decisions')]) for r in good})==1
    summary.append(row)
with (OUT/'timing_summary.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=summary[0]);w.writeheader();w.writerows(summary)
(OUT/'timing_summary.json').write_text(json.dumps(summary,indent=2))

manifest=read('experiments/method_screening/results/manifest.json')
supplement=read('experiments/method_screening/results/two_system_lock.json')
two=read('experiments/method_screening/results/two_system.json')
fixed=read('experiments/method_screening/results/fixed_law.json')
fixed_lock=read('experiments/method_screening/results/fixed_law_lock.json')
hashes={**manifest['source_hashes'],**supplement,**fixed_lock}
git=['git','-c','safe.directory='+ROOT.as_posix()]
changes=subprocess.check_output(git+['diff','a9c2f50','--name-only'],cwd=ROOT,text=True).splitlines()
checks=dict(all_84_timings=len(raw)==84,
    no_errors_timeouts=all('error' not in r and 'timeout_s' not in r for r in raw),
    no_wrong_new_paths=all(not r['wrong'] for r in raw if 'wrong' in r),
    all_repeat_outputs_equal=all(r['output_repeat_parity'] for r in summary),
    sixty_archived_timing_replays= sum(r.get('archive_parity',False) for r in raw)==60,
    all_locked_sources_unchanged=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items()),
    no_previous_files_changed=all(p.startswith('experiments/method_screening/') for p in changes),
    local_main_unchanged=subprocess.check_output(git+['rev-parse','main'],cwd=ROOT,text=True).strip().startswith('50a64e42'),
    six_original_dp_replays=len(two['replays'])==6 and all(r['parity'] for r in two['replays']),
    all_uniform_paths_match_archived_prefixes=len(two['rows'])==30,
    two_system_exhaustive_paths=two['exhaustive_paths']==384,
    no_wrong_two_system_baseline=all(not r['wrong'] for r in two['summary'].values()),
    fixed_law_exhaustive_paths=fixed['exhaustive_paths']==384,
    fixed_law_thirty_full_cost_matches=len(fixed['rows'])==30 and all(r['cost']==r['full'] for r in fixed['rows']))
(OUT/'verification.json').write_text(json.dumps(dict(checks=checks,passed=all(checks.values())),indent=2))
assert all(checks.values()),checks

fig,axes=plt.subplots(1,2,figsize=(10,3.7))
for graph,ax in zip(('star','triangle'),axes):
    for method in ('stage22','paired_exact_closure'):
        rows=[r for r in summary if r['scenario']=='independent_strong' and r['graph']==graph and r['method']==method]
        rows.sort(key=lambda r:r['n'])
        ax.plot([r['n'] for r in rows],[r['wall_s'] for r in rows],'o-',label=method)
    ax.set_title(graph);ax.set_xlabel('Items (3 systems; one fixed fixture / size)');ax.set_ylabel('Wall seconds');ax.legend(fontsize=8);ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(OUT/'survivor_scaling.png',dpi=160);plt.close(fig)

fig,axes=plt.subplots(1,3,figsize=(12,3.5))
for ax,(scenario,value) in zip(axes,two['summary'].items()):
    methods=['stage22_uniform','paired','full','partial']
    values=[value['mean_cost'][m] for m in methods]
    values.insert(2,fixed['summary'][scenario]['mean_cost'])
    ax.bar(range(5),values)
    ax.set_xticks(range(5),['Stage22','Learning pair','Matched pair','DP full','DP half'],rotation=35)
    ax.set_title(scenario);ax.set_ylabel('Mean paid cells (10 archived matrices)')
fig.tight_layout();fig.savefig(OUT/'two_system_screen.png',dpi=160);plt.close(fig)
print(json.dumps(dict(checks=checks),indent=2))
for r in summary:
    if r['method']=='paired_exact_closure':print(json.dumps(r))
