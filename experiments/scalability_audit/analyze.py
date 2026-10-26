import csv,hashlib,json,statistics as st,subprocess
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=HERE/'results'
raw=[json.loads(x) for x in (OUT/'raw.jsonl').read_text().splitlines()]
manifest=json.loads((OUT/'manifest.json').read_text());summary=[]
diagnostic=json.loads((OUT/'diagnostic_retry.json').read_text())
for case in range(len(manifest['matrix'])):
    rows=[r for r in raw if r['case']==case]
    good=[r for r in rows if r.get('parity')]
    if not good:continue
    row=dict(case=case,**good[0]['config'],pairs=good[0]['pairs'],repeats=len(good))
    for key in ('evidence_wall_s','evidence_cpu_s','peak_plain_mib','peak_attribution_mib'):
        row[key]=st.median(r[key] for r in good)
    row['evidence_wall_min_s']=min(r['evidence_wall_s'] for r in good)
    row['evidence_wall_max_s']=max(r['evidence_wall_s'] for r in good)
    for phase in ('cs_update','stop_check'):
        row[phase+'_total_s']=st.median(r['phases'][phase]['total_s'] for r in good)
        row[phase+'_p50_s']=st.median(r['phases'][phase]['p50_s'] for r in good)
        row[phase+'_p95_s']=st.median(r['phases'][phase]['p95_s'] for r in good)
    row['cs_state_theoretical_mib']=112*row['pairs']/2**20
    replay=next((r for r in rows if r['repeat']==0),{})
    for key in ('replay_instrumented_s','replay_labels','global_stop_s','global_stop_calls','availability_s','availability_calls','censored'):
        if key in replay:row[key]=replay[key]
    if 'replay_instrumented_s' in row:
        row['same_attempt_evidence_plus_replay_s']=replay['evidence_wall_s']+row['replay_instrumented_s']
        row['availability_fraction']=row['availability_s']/row['replay_instrumented_s']
        row['global_stop_fraction']=row['global_stop_s']/row['replay_instrumented_s']
        row['replay_per_label_ms']=row['replay_instrumented_s']/row['replay_labels']*1000
        row['combined_compute_s']=row['evidence_wall_s']+row['replay_instrumented_s']
        row['serial_share_30s']=row['combined_compute_s']/(30*row['replay_labels']+row['combined_compute_s'])
    elif replay.get('censored')=='replay_timeout_45s' and 'evidence_wall_s' in replay:
        row['same_attempt_total_lower_bound_s']=replay['evidence_wall_s']+45
    summary.append(row)
keys=list(dict.fromkeys(k for r in summary for k in r))
with (OUT/'summary.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(summary)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))
git=['git','-c','safe.directory='+ROOT.as_posix()]
changes=subprocess.check_output(git+['diff','5d991e7','--name-only'],cwd=ROOT,text=True).splitlines()
checks=dict(expected_60_rows=len(raw)==60,no_worker_errors=all('error_exit' not in r for r in raw),
    all_completed_evidence_parity=all(r.get('parity') for r in raw if 'instrumented_evidence_s' in r),
    phase_counts=all(r['phases'][p]['calls']==r['config']['n'] for r in raw if r.get('parity') for p in ('cs_update','stop_check')),
    source_hashes_preserved=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in manifest['hashes'].items()),
    smallest_replay_parity=all(r.get('replay_parity') for r in raw if r['config']['s']==32 and r['repeat']==0),
    timeouts_follow_protocol=all(r.get('censored','replay_timeout_45s') in ('replay_timeout_45s','worker_timeout_180s') for r in raw),
    previous_files_preserved=all(p.startswith('experiments/scalability_audit/') for p in changes),
    main_preserved=subprocess.check_output(git+['rev-parse','main'],cwd=ROOT,text=True).strip().startswith('50a64e42'),
    diagnostic_completed=diagnostic.get('exit_code')==0 and diagnostic.get('phase')=='complete' and diagnostic.get('parity') is True)
verification=dict(checks=checks,passed=all(checks.values()),replay_timeouts=sum(r.get('censored')=='replay_timeout_45s' for r in raw),
                  worker_timeouts=sum(r.get('censored')=='worker_timeout_180s' for r in raw),
                  evidence_attempts=len(raw),completed_evidence=sum(bool(r.get('parity')) for r in raw),
                  completed_replays=sum('replay_instrumented_s' in r for r in raw))
(OUT/'verification.json').write_text(json.dumps(verification,indent=2));assert verification['passed'],verification

fig,axes=plt.subplots(1,3,figsize=(13,3.6))
for graph in ('star','complete'):
    rows=sorted([r for r in summary if r['n']==64 and r['graph']==graph],key=lambda r:r['s'])
    axes[0].plot([r['s'] for r in rows],[r['evidence_wall_s'] for r in rows],'o-',label=graph)
    axes[1].plot([r['s'] for r in rows],[r['peak_plain_mib'] for r in rows],'o-',label=graph)
    done=[r for r in rows if 'replay_instrumented_s' in r]
    axes[2].plot([r['s'] for r in done],[r['replay_instrumented_s'] for r in done],'o-',label=graph)
    censored=[r for r in rows if 'censored' in r]
    if censored:axes[2].scatter([r['s'] for r in censored],[45]*len(censored),marker='^',label='complete >45s')
for ax,label in zip(axes,('Offline evidence seconds','Plain-pass process peak MiB','Instrumented replay seconds')):
    ax.set_xlabel('Systems (64 items)');ax.set_ylabel(label);ax.legend(fontsize=8);ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(OUT/'systems_scaling.png',dpi=170);plt.close(fig)

fig,axes=plt.subplots(1,2,figsize=(10,3.7))
for systems in (100,200):
    rows=sorted([r for r in summary if r['s']==systems and r['graph']=='complete' and r['scenario']=='separated'],key=lambda r:r['n'])
    axes[0].plot([r['n'] for r in rows],[r['evidence_wall_s'] for r in rows],'o-',label=f'S={systems}')
    axes[1].plot([r['n'] for r in rows],[r['cs_update_p50_s']*1000 for r in rows],'o-',label=f'CS update S={systems}')
    axes[1].plot([r['n'] for r in rows],[r['stop_check_p50_s']*1000 for r in rows],'--',label=f'Stop S={systems}')
axes[0].set_ylabel('Offline evidence seconds');axes[1].set_ylabel('Pair-batch median milliseconds')
for ax in axes:ax.set_xlabel('Items (complete graph)');ax.legend(fontsize=8);ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(OUT/'items_and_phases.png',dpi=170);plt.close(fig)
print(json.dumps(verification,indent=2))
for row in summary:print(json.dumps(row))
