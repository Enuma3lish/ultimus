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
def parms_parser(parms):
    bp_parms_dt = json.loads(parms.replace("\'", "\"")) # 雙引號才能轉換
    name = '/'.join([f'{k}{v}' for k,v  in bp_parms_dt.items()])
    return name

df['bp_parms'] = df['bp_parameter'].apply(parms_parser)
for i in df['bp_parms'].unique():
    x = df[df['bp_parms']==i]
    x_arrival = x['arrival_rate'].to_list()
    y_sjf = x['SJF/SRPT'].to_list()
    y_rr = x['RR/SRPT'].to_list()
    y_mlfq = x['MLFQ/SRPT'].tolist()
    y_prmlfq = x ['PRMLFQ/SRPT'].tolist()
    y_setf = x['SETF/SRPT'].tolist()
    y_rmlfq = x['RMLFQ/SRPT'].tolist()
    y_rmlfq_dy = x['RMLFQ_Dy/SRPT'].tolist()
    y_fcfs = x['FCFS/SRPT'].tolist()
    plt.clf()
    plt.figure(figsize=(30,20))  # Adjust the figure size as needed
    plt.axhline(y=1, color='r', linestyle='--', label='Y=1')
    plt.plot(x_label, y_sjf,'-o', label='SJF/SRPT')
    plt.plot(x_label, y_rr,'->', label='RR/SRPT')
    plt.plot(x_label, y_mlfq,'-v', label='MLFQ/SRPT')
    plt.plot(x_label, y_setf,'-+', label='SETF/SRPT')
    plt.plot(x_label, y_rmlfq,'-^',label='RMLFQ/SRPT')
    plt.plot(x_label,y_prmlfq,'-*',label='PRMLFQ/SRPT')
    plt.plot(x_label,y_prmlfq,'-<',label='RMLFQ_Dy/SRPT')
    plt.plot(x_label,y_fcfs,'-d',label='FCFS/SRPT')

    # Add labels and legend
    plt.xticks(x_label,rotation=35, fontsize='14')
    plt.xlabel('inter arrival rate', font={'size': 18})
    plt.ylabel('Compare', font={'size': 18})
    plt.legend()
    plt.title(f"bp parameter experimental results({i}) compare with average flow time with SRPT", font={'size': 18, 'weight': 'bold'})
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(1.0))  # Major ticks every 1 unit
    plt.gca().xaxis.set_minor_locator(ticker.MultipleLocator(0.5))  # Minor ticks every 0.5 unit
    # # Optionally, customize the title and save the figure
    img_name = i.replace("/","_") + "_result_with_SRPT.pdf"
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, img_name), bbox_inches="tight")
    plt.close()
    
arithmetic_ls = ['SJF/SRPT', 'RR/SRPT', 'MLFQ/SRPT', 'SETF/SRPT', 'FCFS/SRPT','RMLFQ/SRPT','PRMLFQ/SRPT','RMLFQ_Dy/SRPT']
df_melt = df.melt(id_vars=['bp_parms', 'arrival_rate'], value_vars=arithmetic_ls, var_name='arithmetic', value_name='value')
tmp = df_melt['bp_parms'].str.split('/', expand=True)
tmp.columns = ['L', 'H']
tmp['L'] = tmp['L'].str[1:].astype(float)
tmp['H'] = tmp['H'].str[1:].astype(float)
df_melt = tmp.join(df_melt)
df_melt.to_csv("avg_flow_time_compare_with_srpt.csv",index=False)