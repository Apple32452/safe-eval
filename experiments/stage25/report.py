import csv,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results_reference'


def write(name,rows):
    with (OUT/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    with (OUT/'trials.csv').open(newline='',encoding='utf-8') as f:rows=list(csv.DictReader(f))
    with (OUT/'budgets.csv').open(newline='',encoding='utf-8') as f:budgets=list(csv.DictReader(f))
    methods=list(dict.fromkeys(r['method'] for r in rows));cells=sorted({(r['matrix'],r['graph']) for r in rows})
    summary=[];paired=[];overall=[]
    for matrix,graph in cells:
        group=[r for r in rows if r['matrix']==matrix and r['graph']==graph]
        values={method:np.array([int(r['labels']) for r in sorted(group,key=lambda r:int(r['repeat'])) if r['method']==method]) for method in methods}
        for method,a in values.items():
            rr=[r for r in group if r['method']==method]
            summary.append(dict(matrix=matrix,graph=graph,method=method,mean_labels=float(a.mean()),
                                any_wrong=sum(int(r['any_wrong']) for r in rr)))
        for method,b in values.items():
            if method=='partial_hedge':continue
            d=values['partial_hedge']-b
            paired.append(dict(matrix=matrix,graph=graph,baseline=method,mean_difference=float(d.mean()),
                 relative_change_percent=float(100*d.mean()/b.mean()),paired_mcse=float(d.std(ddof=1)/np.sqrt(len(d))),
                 wins=int((d<0).sum()),ties=int((d==0).sum()),losses=int((d>0).sum())))
    for method in methods:
        rr=[r for r in rows if r['method']==method]
        coverage=[int(r['joint_covered']) for r in rr if r['joint_covered']!='']
        overall.append(dict(method=method,mean_labels=float(np.mean([int(r['labels']) for r in rr])),
                 anytime_coverage='' if not coverage else float(np.mean(coverage)),any_wrong=sum(int(r['any_wrong']) for r in rr)))
    write('per_cell.csv',summary);write('paired.csv',paired);write('overall.csv',overall)
    budget_summary=[]
    for method in methods:
        for fraction in (.25,.5,.75,1.):
            rr=[r for r in budgets if r['method']==method and float(r['fraction'])==fraction]
            budget_summary.append(dict(method=method,fraction=fraction,**{k:float(np.mean([int(r[k]) for r in rr])) for k in ('labels_used','correct','wrong','unresolved')}))
    write('budget_summary.csv',budget_summary)
    costs={r['method']:r['mean_labels'] for r in overall}
    text='# Adaptive partial-cell inference: final assessment\n\n'
    text+='**NO-GO for this candidate as an ICML-level new contribution.** Partial-cell acquisition can save labels relative to Stage 22, but the separation is already attained by existing joint evidence controls. No new correlation-sharing or efficiency theorem beyond those controls has been established.\n\n'
    text+='| Method | Mean unique labels | Candidate change vs method |\n|---|---:|---:|\n'
    for r in overall:text+=f"| {r['method']} | {r['mean_labels']:.3f} | {100*(costs['partial_hedge']/r['mean_labels']-1):+.2f}% |\n"
    text+='\nThese are equally weighted results on 24 fixed small binary matrix/graph cells and 20 matched path seeds, not an estimate of WMT performance. Partial-cell methods share per-system uniform streams; Stage 22 necessarily follows a common paired item stream. Equal budgets, estimands and nominal family error are matched; purchased paths differ.\n\n'
    for base in methods:
        if base=='partial_hedge':continue
        rr=[r for r in paired if r['baseline']==base]
        se=np.sqrt(sum(r['paired_mcse']**2 for r in rr))/len(rr)
        text+=f"- Versus {base}: mean label difference {np.mean([r['mean_difference'] for r in rr]):+.4f}, conditional MCSE {se:.4f}; {sum(r['mean_difference']<0 for r in rr)} improved / {sum(r['mean_difference']==0 for r in rr)} tied / {sum(r['mean_difference']>0 for r in rr)} worse cells.\n"
    text+='\n## Proven findings\n\n'
    text+='The exact-rational binary implementation has 95% anytime joint coverage and thus familywise coverage of every requested sign, under predictable system selection and fresh uniform sampling within its remaining items. PPR processes are supermartingales at support boundaries; the proof does not incorrectly demand equality of conditional expectation there. The PEAK-style adaptation uses the predictable remaining null mean and is proved separately. See THEORY.md. No finite-grid guarantee for arbitrary continuous MT scores is claimed.\n\n'
    text+='For an N-item reference-star population with reference scores all one and L all-zero leaves, compatible-completion certificates require at least N+L labels. Reference-first acquisition attains this bound. With N=4/6/8 and L=2 it costs at most 6/8/10 versus Stage 22 costs 9/12/15 for its unchanged certificate and specified within-item order. These are restricted, exact separations; they are not lower bounds over all 95%-valid procedures. Existing joint controls attain the same upper bound.\n\n'
    text+='## Novelty and unresolved limitations\n\n'
    text+='Joint adaptive-stream testing (PEAK), products of arm martingales (Kaufmann/Koolen), and finite-pool PPR inference already cover the key construction. Fixed hedging, shared caching, projection and a reference-first schedule do not establish a genuinely new method. Correlation is not borrowed to infer unseen coordinates. The prototype is binary-only, exponential in system count, and the reference-first policy may oversample an unhelpful anchor. See RELATED_WORK.md and failure cells.\n\n'
    text+='A literal post-observation-remaining-mean substitution in the cited Ryu/Wornell categorical WoR expression fails a two-item check; this expression was excluded from matched-validity comparisons pending source/implementation clarification. This does not refute the authors\' general vector-gambling framework or establish our superiority over its full algorithms. The experiment does not establish dominance over every strongest existing Joint-CS implementation.\n\n'
    text+='## Recommendation\n\nDo not start WMT or an ICML submission from this construction. A GO would require a tractable continuous-score partial-cell certificate with an instance-dependent improvement that survives existing joint/stream controls, or a genuine computational/lower-bound separation. That theoretical gap remains open. No additional synthetic tuning is justified by the present evidence.\n'
    (OUT/'ASSESSMENT.md').write_text(text,encoding='utf-8')
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    families=sorted({matrix.split('_',1)[1] for matrix,graph in cells})
    for ax,n in zip(axes,(4,8)):
        for j,method in enumerate(methods):
            means=[np.mean([r['mean_labels'] for r in summary if r['matrix']==str(n)+'_'+family and r['method']==method]) for family in families]
            ax.bar(np.arange(len(families))+j*.13,means,width=.13,label=method)
        ax.set_xticks(np.arange(len(families))+.325,families,rotation=30,ha='right');ax.set(title=f'3 systems x {n} items',ylabel='Mean unique labels')
    axes[-1].legend(fontsize=6);fig.tight_layout();fig.savefig(OUT/'costs.png',dpi=160);plt.close(fig)
    print(text)


if __name__=='__main__':main()
