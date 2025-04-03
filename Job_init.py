import numpy as np
import scipy.stats as stats
import tqdm
import Write_csv
import math
import os
import random

# Define inter-arrival times
inter_arrival_time = [i for i in range(20, 41, 2)]  # This defines average inter-arrival times

bp_parameter_60 = [
    {"L": 56.300, "H": pow(2, 6)},
    {"L": 18.900, "H": pow(2, 9)},
    {"L": 12.400, "H": pow(2, 12)},
    {"L": 9.800, "H": pow(2, 15)},
    {"L": 8.500, "H": pow(2, 18)}
]
bp_parameter_90 = [
    {"L": 32.300, "H": pow(2, 9)},
    {"L": 19.700, "H": pow(2, 12)},
    {"L": 15.300, "H": pow(2, 15)},
    {"L": 13.000, "H": pow(2, 18)}
]
bp_parameter_30 = [
    {"L": 16.772, "H": pow(2, 6)},
    {"L": 7.918, "H": pow(2, 9)},
    {"L": 5.649, "H": pow(2, 12)},
    {"L": 4.639, "H": pow(2, 15)},
    {"L": 4.073, "H": pow(2, 18)}
]

# Create a dictionary mapping parameter sets to their names
parameter_sets = {
    "avg_30": bp_parameter_30,
    "avg_60": bp_parameter_60,
    "avg_90": bp_parameter_90
}

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
    
    # Generate integer arrival times
    current_time = 0
    arrival_times = []
    for _ in range(num_jobs):
        # Generate inter-arrival time and round to nearest integer
        inter_arrival = round(np.random.exponential(scale=avg_inter_arrival_time))
        # Ensure inter-arrival time is at least 1
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        arrival_times.append(current_time)
    
    # Create job list with arrival times and job sizes
    for k in range(len(jb)):
        samples.append({"arrival_time": arrival_times[k], "job_size": jb[k]})
    return samples

def random_job_init(num_jobs, avg_inter_arrival_time, coherence_time=1):
    """
    Create jobs with randomly selected parameters from 30, 60, or 90 sets
    according to the specified coherence time.
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    avg_inter_arrival_time (float): Average inter-arrival time
    coherence_time (int): Number of consecutive jobs that use the same parameter set
                         Values: 1, 10, 100, 500, 1000, 10000
    """
    samples = []
    jb = []
    alpha = 1.1
    pareto = stats.pareto(b=alpha)
    
    all_parameters = bp_parameter_30 + bp_parameter_60 + bp_parameter_90
    
    # Generate job sizes by randomly selecting parameter sets
    # but maintain coherence for 'coherence_time' consecutive jobs
    current_param = None
    param_jobs_count = 0
    
    while len(jb) < num_jobs:
        # Check if we need to select a new parameter set based on coherence time
        if current_param is None or param_jobs_count >= coherence_time:
            current_param = random.choice(all_parameters)
            param_jobs_count = 0
        
        xmin, xmax = current_param["L"], current_param["H"]
        
        raw_sample = math.ceil(pareto.rvs(size=1)[0])
        if xmin <= raw_sample <= xmax:
            jb.append(raw_sample)
            param_jobs_count += 1
    
    # Generate integer arrival times
    current_time = 0
    arrival_times = []
    for _ in range(num_jobs):
        # Generate inter-arrival time and round to nearest integer
        inter_arrival = round(np.random.exponential(scale=avg_inter_arrival_time))
        # Ensure inter-arrival time is at least 1
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        arrival_times.append(current_time)
    
    # Create job list with arrival times and job sizes
    for k in range(len(jb)):
        samples.append({"arrival_time": arrival_times[k], "job_size": jb[k]})
    return samples

def Save_file(num_jobs):
    # Create base data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Create frequency/coherence time folders
    coherence_times = [1, 10, 100, 500, 1000, 10000]
    for ct in coherence_times:
        freq_folder = f"data/freq_{ct}"
        os.makedirs(freq_folder, exist_ok=True)
    
    # Process normal parameter sets (30, 60, 90)
    for param_name, param_set in parameter_sets.items():
        # Create folder for this parameter set
        os.makedirs(f"data/{param_name}", exist_ok=True)
        
        for avg_inter_arrival in inter_arrival_time:
            for b in tqdm.tqdm(param_set, desc=f"Processing {param_name}, inter_arrival={avg_inter_arrival}"):
                job_list = job_init(num_jobs, avg_inter_arrival, b["L"], b["H"])
                bl = b["L"]
                # Format the filename as (inter_arrival, bl).csv
                filename = f"data/{param_name}/({avg_inter_arrival}, {bl}).csv"
                Write_csv.Write_raw(filename, job_list)
    
    # Create random folder
    os.makedirs("data/random", exist_ok=True)
    
    # Generate and save job lists for each coherence time
    for ct in coherence_times:
        for avg_inter_arrival in inter_arrival_time:
            # Generate job list with random parameters and specified coherence time
            job_list = random_job_init(num_jobs, avg_inter_arrival, coherence_time=ct)
            
            # Save to the frequency-specific folder
            filename = f"data/freq_{ct}/({avg_inter_arrival}).csv"
            Write_csv.Write_raw(filename, job_list)
    
    # Also generate a general random set without coherence for the random folder
    for avg_inter_arrival in inter_arrival_time:
        job_list = random_job_init(num_jobs, avg_inter_arrival, coherence_time=1)
        filename = f"data/random/({avg_inter_arrival}).csv"
        Write_csv.Write_raw(filename, job_list)

if __name__ == "__main__":
    Save_file(10000)