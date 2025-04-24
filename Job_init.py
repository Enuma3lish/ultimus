import numpy as np
import scipy.stats as stats
import tqdm
import Write_csv
import math
import os
import random
import multiprocessing as mp
from functools import partial
import sys

# For macOS, ensure proper multiprocessing setup
if sys.platform == 'darwin':
    try:
        mp.set_start_method('fork', force=True)
    except RuntimeError:
        # If already set, ignore the error
        pass

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
    coherence_time (int): Number of consecutive jobs that use the same parameter pair
                         Values: 1, 10, 100, 500, 1000, 10000
    """
    samples = []
    jb = []
    arrival_times = []
    alpha = 1.1
    pareto = stats.pareto(b=alpha)
    
    all_parameters = bp_parameter_30 + bp_parameter_60 + bp_parameter_90
    
    # Generate job sizes by randomly selecting parameter sets
    # but maintain coherence for 'coherence_time' consecutive jobs
    current_param = None
    param_jobs_count = 0
    
    job_count = 0
    # Generate integer arrival times first
    current_time = 0
    while job_count < num_jobs:
        # Generate inter-arrival time and round to nearest integer
        inter_arrival = round(np.random.exponential(scale=avg_inter_arrival_time))
        # Ensure inter-arrival time is at least 1
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        arrival_times.append(current_time)
        job_count += 1
    
    # Now generate job sizes with proper coherence
    job_count = 0
    while job_count < num_jobs:
        # Check if we need to select a new parameter set based on coherence time
        if current_param is None or param_jobs_count >= coherence_time:
            current_param = random.choice(all_parameters)
            param_jobs_count = 0
        
        xmin, xmax = current_param["L"], current_param["H"]
        
        raw_sample = math.ceil(pareto.rvs(size=1)[0])
        if xmin <= raw_sample <= xmax:
            jb.append(raw_sample)
            param_jobs_count += 1
            job_count += 1
    
    # Create job list with arrival times and job sizes
    for k in range(len(jb)):
        samples.append({"arrival_time": arrival_times[k], "job_size": jb[k]})
    return samples

def soft_random_job_init(num_jobs, avg_inter_arrival_time, coherence_time=1):
    """
    Create jobs with soft randomness: 50% chance to keep the same parameter set
    (avg_30, avg_60, or avg_90) but different specific parameters within that set.
    Also follows the coherence time pattern.
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    avg_inter_arrival_time (float): Average inter-arrival time
    coherence_time (int): Number of consecutive jobs that use the same parameter set family
                         Values: 1, 10, 100, 500, 1000, 10000
    """
    samples = []
    jb = []
    arrival_times = []
    alpha = 1.1
    pareto = stats.pareto(b=alpha)
    
    # Parameter set tracking variables
    param_set_keys = list(parameter_sets.keys())  # ["avg_30", "avg_60", "avg_90"]
    current_param_set_key = None
    current_param = None
    param_set_jobs_count = 0
    
    # Generate integer arrival times first
    current_time = 0
    job_count = 0
    while job_count < num_jobs:
        # Generate inter-arrival time and round to nearest integer
        inter_arrival = round(np.random.exponential(scale=avg_inter_arrival_time))
        # Ensure inter-arrival time is at least 1
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        arrival_times.append(current_time)
        job_count += 1
    
    # Now generate job sizes with proper coherence
    job_count = 0
    while job_count < num_jobs:
        # Check if we need to select a new parameter set based on coherence time
        if current_param_set_key is None or param_set_jobs_count >= coherence_time:
            # Choose whether to keep the same parameter set family with 50% probability
            # (but only if we already have a parameter set and this isn't the first selection)
            if current_param_set_key is not None and random.random() < 0.5:
                # Keep the same parameter set family
                pass
            else:
                # Choose a new parameter set family
                current_param_set_key = random.choice(param_set_keys)
            
            # Reset the coherence counter
            param_set_jobs_count = 0
            
            # Always choose a new specific parameter from the current set
            current_param = random.choice(parameter_sets[current_param_set_key])
        
        xmin, xmax = current_param["L"], current_param["H"]
        
        raw_sample = math.ceil(pareto.rvs(size=1)[0])
        if xmin <= raw_sample <= xmax:
            jb.append(raw_sample)
            param_set_jobs_count += 1
            job_count += 1
    
    # Create job list with arrival times and job sizes
    for k in range(len(jb)):
        samples.append({"arrival_time": arrival_times[k], "job_size": jb[k]})
    return samples

def process_normal_job(param_name, param_info, avg_inter_arrival, num_jobs):
    """Process and save a single job with normal parameters"""
    b, output_dir = param_info
    job_list = job_init(num_jobs, avg_inter_arrival, b["L"], b["H"])
    bl = b["L"]
    # Format the filename as (inter_arrival, bl).csv
    filename = f"{output_dir}/({avg_inter_arrival}, {bl}).csv"
    Write_csv.Write_raw(filename, job_list)
    return f"Completed {filename}"

def process_random_job(coherence_time, avg_inter_arrival, num_jobs, is_soft=False):
    """Process and save a single job with random parameters"""
    if is_soft:
        base_dir = "data/softrandom"
        job_list = soft_random_job_init(num_jobs, avg_inter_arrival, coherence_time=coherence_time)
    else:
        base_dir = "data"
        job_list = random_job_init(num_jobs, avg_inter_arrival, coherence_time=coherence_time)
    
    output_dir = f"{base_dir}/freq_{coherence_time}"
    filename = f"{output_dir}/({avg_inter_arrival}).csv"
    Write_csv.Write_raw(filename, job_list)
    return f"Completed {filename}"

def Save_file(num_jobs):
    # Create base data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Create frequency/coherence time folders
    coherence_times = [1, 10, 100, 500, 1000, 10000]
    for ct in coherence_times:
        freq_folder = f"data/freq_{ct}"
        os.makedirs(freq_folder, exist_ok=True)
    
    # Create a pool with CPU count - 1 processes (to keep one CPU free)
    num_processes = max(1, mp.cpu_count() - 1)
    print(f"Using {num_processes} processes for parallel execution")
    
    # Create a multiprocessing pool
    with mp.Pool(processes=num_processes) as pool:
        # Create tasks for normal parameter sets (30, 60, 90)
        normal_tasks = []
        for param_name, param_set in parameter_sets.items():
            # Create folder for this parameter set
            output_dir = f"data/{param_name}"
            os.makedirs(output_dir, exist_ok=True)
            
            for avg_inter_arrival in inter_arrival_time:
                for b in param_set:
                    normal_tasks.append((param_name, (b, output_dir), avg_inter_arrival, num_jobs))
        
        # Process normal tasks with multiprocessing
        print(f"Processing {len(normal_tasks)} normal parameter jobs")
        results = list(tqdm.tqdm(
            pool.starmap(process_normal_job, normal_tasks),
            total=len(normal_tasks),
            desc="Processing normal parameter jobs"
        ))
        
        # Create tasks for random parameter jobs
        random_tasks = []
        for ct in coherence_times:
            for avg_inter_arrival in inter_arrival_time:
                random_tasks.append((ct, avg_inter_arrival, num_jobs, False))  # False means not soft random
        
        # Process random tasks with multiprocessing
        print(f"Processing {len(random_tasks)} random parameter jobs")
        results = list(tqdm.tqdm(
            pool.starmap(process_random_job, random_tasks),
            total=len(random_tasks),
            desc="Processing random parameter jobs"
        ))
        
        # Create soft random folder and generate soft random job lists for each coherence time
        os.makedirs("data/softrandom", exist_ok=True)
        
        # Create coherence time subfolders within softrandom
        for ct in coherence_times:
            softrandom_folder = f"data/softrandom/freq_{ct}"
            os.makedirs(softrandom_folder, exist_ok=True)
        
        # Create tasks for soft random parameter jobs
        soft_random_tasks = []
        for ct in coherence_times:
            for avg_inter_arrival in inter_arrival_time:
                soft_random_tasks.append((ct, avg_inter_arrival, num_jobs, True))  # True means soft random
        
        # Process soft random tasks with multiprocessing
        print(f"Processing {len(soft_random_tasks)} soft random parameter jobs")
        results = list(tqdm.tqdm(
            pool.starmap(process_random_job, soft_random_tasks),
            total=len(soft_random_tasks),
            desc="Processing soft random parameter jobs"
        ))

if __name__ == "__main__":
    mp.freeze_support()  # Support for frozen executables
    Save_file(10000)