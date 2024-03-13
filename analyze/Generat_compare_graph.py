import os
import json
import pandas as pd
import seaborn as sns

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
output_dir = './plots'
os.makedirs(output_dir, exist_ok=True)
# Step 1: Read the CSV file into a DataFrame
df = pd.read_csv('analyze/100000_data.csv')
x_label = [i for i in range(20, 41, 2)]
#x_label = [ceil(1/0.05), ceil(1/0.04545), ceil(1/0.0416), ceil(1/0.0385), ceil(1/0.036), ceil(1/0.033), ceil(1/0.03123), ceil(1/0.029), ceil(1/0.028), ceil(1/0.026), ceil(1/0.025)]

def parms_parser(parms):
    bp_parms_dt = json.loads(parms.replace("\'", "\"")) # 雙引號才能轉換
    name = '/'.join([f'{k}{v}' for k,v  in bp_parms_dt.items()])
    return name

df['bp_parms'] = df['bp_parameter'].apply(parms_parser)
for i in df['bp_parms'].unique():
    x = df[df['bp_parms']==i]
    x_arrival = x['arrival_rate'].to_list()
    y_comp = x['Rmlfq_L2_Norm/Rmlfq_Dy_L2_norm'].to_list()
    plt.clf()
    plt.figure(figsize=(30,20))  # Adjust the figure size as needed
    plt.axhline(y=1, color='r', linestyle='--', label='Y=1')
    plt.plot(x_label,y_comp,'-^',label='Rmlfq_L2_Norm/Rmlfq_Dy_L2_norm')

    # Add labels and legend
    plt.xticks(x_label,rotation=35, fontsize='14')
    plt.xlabel('arrival_rate', font={'size': 18})
    plt.ylabel('Compare', font={'size': 18})
    plt.legend()
    plt.title(f"bp parameter experimental results({i}) compare with two customize algorithm", font={'size': 18, 'weight': 'bold'})
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(1.0))  # Major ticks every 1 unit
    plt.gca().xaxis.set_minor_locator(ticker.MultipleLocator(0.5))  # Minor ticks every 0.5 unit
    # # Optionally, customize the title and save the figure
    img_name = i.replace("/","_") + "_result_with_comp.pdf"
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, img_name), bbox_inches="tight")
    plt.close()
    