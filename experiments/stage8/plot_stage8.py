"""Static scientific comparison of matched history and zero-trust pipelines."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from stage8_common import read_csv, SCENARIOS


def plot(directory):
    directory = Path(directory)
    rows = read_csv(directory / 'comparison.csv')
    lookup = {(r['scenario'], r['language_pair'], r['family']): r for r in rows}
    pairs = ('en-de', 'he-en', 'zh-en')
    figure, axes = plt.subplots(3, 3, figsize=(12, 9), sharex=True)
    colors = ('#7795a9', '#264e70', '#d9ac69', '#95672d')
    for i, scenario in enumerate(SCENARIOS):
        for j, pair in enumerate(pairs):
            ax = axes[i, j]
            values = []
            for family in ('standalone', 'reserve75'):
                row = lookup[(scenario, pair, family)]
                values.extend([float(row['model_free_change_percent_vs_raw95']), float(row['total_prediction_change_percent_vs_raw95'])])
            ax.bar(np.arange(4), values, color=colors, width=.7)
            ax.axhline(0, color='#444444', linewidth=.8)
            ax.set_title(f"{scenario.replace('_history', '').capitalize()} / {pair}", fontsize=10)
            ax.grid(axis='y', alpha=.18)
            ax.set_axisbelow(True)
            if j == 0:
                ax.set_ylabel('Query change (%)')
            ax.set_xticks(np.arange(4), ['Zero\nstandalone', 'History\nstandalone', 'Zero\nreserve75', 'History\nreserve75'], fontsize=8)
    figure.suptitle('Stage 8: matched historical-prediction ablation\nChange versus raw PPR 95%; negative values mean fewer labels', fontsize=13)
    figure.tight_layout(rect=(0, 0, 1, .94), h_pad=2.1, w_pad=1.8)
    figure.savefig(directory / 'matched_controls.png', dpi=180)
    plt.close(figure)
