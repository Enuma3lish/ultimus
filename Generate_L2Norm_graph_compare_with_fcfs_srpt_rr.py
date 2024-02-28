import os
import pandas as pd
import matplotlib.pyplot as plt

import seaborn as sns
sns.set_theme(style="white")

def draw(path, output_folder, ncol=3):
    df = pd.read_csv(path)
    df['value'] = df['value']
    df['arrival_rate'] = 1/df['arrival_rate'].astype(float)


    plot_gp = df['arithmetic'].unique()

    f, axes = plt.subplots(nrows=len(plot_gp)//ncol, ncols=ncol,  figsize=(12,5))
    for pid, gp in enumerate(plot_gp):
        df_filter = df[df['arithmetic'] ==  gp]
        axes[pid].title.set_text(gp)
        sns.lineplot(
                data=df_filter, x="arrival_rate", y="value", hue="bp_parms", style="bp_parms", markers=True,
                estimator=None, color=".7", linewidth=1, ax=axes[pid]
        )

    plt.savefig(os.path.join(output_folder, path.split('.')[0] + '.value.pdf'))



output_folder = 'img2'
os.makedirs(output_folder, exist_ok=True)

source_name = 'l2norm_compare_with_srpt_fcfs_rr.csv'

draw(source_name, output_folder)