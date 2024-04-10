import numpy as np
import scipy.stats as stats
import tqdm
import Write_csv
import math
Arrival_rate = [i for i in range(20, 41, 2)]
#Arrival_rate=[0.05,0.04545,0.0416,0.0385,0.036,0.033,0.03123,0.029,0.028,0.026,0.025] #problem for loop 
bp_parameter=[{"L":16.772,"H":pow(2,6)},{"L":7.918,"H":pow(2,9)},{"L":5.649,"H":pow(2,12)},{"L":4.639,"H":pow(2,15)},{"L":4.073,"H":pow(2,18)}]   
def job_init(num_jobs,arrival_rate,xmin,xmax):
    alpha =1.1
    samples = []
    jb=[]
    pareto = stats.pareto(b=alpha) #bounded pareto
    while len(jb) < num_jobs:
        raw_sample = math.ceil(pareto.rvs(size=1)[0])
        if xmin <= raw_sample <= xmax:
            jb.append(raw_sample)
    arrival_times = np.random.poisson(arrival_rate, num_jobs).cumsum()  #put iterarrival time
    for k in range(len(jb)):
        samples.append({"arrival_time":arrival_times[k],"job_size":jb[k]})
    return samples

def Save_file(num_jobs):
    for a in Arrival_rate:
        for b in tqdm.tqdm(bp_parameter):
            #put bp_paremeter in avg_job_flow because each turn
            job_list =job_init(num_jobs,a,b["L"],b["H"])
            bl = b["L"]
            Write_csv.Write_raw(f"/home/melowu/Work/expri/data/{a,bl}.csv",job_list)
Save_file(100)