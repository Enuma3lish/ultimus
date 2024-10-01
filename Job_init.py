import numpy as np
import scipy.stats as stats
import tqdm
import Write_csv
import math

# Define inter-arrival times
inter_arrival_time = [i for i in range(20, 41, 2)]  # This defines average inter-arrival times

# Bounded Pareto parameters
bp_parameter = [
    {"L": 16.772, "H": pow(2, 6)},
    {"L": 7.918, "H": pow(2, 9)},
    {"L": 5.649, "H": pow(2, 12)},
    {"L": 4.639, "H": pow(2, 15)},
    {"L": 4.073, "H": pow(2, 18)}
]

def job_init(num_jobs, avg_inter_arrival_time, xmin, xmax):
    alpha = 1.1
    samples = []
    jb = []
    pareto = stats.pareto(b=alpha)  # Bounded Pareto distribution
    # Generate job sizes within [xmin, xmax]
    while len(jb) < num_jobs:
        raw_sample = math.ceil(pareto.rvs(size=1)[0])
        if xmin <= raw_sample <= xmax:
            jb.append(raw_sample)
    # Generate inter-arrival times from exponential distribution
    inter_arrival_times = np.random.exponential(scale=avg_inter_arrival_time, size=num_jobs)
    # Compute arrival times as cumulative sum of inter-arrival times
    arrival_times = np.cumsum(inter_arrival_times)
    # Create job list with arrival times and job sizes
    for k in range(len(jb)):
        samples.append({"arrival_time": arrival_times[k], "job_size": jb[k]})
    return samples

def Save_file(num_jobs):
    for avg_inter_arrival in inter_arrival_time:
        for b in tqdm.tqdm(bp_parameter):
            job_list = job_init(num_jobs, avg_inter_arrival, b["L"], b["H"])
            bl = b["L"]
            # Format the filename as (inter_arrival, bl).csv
            filename = f"/home/melowu/Work/ultimus/data/({avg_inter_arrival}, {bl}).csv"
            Write_csv.Write_raw(filename, job_list)

Save_file(100000)