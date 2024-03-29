import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import seaborn as sns
sns.set_theme(style="white")


output_folder = 'img'
os.makedirs(output_folder, exist_ok=True)
def draw(source_name):
    df = pd.read_csv(source_name)
    df['compare'] = df['value']
    df['inter arrival rate'] = df['arrival_rate'].astype(float)
    for gp in df['arithmetic'].unique():
        df_filter = df[df['arithmetic'] ==  gp]
        plt.cla()
        plt.clf()
        plt.title(gp)
        sns.lineplot(
            data=df_filter, x="inter arrival rate", y="value", hue="bp_parms", style="bp_parms", markers=True,
            estimator=None, color=".7", linewidth=1
        )
        plt.savefig(os.path.join(output_folder, gp.replace('/', '-') + '.value.pdf'))
        plt.close()
