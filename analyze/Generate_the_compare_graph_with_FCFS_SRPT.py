from math import ceil
import os
import json
import pandas as pd
import seaborn as sns

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
output_dir = './img'
os.makedirs(output_dir, exist_ok=True)
# Step 1: Read the CSV file into a DataFrame
df = pd.read_csv('analyze/100000_data.csv')
x_label = [i for i in range(20, 41, 2)]
def parms_parser(parms):
    bp_parms_dt = json.loads(parms.replace("\'", "\"")) # 雙引號才能轉換
    name = '/'.join([f'{k}{v}' for k,v  in bp_parms_dt.items()])
    return name

df['bp_parms'] = df['bp_parameter'].apply(parms_parser)

for i in df['bp_parms'].unique():
    x = df[df['bp_parms']==i]
    x_arrival = x['arrival_rate'].to_list()
    
    y_srpt = x['RMLFQ_L2_Norm/SRPT_L2_Norm'].to_list()
    y_fcfs = x['RMLFQ_L2_Norm/FCFS_L2_Norm'].tolist()
    y_rr   = x['Rmlfq_L2_Norm/RR_L2_Norm'].tolist()
    plt.clf()
    plt.figure(figsize=(30,20))  # Adjust the figure size as needed
    plt.axhline(y=1, color='r', linestyle='--', label='Y=1')
    plt.plot(x_label, y_srpt,'-v',label='RMLFQ_L2_Norm/SRPT_L2_Normm')
    plt.plot(x_label, y_fcfs,'-^',label="RMLFQ_L2_Norm/FCFS_L2_Norm")
    plt.plot(x_label,y_rr,'-d',label='RMLFQ_L2_Norm/RR_L2_Norm')

    # Add labels and legend
    plt.xticks(x_label, rotation=35, fontsize='14')
    plt.xlabel('inter arrival rate', font={'size': 18})
    plt.ylabel('Compare', font={'size': 18})
    plt.legend()
    plt.title(f"bp parameter experimental results({i}) and compare FCFS with SRPT and Round-Ronbin L2-Norm", font={'size': 18, 'weight': 'bold'})
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(1.0))  # Major ticks every 1 unit
    plt.gca().xaxis.set_minor_locator(ticker.MultipleLocator(0.5))  # Minor ticks every 0.5 unit
    plt.grid(True)
    # # Optionally, customize the title and save the figure
    img_name = i.replace("/","_") + "_l2_norm_compare_fcfs_srpt.pdf"
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, img_name), bbox_inches="tight")
    plt.close()
