import pandas as pd
from math import ceil
import json

x_label = [i for i in range(20, 41, 2)]
def parms_parser(parms):
    bp_parms_dt = json.loads(parms.replace("\'", "\"")) # 雙引號才能轉換
    name = '/'.join([f'{k}{v}' for k,v  in bp_parms_dt.items()])
    return name
df = pd.read_csv('analyze/100000_data.csv')
df['bp_parms'] = df['bp_parameter'].apply(parms_parser)
arithmetic_ls = ['RMLFQ_L2_Norm/SRPT_L2_Norm','RMLFQ_L2_Norm/FCFS_L2_Norm','Rmlfq_L2_Norm/RR_L2_Norm']
df_melt = df.melt(id_vars=['bp_parms', 'arrival_rate'], value_vars=arithmetic_ls, var_name='arithmetic', value_name='value')
tmp = df_melt['bp_parms'].str.split('/', expand=True)
tmp.columns = ['L', 'H']
tmp['L'] = tmp['L'].str[1:].astype(float)
tmp['H'] = tmp['H'].str[1:].astype(float)
df_melt = tmp.join(df_melt)
df_melt.to_csv("l2norm_compare_with_srpt_fcfs_rr.csv",index=False)