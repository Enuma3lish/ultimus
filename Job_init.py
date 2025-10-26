import numpy as np
import scipy.stats as stats
import tqdm
import Write_csv
import math
import os
import random

# Define inter-arrival times
inter_arrival_time = [i for i in range(20, 41, 2)]

# Bounded Pareto parameters
bp_parameter_60 = [
    {"L": 56.300, "H": pow(2, 6), "type": "BP"},
    {"L": 18.900, "H": pow(2, 9), "type": "BP"},
    {"L": 12.400, "H": pow(2, 12), "type": "BP"},
    {"L": 9.800, "H": pow(2, 15), "type": "BP"},
    {"L": 8.500, "H": pow(2, 18), "type": "BP"}
]
bp_parameter_90 = [
    {"L": 32.300, "H": pow(2, 9), "type": "BP"},
    {"L": 19.700, "H": pow(2, 12), "type": "BP"},
    {"L": 15.300, "H": pow(2, 15), "type": "BP"},
    {"L": 13.000, "H": pow(2, 18), "type": "BP"}
]
bp_parameter_30 = [
    {"L": 16.772, "H": pow(2, 6), "type": "BP"},
    {"L": 7.918, "H": pow(2, 9), "type": "BP"},
    {"L": 5.649, "H": pow(2, 12), "type": "BP"},
    {"L": 4.639, "H": pow(2, 15), "type": "BP"},
    {"L": 4.073, "H": pow(2, 18), "type": "BP"}
]

# Normal distribution parameters
# Calibrated for more even distribution with lower variance
# Each set maintains average job size of 30, 60, or 90 with tight control
# Using std = mean * 0.2 for ~95% of values within ±40% of mean

# Average 30: Very even distribution around 30
normal_parameter_30 = [
    {"mean": 30, "std": 6, "type": "Normal"},      # Tight: 18-42 (95% range)
    {"mean": 30, "std": 9, "type": "Normal"},      # Medium: 12-48
    {"mean": 30, "std": 12, "type": "Normal"}      # Wider: 6-54
]

# Average 60: Very even distribution around 60
normal_parameter_60 = [
    {"mean": 60, "std": 12, "type": "Normal"},     # Tight: 36-84 (95% range)
    {"mean": 60, "std": 18, "type": "Normal"},     # Medium: 24-96
    {"mean": 60, "std": 24, "type": "Normal"}      # Wider: 12-108
]

# Average 90: Very even distribution around 90
normal_parameter_90 = [
    {"mean": 90, "std": 18, "type": "Normal"},     # Tight: 54-126 (95% range)
    {"mean": 90, "std": 27, "type": "Normal"},     # Medium: 36-144
    {"mean": 90, "std": 36, "type": "Normal"}      # Wider: 18-162
]

# Create parameter sets - now including both BP and Normal
parameter_sets = {
    "avg_30": bp_parameter_30 + normal_parameter_30,
    "avg_60": bp_parameter_60 + normal_parameter_60,
    "avg_90": bp_parameter_90 + normal_parameter_90
}

# For normal distribution only cases
normal_parameter_sets = {
    "avg_30": normal_parameter_30,
    "avg_60": normal_parameter_60,
    "avg_90": normal_parameter_90
}

def generate_bounded_pareto(alpha, xmin, xmax, size=1):
    """Generate bounded Pareto distributed random values."""
    cdf_xmin = 1 - (xmin / xmax) ** alpha
    u = np.random.uniform(0, cdf_xmin, size=size)
    x = xmin / ((1 - u) ** (1 / alpha))
    return x

def generate_normal_job_size(mean, std, size=1):
    """
    Generate job sizes from normal distribution.
    Ensures positive values and rounds to integers.
    Uses truncation at 1 to avoid negative or zero job sizes.
    """
    samples = np.random.normal(mean, std, size=size)
    # Ensure all values are positive (minimum job size = 1)
    samples = np.maximum(samples, 1)
    return samples

def generate_job_size(param, size=1):
    """
    Generate job size based on parameter type.
    
    Parameters:
    param (dict): Parameter dictionary with 'type' key
    size (int): Number of samples to generate
    """
    if param["type"] == "BP":
        return generate_bounded_pareto(1.1, param["L"], param["H"], size=size)
    elif param["type"] == "Normal":
        return generate_normal_job_size(param["mean"], param["std"], size=size)
    else:
        raise ValueError(f"Unknown parameter type: {param['type']}")

def job_init(num_jobs, avg_inter_arrival_time, param):
    """
    Create jobs with either bounded Pareto or Normal distribution.
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    avg_inter_arrival_time (float): Average inter-arrival time
    param (dict): Parameter dictionary with distribution info
    """
    samples = []
    
    # Generate job sizes based on distribution type
    job_sizes = [math.ceil(size) for size in generate_job_size(param, size=num_jobs)]
    
    # Generate integer arrival times
    current_time = 0
    arrival_times = []
    for _ in range(num_jobs):
        inter_arrival = round(np.random.exponential(scale=avg_inter_arrival_time))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        arrival_times.append(current_time)
    
    # Create job list
    for k in range(num_jobs):
        samples.append({"arrival_time": arrival_times[k], "job_size": job_sizes[k]})
    return samples

