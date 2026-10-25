"""Summarize frozen raw measurements and produce scientific plots."""
import csv
import json
from pathlib import Path
import statistics as st
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE/'results'
raw = [json.loads(line) for line in (OUT/'raw.jsonl').read_text().splitlines()]
groups = {}
for row in raw:
    groups.setdefault(row['case'], []).append(row)
summary = []
for case, rows in groups.items():
    good = [r for r in rows if 'wall_s' in r]
    config = rows[0]['config']
    if not good:
        summary.append(dict(case=case, **config, valid_repeats=0))
        continue
    def med(key, default=0):
        return st.median(r.get(key,default) for r in good)
    row = dict(case=case, **config, valid_repeats=len(good), wall_s=med('wall_s'),
        wall_min_s=min(r['wall_s'] for r in good),wall_max_s=max(r['wall_s'] for r in good),
        cpu_s=med('cpu_s'),cpu_core_percent=med('cpu_core_percent'),
        peak_plain_mib=med('peak_plain_bytes')/2**20, ready_rss_mib=med('ready_rss_bytes')/2**20,
        setup_s=med('setup_wall_s'),offline_s=med('offline_inference_wall_s'),
        panel_setup_s=med('panel_setup_wall_s'),steps=med('steps'),queries=med('queries'),
        complete=all(r['complete'] for r in good),wrong=max(int(r['wrong']) for r in good),
        reproducible=len({r['output_digest'] for r in good})==1,
        instrumented_ratio=st.median(r['profiled_wall_s']/r['wall_s'] for r in good))
    for phase in ('selection','inference','other'):
        row[phase+'_fraction']=sum(r['phases'].get(phase,{}).get('total_s',0) for r in good)/sum(r['profiled_wall_s'] for r in good)
        for metric in ('p50_s','p95_s','max_s'):
            row[phase+'_'+metric]=st.median(r['phases'].get(phase,{}).get(metric,0) for r in good)
    row['wall_per_step_s']=row['wall_s']/row['steps']
    summary.append(row)
keys = list(dict.fromkeys(k for row in summary for k in row))
with (OUT/'summary.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(summary)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2))

# Latencies are sensitivity scenarios, not observed annotation measurements.
latency=[]
for row in summary:
    if not row['valid_repeats']:continue
    for seconds in ((30,104,180) if row['kind']=='stage31' else (10,30,60)):
        compute=row['wall_s']+row['offline_s']+row['panel_setup_s']
        for workers in (1,10,100):
            human=row['queries']*seconds/workers
            latency.append(dict(case=row['case'],seconds_per_query=seconds,workers=workers,
                compute_s=compute,human_ideal_s=human,compute_fraction=compute/(compute+human),
                max_speedup_if_compute_free=(compute+human)/human,
                throughput_workers_at_equal_rates=seconds*row['queries']/compute))
with (OUT/'latency.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=latency[0]);writer.writeheader();writer.writerows(latency)

fig,axes=plt.subplots(1,3,figsize=(13,3.8))
for kind,ax in zip(('stage22','stage31','exact'),axes):
    rows=[r for r in summary if r['kind']==kind and r['valid_repeats']]
    if kind=='stage22':
        for graph in ('star','complete'):
            q=[r for r in rows if r['method']=='star_pruned' and r['n']==512 and r['scenario']=='strong' and r['graph']==graph]
            q.sort(key=lambda r:r['s']);ax.plot([r['s'] for r in q],[r['wall_s'] for r in q],'o-',label=graph)
        ax.set_xlabel('Systems (512 items)')
    elif kind=='stage31':
        for method in ('uniform_panel','unresolved_panel'):
            q=[r for r in rows if r['s']==15 and r['n']==1024 and r['method']==method]
            q.sort(key=lambda r:r['candidates']);ax.plot([r['candidates'] for r in q],[r['selection_p50_s']*1000 for r in q],'o-',label=method)
        ax.set_xscale('log');ax.set_xlabel('Candidate panels / step');ax.set_ylabel('Selection median (milliseconds)')
    else:
        for qvalue in (1,.5):
            q=[r for r in rows if r['scenario']=='strong' and r['q']==qvalue]
            q.sort(key=lambda r:r['n']);ax.plot([r['n'] for r in q],[r['wall_s'] for r in q],'o-',label=f'q={qvalue}')
        ax.set_xlabel('Items (two systems)')
    if kind!='stage31':ax.set_ylabel('Algorithm wall time (seconds)')
    ax.set_title(kind);ax.legend(fontsize=8);ax.grid(alpha=.25)
fig.tight_layout();fig.savefig(OUT/'scalability.png',dpi=180);plt.close(fig)

representatives=[next(r for r in summary if r['kind']=='stage22' and r['s']==15 and r['n']==512 and r['graph']=='complete' and r['scenario']=='strong' and r['method']=='star_pruned'),
                 next(r for r in summary if r['kind']=='stage31' and r['s']==15 and r['n']==6000 and r['method']=='unresolved_panel'),
                 next(r for r in summary if r['kind']=='exact' and r['n']==32 and r['q']==.5 and r['scenario']=='strong')]
fig,axes=plt.subplots(1,2,figsize=(10,3.7))
bottom=np.zeros(3)
for phase in ('selection','inference','other'):
    values=np.array([r[phase+'_fraction'] for r in representatives])*100
    axes[0].bar(range(3),values,bottom=bottom,label=phase);bottom+=values
axes[0].set_xticks(range(3),['Stage 22','Stage 31','Exact']);axes[0].set_ylabel('Instrumented time (%)');axes[0].legend()
for workers in (1,10,100):
    vals=[]
    for row in representatives:
        seconds=104 if row['kind']=='stage31' else 30
        vals.append(next(r['compute_fraction']*100 for r in latency if r['case']==row['case'] and r['workers']==workers and r['seconds_per_query']==seconds))
    axes[1].plot(range(3),vals,'o-',label=f'{workers} ideal workers')
axes[1].set_xticks(range(3),['Stage 22','Stage 31','Exact']);axes[1].set_ylabel('Modeled compute share (%)');axes[1].legend()
fig.tight_layout();fig.savefig(OUT/'bottlenecks.png',dpi=180);plt.close(fig)
print('rows',len(raw),'cases',len(summary),'failures',sum('error' in r or 'timeout_s' in r for r in raw))
for r in representatives:print(json.dumps(r))
