"""Presentation-only plot of the predeclared primary budget diagnostics."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main(directory):
    with (directory/'budgets.csv').open(newline='') as stream:
        rows=list(csv.DictReader(stream))
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(1,2,figsize=(10,4.7),sharey=True)
    policies=[('paired_ppr','Paired PPR','#334155'),('reserve_zero','Matched zero-history reserve','#d97706'),
              ('reserve_aligned','Historical reserve','#2563eb')]
    for axis,level,title in zip(axes,('pairwise_95','family_95'),('95% per pair','95% across all 237 pairs')):
        for method,label,color in policies:
            selected=sorted([r for r in rows if r['language_pair']=='overall' and r['error_setting']==level and r['method']==method],
                            key=lambda r:float(r['budget_fraction']))
            axis.plot([100*float(r['budget_fraction']) for r in selected],
                      [100*float(r['correct_decision_rate']) for r in selected],marker='o',label=label,color=color,lw=2)
        axis.set(title=title,xlabel='Fraction of full labeling budget (%)',xticks=[25,50,75],ylim=(0,100),yticks=range(0,101,20))
        axis.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('Comparisons correctly certified (%)')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.5,.04),fontsize=10)
    fig.suptitle('How many full-benchmark pairwise conclusions can a smaller evaluation certify?',fontsize=13)
    fig.text(.5,.005,'WMT23 development data; 50 query orders per pair; equal language weighting; unresolved pairs remain in the denominator.\n'
             'Family-wide reserve curves have a component-cap limitation (see CAP_LIMITATION.md). Error settings apply separately to each method.',
             ha='center',fontsize=8.2,color='#475569')
    fig.tight_layout(rect=(0,.14,1,.94))
    fig.savefig(directory/'paired_budget_comparison.png',dpi=180,bbox_inches='tight',facecolor='white')
    fig.savefig(directory/'paired_budget_comparison.pdf',bbox_inches='tight',facecolor='white')
    plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',required=True)
    args=parser.parse_args()
    main(Path(args.input))
