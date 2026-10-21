import csv
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'results_reference'
METHODS = ('stage22', 'per_system', 'joint_diagonal', 'joint_covariance', 'joint_adaptive')


def write_csv(name, rows):
    with (OUT/name).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)


def main():
    with (OUT/'trials.csv').open(newline='', encoding='utf-8') as f: rows = list(csv.DictReader(f))
    for row in rows:
        for key in ('cost', 'repeat', 'any_wrong', 'items', 'systems'): row[key] = int(row[key])
        row['fraction'] = float(row['fraction'])
    cell_fields = ('matrix', 'graph', 'history')
    cells = sorted({tuple(r[k] for k in cell_fields) for r in rows})
    summary, comparisons = [], []
    for cell in cells:
        group = [r for r in rows if tuple(r[k] for k in cell_fields)==cell]
        by_method = {method:sorted([r for r in group if r['method']==method], key=lambda r:r['repeat']) for method in METHODS}
        for method, rr in by_method.items():
            summary.append(dict(zip(cell_fields, cell), method=method, mean_labels=float(np.mean([r['cost'] for r in rr])),
                                mean_fraction=float(np.mean([r['fraction'] for r in rr])), any_wrong=sum(r['any_wrong'] for r in rr)))
        for candidate in ('joint_diagonal', 'joint_covariance', 'joint_adaptive'):
            for baseline in ('stage22', 'per_system', 'joint_diagonal'):
                if candidate==baseline: continue
                a = np.array([r['cost'] for r in by_method[candidate]]); b = np.array([r['cost'] for r in by_method[baseline]])
                d = a-b
                comparisons.append(dict(zip(cell_fields, cell), candidate=candidate, baseline=baseline,
                    mean_difference=float(d.mean()), relative_change_percent=float(100*d.mean()/b.mean()),
                    paired_mcse=float(d.std(ddof=1)/np.sqrt(len(d))),
                    wins=int((d<0).sum()), ties=int((d==0).sum()), losses=int((d>0).sum())))
    write_csv('per_cell.csv', summary); write_csv('paired_per_cell.csv', comparisons)
    totals = []
    for method in METHODS:
        rr = [r for r in rows if r['method']==method]
        totals.append(dict(method=method, mean_labels=float(np.mean([r['cost'] for r in rr])),
                           mean_fraction=float(np.mean([r['fraction'] for r in rr])), any_wrong=sum(r['any_wrong'] for r in rr)))
    write_csv('overall.csv', totals)
    families = sorted({r['matrix'].split('_', 1)[1] for r in rows})
    family_rows = []
    for family in families:
        for method in METHODS:
            rr = [r for r in rows if r['matrix'].split('_', 1)[1]==family and r['method']==method]
            family_rows.append(dict(family=family, method=method, mean_labels=float(np.mean([r['cost'] for r in rr]))))
    write_csv('per_family.csv', family_rows)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, shape in zip(axes, ('4x8', '3x24')):
        for j, method in enumerate(METHODS):
            means = [np.mean([r['mean_labels'] for r in summary if r['matrix']==shape+'_'+family and r['method']==method]) for family in families]
            ax.bar(np.arange(len(families))+j*.16, means, width=.16, label=method)
        ax.set_xticks(np.arange(len(families))+.32, families, rotation=25, ha='right')
        ax.set(title=shape, ylabel='Mean unique system-item labels')
    axes[-1].legend(fontsize=7); fig.tight_layout(); fig.savefig(OUT/'costs.png', dpi=160); fig.savefig(OUT/'costs.svg'); plt.close(fig)
    costs = {r['method']:r['mean_labels'] for r in totals}
    text = '# Stage 24 feasibility result\n\n'
    text += '**NO-GO for the tested construction as a novel ICML contribution.** This is not a proof that all joint finite-pool methods fail.\n\n'
    text += '| Method | Mean unique labels | Change vs Stage 22 |\n|---|---:|---:|\n'
    for row in totals:
        text += f"| {row['method']} | {row['mean_labels']:.3f} | {100*(row['mean_labels']/costs['stage22']-1):+.2f}% |\n"
    text += '\nLower is better. These averages equally weight the 60 fixed cells and their 20 paths; uniform-method results repeat across histories and are not extra independent data. See per-shape and per-cell results rather than interpreting the pooled average as population performance.\n\n'
    for candidate in ('joint_covariance', 'joint_adaptive'):
        for baseline in ('stage22', 'per_system', 'joint_diagonal'):
            rr = [r for r in comparisons if r['candidate']==candidate and r['baseline']==baseline]
            text += f"- {candidate} vs {baseline}: {sum(r['mean_difference']<0 for r in rr)} cells improve, {sum(r['mean_difference']==0 for r in rr)} tie, {sum(r['mean_difference']>0 for r in rr)} worsen (history-duplicated cells included).\n"
    verification = json.loads((OUT/'VERIFICATION.json').read_text())
    text += f"\nObserved wrong declarations: {verification['any_wrong']}; joint anytime-coverage failures: {verification['joint_coverage_failures']}. Small synthetic observations do not prove the 95% guarantee. The explicit conditional-expectation proof and exact arithmetic checks are the justification.\n"
    text += '\n## Proven versus empirical versus open\n\n'
    text += '- Proven in THEORY.md: design-unbiased vector correction, valid nonnegative joint wealth, simultaneous all-time pairwise projections at 95%, under positive known predictable inclusion probabilities. The prototype uses conservative arithmetic on the full binary-total grid.\n'
    text += '- Empirical: results above apply to two small binary shapes, four fixed matrix families and the frozen path seeds. They do not establish continuous-score WMT performance or an optimal joint method. The inverse-covariance sign heuristic has no efficiency guarantee.\n'
    text += '- Novelty: the ingredients are direct combinations of existing adaptive finite-pool inverse-probability betting and vector CS inversion. No new theorem/complexity advantage survived this audit. AnyRank is related but targets different i.i.d. outcomes; no surrogate AnyRank benchmark was used.\n'
    text += '- Open: a scalable continuous-score joint method using partially observed cached cells with a provable unique-label efficiency advantage. General partial-cell unbiasedness is proved and tested one step, but only whole-row acquisition is evaluated end-to-end.\n'
    text += '\n## Recommendation\n\nDo not run WMT or prepare an ICML claim from this candidate. The most promising next theoretical question is an instance-dependent efficiency bound for joint adaptive partial-cell inference, compared with existing joint gambling constructions and strong coordinate/pair procedures. Require a concrete separation or useful computational theorem before another benchmark. Avoid further tuning this pilot against the same synthetic fixtures.\n'
    (OUT/'FINDINGS.md').write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__': main()