def random_job_init(num_jobs, coherence_time=1):
    """
    Create jobs with randomly selected parameters (BP or Normal) with equal probability.
    All parameters across all families have equal probability of selection.
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): Time units after which parameters may change
    """
    samples = []
    
    # Collect all parameters from all families (BP + Normal)
    all_parameters = []
    for param_set in parameter_sets.values():
        all_parameters.extend(param_set)
    
    # Now each parameter (whether BP or Normal) has equal probability: 1/len(all_parameters)
    
    # Initialize with random parameter and inter-arrival time
    current_param = random.choice(all_parameters)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    current_time = 0
    last_change_time = 0
    
    # Generate jobs one by one
    for _ in range(num_jobs):
        if current_time - last_change_time >= coherence_time:
            current_param = random.choice(all_parameters)
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time
        
        # Generate job size based on current parameter type
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])
        
        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        samples.append({"arrival_time": current_time, "job_size": job_size})
    
    return samples

def soft_random_job_init(num_jobs, coherence_time=1):
    """
    Create jobs with soft randomness - smooth transitions within a chosen family.
    The family (avg_30, avg_60, avg_90) is chosen once at the start and contains
    both BP and Normal parameters. Transitions happen within this mixed family.
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): Time units after which parameters may change
    """
    samples = []
    param_set_keys = list(parameter_sets.keys())
    
    # Step 1: Choose family (which now contains both BP and Normal)
    current_param_set_key = random.choice(param_set_keys)
    current_param_set = parameter_sets[current_param_set_key]
    
    # Step 2: Start with random parameter within the family
    current_param_index = random.randint(0, len(current_param_set) - 1)
    
    # Step 3: Initialize inter-arrival time
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    
    current_time = 0
    last_change_time = 0
    
    # Generate jobs
    for _ in range(num_jobs):
        if current_time - last_change_time >= coherence_time:
            num_params = len(current_param_set)
            
            # Apply transition rules (same as before)
            if current_param_index == 0:
                if random.random() < 0.5:
                    current_param_index = 1
            elif current_param_index == num_params - 1:
                if random.random() < 0.5:
                    current_param_index = num_params - 2
            else:
                choice = random.random()
                if choice < 1/3:
                    pass
                elif choice < 2/3:
                    current_param_index -= 1
                else:
                    current_param_index += 1
            
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time
        
        # Get current parameter (could be BP or Normal)
        current_param = current_param_set[current_param_index]
        
        # Generate job size based on parameter type
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])
        
        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        samples.append({"arrival_time": current_time, "job_size": job_size})
    
    return samples

def Save_file(num_jobs, i):
    """Save all job files including normal distribution cases."""
    os.makedirs("data", exist_ok=True)
    
    coherence_times = [pow(2, j) for j in range(1, 17, 1)]
    for ct in coherence_times:
        freq_folder = f"data/freq_{ct}_{i}"
        os.makedirs(freq_folder, exist_ok=True)
    
    # Process parameter sets (now including both BP and Normal)
    for param_name, param_set in parameter_sets.items():
        param_folder = f"data/{param_name}_{i}"
        os.makedirs(param_folder, exist_ok=True)
        
        for avg_inter_arrival in inter_arrival_time:
            for param in tqdm.tqdm(param_set, desc=f"Processing {param_name}_{i}, inter_arrival={avg_inter_arrival}"):
                job_list = job_init(num_jobs, avg_inter_arrival, param)
                
                # Create filename based on parameter type
                if param["type"] == "BP":
                    bl = param["L"]
                    bh = param["H"]
                    filename = f"{param_folder}/({avg_inter_arrival}, {bl}_{bh}).csv"
                elif param["type"] == "Normal":
                    mean = param["mean"]
                    std = param["std"]
                    filename = f"{param_folder}/({avg_inter_arrival}, Normal_{mean}_{std}).csv"
                
                Write_csv.Write_raw(filename, job_list)
    
    # Generate random jobs (with both BP and Normal)
    for ct in tqdm.tqdm(coherence_times, desc=f"Processing random jobs _{i}"):
        job_list = random_job_init(num_jobs, coherence_time=ct)
        filename = f"data/freq_{ct}_{i}/random_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)
    
    # Generate soft random jobs (with both BP and Normal)
    softrandom_base = f"data/softrandom_{i}"
    os.makedirs(softrandom_base, exist_ok=True)
    
    for ct in tqdm.tqdm(coherence_times, desc=f"Processing soft random jobs _{i}"):
        softrandom_folder = f"{softrandom_base}/freq_{ct}_{i}"
        os.makedirs(softrandom_folder, exist_ok=True)
        
        job_list = soft_random_job_init(num_jobs, coherence_time=ct)
        filename = f"{softrandom_folder}/softrandom_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)

if __name__ == "__main__":
    for i in range(1, 11):
        Save_file(10000, i)