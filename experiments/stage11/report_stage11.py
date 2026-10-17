"""Post-freeze report checks and a static figure; changes no inference rule."""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def read(path):
    with Path(path).open(newline='') as f:return list(csv.DictReader(f))


def build_report(directory):
    directory=Path(directory)
    if not json.loads((directory/'VERIFICATION.json').read_text())['all_checks_passed']:
        raise ValueError('Complete the curve audit before reporting')
    rows=read(directory/'per_trial.csv');cases={};costs={}
    for row in rows:
        key=row['case_id'];cases[key]=(row['scenario'],row['language_pair'])
        series=costs.setdefault((key,row['method']),{})
        repeat=int(row['repeat'])
        if repeat in series:raise ValueError('Duplicate saved repeat')
        series[repeat]=int(row['stop_queries'])
    for series in costs.values():
        if set(series)!=set(range(100)):raise ValueError('Incomplete repeated paths')
    comparisons=read(directory/'comparison.csv');checked=0
    for row in comparisons:
        chosen=[key for key,(scenario,lang) in cases.items() if scenario==row['scenario']
                and (row['language_pair']=='overall' or lang==row['language_pair'])]
        languages={cases[key][1] for key in chosen}
        weights={key:1/(len(languages)*sum(cases[c][1]==cases[key][1] for c in chosen)) for key in chosen}
        method=row['method'];control=row['control']
        delta=[math.fsum(weights[key]*(costs[(key,method)][r]-costs[(key,control)][r]) for key in chosen)
               for r in range(100)]
        mm=math.fsum(weights[key]*statistics.mean(costs[(key,method)].values()) for key in chosen)
        cm=math.fsum(weights[key]*statistics.mean(costs[(key,control)].values()) for key in chosen)
        mean=statistics.mean(delta)
        target_d=[statistics.mean(costs[(key,method)][r]-costs[(key,control)][r] for r in range(100)) for key in chosen]
        actual=dict(method_mean=mm,control_mean=cm,paired_mean_difference=mean,percent_change=100*mean/cm,
            conditional_mcse=statistics.stdev(delta)/10,
            largest_extra_queries=max(costs[(key,method)][r]-costs[(key,control)][r] for key in chosen for r in range(100)),
            target_mean_wins=sum(v< -1e-10 for v in target_d),target_mean_ties=sum(abs(v)<=1e-10 for v in target_d),
            target_mean_losses=sum(v>1e-10 for v in target_d))
        for field,value in actual.items():
            if not math.isclose(float(row[field]),value,abs_tol=1e-10,rel_tol=0):
                raise ValueError('Independent report reconstruction differs: '+field)
        checked+=1
    if len(rows)!=93600 or checked!=120:raise ValueError('Unexpected fixed study dimensions')
    result=dict(all_checks_passed=True,per_trial_rows_read=len(rows),independent_contrasts_checked=checked,
        scope='post-freeze reporting check from per-trial costs; inference and frozen analysis unchanged')
    (directory/'REPORT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    languages=['en-de','he-en','zh-en','overall']
    titles=[('aligned','Aligned','#2463A6'),('permuted_history','Permuted','#BD681D'),('reversed_history','Reversed','#A53F49')]
    fig,axes=plt.subplots(1,3,figsize=(12.8,4.2),sharex=True,sharey=True)
    for ax,(scenario,title,color) in zip(axes,titles):
        selected=[next(r for r in comparisons if r['scenario']==scenario and r['language_pair']==lang
            and r['method']=='budget_prediction95' and r['control']=='boosted_ppr95') for lang in languages]
        ax.errorbar([float(r['paired_mean_difference']) for r in selected],range(4),
            xerr=[1.96*float(r['conditional_mcse']) for r in selected],fmt='o',color=color,
            markersize=6,capsize=4,elinewidth=1.5)
        ax.axvline(0,color='#737373',linestyle='--',linewidth=1)
        ax.grid(axis='x',alpha=.15);ax.set_xlim(-6,11);ax.set_ylim(3.5,-.5)
        ax.set_title(title,fontsize=12,fontweight='bold',pad=11)
        ax.set_xlabel('Prediction minus boosted PPR: labels',fontsize=10)
        ax.spines[['top','right']].set_visible(False)
    axes[0].set_yticks(range(4),['English–German','Hebrew–English','Chinese–English','Equal-language mean'])
    fig.suptitle('Stage 11: prediction versus the published boosting baseline',fontsize=15,fontweight='bold',y=.98)
    fig.text(.5,.875,'Negative values use fewer labels. Error bars show ±1.96 conditional Monte Carlo standard errors.',ha='center',fontsize=10)
    fig.text(.5,.025,'Fixed WMT23 development pools; unchanged prediction paths. Uncertainty concerns query randomization only.',ha='center',fontsize=9,color='#4F4F4F')
    fig.subplots_adjust(left=.165,right=.98,bottom=.20,top=.76,wspace=.12)
    fig.savefig(directory/'boosting_comparison.png',dpi=180)
    plt.close(fig)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True)
    build_report(p.parse_args().input)
