import os
import pandas as pd
import matplotlib.pyplot as plt
from  itertools import combinations 
import seaborn as sns
sns.set_theme(style="white")

def draw(path, output_folder, ncol=1):
    df = pd.read_csv(path)
    df['value'] = df['value']
    df['arrival_rate'] = df['arrival_rate']


    plot_gp = df['arithmetic'].unique()
    plot_gp_list = list(combinations(plot_gp,2))
    f, axes = plt.subplots(nrows=len(plot_gp_list)//ncol, ncols=ncol,  figsize=(9,30))
    palette_list = ["blue", "red"]
    
    for pid, gp in enumerate(plot_gp_list):
        df_filter = df[df['arithmetic'].isin([gp[0],gp[1]])]
        if gp[0] =='RMLFQ_L2_Norm/SRPT_L2_Norm' and gp[1] == 'RMLFQ_L2_Norm/FCFS_L2_Norm' or gp[0] =='RMLFQ_L2_Norm/SRPT_L2_Norm' and gp[1] == 'RMLFQ_L2_Norm/BAL_L2_Norm' :
            axes[pid].title.set_text(gp)
            sns.lineplot(
                data=df_filter, x="arrival_rate", y="value", hue="arithmetic", style="bp_parms",markers=True,
                dashes=False,  # Ensures lines are solid
                palette=palette_list,
                estimator=None, color=".7", linewidth=1,ax=axes[pid]
            )
            axes[pid].legend(loc='upper right')
            axes[pid].set_xlabel("mean inter arrival time")
            axes[pid].set_ylabel("compare")
            plt.tight_layout()
    plt.savefig(os.path.join(output_folder, path.split('.')[0] + '.value.pdf'))

output_folder = 'img2'
os.makedirs(output_folder, exist_ok=True)

source_name = 'l2norm_compare_with_needed.csv'

draw(source_name, output_folder)