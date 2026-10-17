"""Presentation only: plot frozen, audited comparison table values."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True)
    parser.add_argument('--output',required=True);args=parser.parse_args()
    source=Path(args.input)
    if not json.loads((source/'VERIFICATION.json').read_text())['all_checks_passed']:
        raise ValueError('A passing full audit is required')
    with (source/'comparison.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    languages=('en-de','he-en','zh-en','overall')
    scenarios=('aligned','permuted_history','reversed_history')
    titles=('Aligned history','Permuted history','Reversed history')
    fig,axes=plt.subplots(1,3,figsize=(11.8,4.6),sharex=True,sharey=True)
    extrema=[]
    for ax,scenario,title in zip(axes,scenarios,titles):
        chosen=[next(r for r in rows if r['scenario']==scenario and r['language_pair']==lang
                     and r['method']=='budget_prediction95' and r['control']=='repair_raw95')
                for lang in languages]
        values=np.array([float(r['paired_mean_difference']) for r in chosen])
        error=1.96*np.array([float(r['conditional_mcse']) for r in chosen])
        extrema.extend(values-error);extrema.extend(values+error)
        y=np.arange(4)
        ax.axvline(0,color='#475569',linewidth=1)
        ax.errorbar(values,y,xerr=error,fmt='none',ecolor='#64748b',capsize=3,linewidth=1.2)
        ax.scatter(values,y,c=['#0f766e' if v<0 else '#c2410c' for v in values],s=50,zorder=3)
        for value,pos in zip(values,y):
            ax.annotate(f'{value:+.2f}',(value,pos),xytext=(0,9),
                        textcoords='offset points',ha='center',fontsize=9)
        ax.set_title(title,fontsize=11,fontweight='bold',pad=12)
        ax.set_yticks(y,languages);ax.set_ylim(3.6,-.65)
        ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
        ax.spines[['top','right','left']].set_visible(False)
        ax.tick_params(axis='y',length=0)
    width=max(extrema)-min(extrema)
    axes[0].set_xlim(min(extrema)-.12*width,max(extrema)+.12*width)
    fig.suptitle('Stage 10: prediction versus the selected calibrated control',
                 fontsize=14,fontweight='bold',y=.98)
    fig.supxlabel('Mean extra target labels with prediction (negative = savings)',y=.14,fontsize=11)
    fig.text(.5,.025,'Error bars: +/-1.96 conditional Monte Carlo standard errors on the fixed development pools.\n'
             'Overall weights languages equally, then systems; intervals do not measure new-data generalization.',
             ha='center',fontsize=9,color='#475569')
    fig.tight_layout(rect=(0,.18,1,.91))
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(out,dpi=180,bbox_inches='tight');plt.close(fig)


if __name__=='__main__':main()
