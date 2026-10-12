"""Scientific figures for the fixed diagnostic; no role in inference or tuning."""
import numpy as np

def make_figures(comparison,summary_lookup,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    pairs=('en-de','he-en','zh-en');scenarios=('aligned','permuted_history','reversed_history')
    methods=['legacy_trust201','prediction_count_grid','reserve_mix75']
    labels=['Legacy trust','Prediction','Reserve 75%']
    if 'stage6_active10_mean_queries' in comparison[0]:methods.append('stage6_active10');labels.append('Extra queries')
    all_values=[r[m+'_percent_change'] for r in comparison for m in methods]
    margin=max(3.,.12*(max(all_values)-min(all_values)))
    ymin,ymax=min(-2.,min(all_values)-margin),max(2.,max(all_values)+margin)
    fig,axes=plt.subplots(3,3,figsize=(11,8),sharey=True)
    colors=['#8ba4bf','#418bc1','#204b77','#bd7a52']
    for i,scenario in enumerate(scenarios):
        for j,pair in enumerate(pairs):
            row=next(r for r in comparison if r['scenario']==scenario and r['language_pair']==pair)
            ax=axes[i,j];ys=[row[m+'_percent_change'] for m in methods]
            ax.bar(np.arange(len(methods)),ys,color=colors[:len(methods)])
            ax.axhline(0,color='#222',linewidth=.8)
            ax.set_xticks(np.arange(len(methods)),labels,rotation=30,ha='right',fontsize=8)
            ax.set_ylim(ymin,ymax);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
            ax.set_title(f"{scenario.replace('_history','').replace('_',' ')} | {pair} | N={row['n']}",fontsize=10)
            for x,v in enumerate(ys):
                ax.text(x,v+(.5 if v>=0 else -.5),f'{v:+.1f}%',ha='center',va='bottom' if v>=0 else 'top',fontsize=8)
            if j==0:ax.set_ylabel('Query change (%)')
    fig.suptitle('Stage 7: unchanged Stage 5 inference vs Stage 6 extra queries\nMean query change versus raw 95%; displayed methods have nominal 95% anytime coverage',fontsize=13)
    fig.tight_layout(rect=(0,0,1,.93));fig.savefig(output/'prediction_vs_acquisition.png',dpi=180);plt.close(fig)

    weights=np.array([50,75,90]);fig,axes=plt.subplots(1,3,figsize=(10.5,3.8),sharey=True)
    values=[]
    for pair in pairs:
        baseline=summary_lookup[('aligned',pair,'published_ppr95')]['mean_queries']
        for suffix in weights:
            for prefix in ('reserve_mix','ppr_reserve'):
                values.append(100*(summary_lookup[('aligned',pair,prefix+str(suffix))]['mean_queries']/baseline-1))
    margin=max(2.,.1*(max(values)-min(values)))
    for ax,pair in zip(axes,pairs):
        baseline=summary_lookup[('aligned',pair,'published_ppr95')]['mean_queries']
        for prefix,color,label,style in [('reserve_mix','#204b77','Mixture: 95%','-'),('ppr_reserve','#ad8653','Stricter raw control','--')]:
            ys=[100*(summary_lookup[('aligned',pair,prefix+str(s))]['mean_queries']/baseline-1) for s in weights]
            ax.plot(weights,ys,style+'o',color=color,label=label)
        ax.axhline(0,color='#555',linewidth=.8);ax.axvline(75,color='#888',alpha=.35,linewidth=.8)
        ax.set_title(pair);ax.set_xticks(weights);ax.set_xlabel('Raw-capital reserve (%)')
        ax.set_ylim(min(values)-margin,max(values)+margin);ax.grid(alpha=.15)
    axes[0].set_ylabel('Mean query change vs raw 95% (%)');axes[0].legend(frameon=False,fontsize=8)
    fig.suptitle('Aligned histories: fixed-weight diagnostics; 75% remains primary',fontsize=12)
    fig.text(.5,.02,'Raw controls: 97.5%, 96.25%, 95.5% confidence at reserves 50%, 75%, 90%, respectively.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.08,1,.91));fig.savefig(output/'reserve_tradeoff.png',dpi=180);plt.close(fig)
