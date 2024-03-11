from math import ceil
import os
import json
import pandas as pd
import seaborn as sns

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
output_dir = './plots'
os.makedirs(output_dir, exist_ok=True)
# Step 1: Read the CSV file into a DataFrame
df = pd.read_csv('100000_data.csv')

x_label = [ceil(1/0.05), ceil(1/0.04545), ceil(1/0.0416), ceil(1/0.0385), ceil(1/0.036), ceil(1/0.033), ceil(1/0.03123), ceil(1/0.029), ceil(1/0.028), ceil(1/0.026), ceil(1/0.025)]

def parms_parser(parms):
    bp_parms_dt = json.loads(parms.replace("\'", "\"")) # 雙引號才能轉換
    name = '/'.join([f'{k}{v}' for k,v  in bp_parms_dt.items()])
    return name

df['bp_parms'] = df['bp_parameter'].apply(parms_parser)
for i in df['bp_parms'].unique():
    x = df[df['bp_parms']==i]
    x_arrival = x['arrival_rate'].to_list()
    y_sjf = x['SJF/FCFS'].to_list()
    y_rr = x['RR/FCFS'].to_list()
    y_mlfq = x['MLFQ/FCFS'].tolist()
    y_setf = x['SETF/FCFS'].tolist()
    y_rmlfq = x['RMLFQ/FCFS'].tolist()
    y_prmlfq = x ['PRMLFQ/FCFS'].tolist()
    y_srpt = x['SPRT/FCFS'].tolist()
    plt.clf()
    plt.figure(figsize=(30,20))  # Adjust the figure size as needed
    plt.axhline(y=1, color='r', linestyle='--', label='Y=1')
    plt.plot(x_label, y_sjf,'-o',label='SJF/FCFS')
    plt.plot(x_label, y_rr,'->',label='RR/FCFS')
    plt.plot(x_label, y_mlfq,'-v',label='MLFQ/FCFS')
    plt.plot(x_label, y_setf,'-+',label='SETF/FCFS')
    plt.plot(x_label, y_rmlfq,'-^',label="RMLFQ/FCFS")
    plt.plot(x_label,y_prmlfq,'-*',label='RMLFQ/FCFS')
    plt.plot(x_label, y_srpt,'-d',label="SRPT/FCFS")

    # Add labels and legend
    plt.xticks(x_label,rotation=35, fontsize='14')
    plt.xlabel('arrival_rate', font={'size': 18})
    plt.ylabel('Compare', font={'size': 18})
    plt.legend()
    plt.title(f"bp parameter experimental results({i}) compare with average flow time with FCFS", font={'size': 18, 'weight': 'bold'})
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(1.0))  # Major ticks every 1 unit
    plt.gca().xaxis.set_minor_locator(ticker.MultipleLocator(0.5))  # Minor ticks every 0.5 unit
    # # Optionally, customize the title and save the figure
    img_name = i.replace("/","_") + "_result_with_FCFS.jpg"
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, img_name), bbox_inches="tight")
    plt.close()
    
arithmetic_ls = ['SJF/FCFS', 'RR/FCFS', 'MLFQ/FCFS', 'SETF/FCFS', 'SPRT/FCFS','RMLFQ/FCFS','PRMLFQ/FCFS']
df_melt = df.melt(id_vars=['bp_parms', 'arrival_rate'], value_vars=arithmetic_ls, var_name='arithmetic', value_name='value')
tmp = df_melt['bp_parms'].str.split('/', expand=True)
tmp.columns = ['L', 'H']
tmp['L'] = tmp['L'].str[1:].astype(float)
tmp['H'] = tmp['H'].str[1:].astype(float)
df_melt = tmp.join(df_melt)
df_melt.to_csv("avg_flow_time_compare_with_fcfs.csv",index=False)


