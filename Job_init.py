import numpy as np
import scipy.stats as stats
import tqdm
import Write_csv
import math
import os
import random
import pandas as pd
from typing import List, Dict, Tuple

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
    {"mean": 30, "std": 12, "type": "Normal"},     # Wider: 6-54
    {"mean": 30, "std": 15, "type": "Normal"},     # Extra-wide: 0-60
    {"mean": 30, "std": 18, "type": "Normal"}      # Very wide: 0-66
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

# For Bounded Pareto only cases
bp_parameter_sets = {
    "avg_30": bp_parameter_30,
    "avg_60": bp_parameter_60,
    "avg_90": bp_parameter_90
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

def bounded_pareto_random_job_init(num_jobs, coherence_time=1):
    """
    Create jobs with randomly selected Bounded Pareto parameters only from avg_30.

    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): CPU time units after which parameters may change
    """
    samples = []

    # Only use BP parameters from avg_30
    all_bp_parameters = bp_parameter_30

    # Initialize with random parameter and inter-arrival time
    current_param = random.choice(all_bp_parameters)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    current_time = 0
    last_change_time = 0

    # Generate jobs one by one
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time, not job count)
        if current_time - last_change_time >= coherence_time:
            current_param = random.choice(all_bp_parameters)
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time

        # Generate job size using Bounded Pareto
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])

        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        samples.append({"arrival_time": current_time, "job_size": job_size})

    return samples

def normal_random_job_init(num_jobs, coherence_time=1):
    """
    Create jobs with randomly selected Normal distribution parameters only.
    H is set to 'std' for normal distribution.

    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): CPU time units after which parameters may change
    """
    samples = []

    # Collect all Normal parameters from all families
    all_normal_parameters = []
    for param_set in normal_parameter_sets.values():
        all_normal_parameters.extend(param_set)

    # Initialize with random parameter and inter-arrival time
    current_param = random.choice(all_normal_parameters)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    current_time = 0
    last_change_time = 0

    # Generate jobs one by one
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time, not job count)
        if current_time - last_change_time >= coherence_time:
            current_param = random.choice(all_normal_parameters)
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time

        # Generate job size using Normal distribution
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])

        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        samples.append({"arrival_time": current_time, "job_size": job_size})

    return samples

def bounded_pareto_soft_random_job_init(num_jobs, coherence_time=1):
    """
    Create jobs with soft randomness for Bounded Pareto parameters only from avg_30.
    Modified transition rules:
    - If at lowest H: 1/2 stay, 1/2 move up
    - If at highest H: 1/2 stay, 1/2 move down
    - Otherwise: 1/3 stay, 1/3 move up, 1/3 move down

    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): CPU time units after which parameters may change
    """
    samples = []

    # Only use BP parameters from avg_30
    current_param_set = bp_parameter_30

    # Step 2: Start with random parameter within the family
    current_param_index = random.randint(0, len(current_param_set) - 1)

    # Step 3: Initialize inter-arrival time
    current_avg_inter_arrival = random.choice(inter_arrival_time)

    current_time = 0
    last_change_time = 0

    # Generate jobs
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time)
        if current_time - last_change_time >= coherence_time:
            num_params = len(current_param_set)

            # Apply modified transition rules based on H position
            if current_param_index == 0:  # Lowest H
                if random.random() < 0.5:
                    current_param_index = min(1, num_params - 1)  # Move up
                # else: stay
            elif current_param_index == num_params - 1:  # Highest H
                if random.random() < 0.5:
                    current_param_index = max(0, num_params - 2)  # Move down
                # else: stay
            else:  # Middle positions
                choice = random.random()
                if choice < 1/3:
                    pass  # Stay
                elif choice < 2/3:
                    current_param_index -= 1  # Move down
                else:
                    current_param_index += 1  # Move up

            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time

        # Get current parameter (BP only)
        current_param = current_param_set[current_param_index]

        # Generate job size
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])

        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        samples.append({"arrival_time": current_time, "job_size": job_size})

    return samples

def normal_soft_random_job_init(num_jobs, coherence_time=1):
    """
    Create jobs with soft randomness for Normal distribution parameters only.
    H is represented by 'std' (standard deviation).
    Modified transition rules:
    - If at lowest std: 1/2 stay, 1/2 move up
    - If at highest std: 1/2 stay, 1/2 move down
    - Otherwise: 1/3 stay, 1/3 move up, 1/3 move down

    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): CPU time units after which parameters may change
    """
    samples = []
    normal_set_keys = list(normal_parameter_sets.keys())

    # Step 1: Choose family (Normal only)
    current_param_set_key = random.choice(normal_set_keys)
    current_param_set = normal_parameter_sets[current_param_set_key]

    # Step 2: Start with random parameter within the family
    current_param_index = random.randint(0, len(current_param_set) - 1)

    # Step 3: Initialize inter-arrival time
    current_avg_inter_arrival = random.choice(inter_arrival_time)

    current_time = 0
    last_change_time = 0

    # Generate jobs
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time)
        if current_time - last_change_time >= coherence_time:
            num_params = len(current_param_set)

            # Apply modified transition rules based on std position
            if current_param_index == 0:  # Lowest std
                if random.random() < 0.5:
                    current_param_index = min(1, num_params - 1)  # Move up
                # else: stay
            elif current_param_index == num_params - 1:  # Highest std
                if random.random() < 0.5:
                    current_param_index = max(0, num_params - 2)  # Move down
                # else: stay
            else:  # Middle positions
                choice = random.random()
                if choice < 1/3:
                    pass  # Stay
                elif choice < 2/3:
                    current_param_index -= 1  # Move down
                else:
                    current_param_index += 1  # Move up

            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time

        # Get current parameter (Normal only)
        current_param = current_param_set[current_param_index]

        # Generate job size
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])

        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        samples.append({"arrival_time": current_time, "job_size": job_size})

    return samples

def combination_random_job_init(num_jobs, param_set, coherence_time=1):
    """
    Create jobs with random selection from a specific parameter set (2, 3, or 4 combinations).
    Each parameter in the set has equal probability of selection.
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    param_set (list): List of BP parameters to choose from (2, 3, or 4 parameters)
    coherence_time (int): CPU time units after which parameters may change
    """
    samples = []
    
    # Initialize with random parameter from the set and inter-arrival time
    current_param = random.choice(param_set)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    current_time = 0
    last_change_time = 0
    
    # Generate jobs one by one
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time)
        if current_time - last_change_time >= coherence_time:
            current_param = random.choice(param_set)
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time
        
        # Generate job size using Bounded Pareto
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])
        
        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        samples.append({"arrival_time": current_time, "job_size": job_size})
    
    return samples

def combination_softrandom_job_init(num_jobs, param_set, coherence_time=1):
    """
    Create jobs with soft randomness within a specific parameter set (2, 3, or 4 combinations).
    Transitions follow soft random rules within the given set.
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    param_set (list): List of BP parameters to choose from (2, 3, or 4 parameters)
    coherence_time (int): CPU time units after which parameters may change
    """
    samples = []
    
    # Start with random parameter within the set
    current_param_index = random.randint(0, len(param_set) - 1)
    
    # Initialize inter-arrival time
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    
    current_time = 0
    last_change_time = 0
    
    # Generate jobs
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time)
        if current_time - last_change_time >= coherence_time:
            num_params = len(param_set)
            
            # Apply transition rules based on position
            if num_params == 2:
                # For 2 combinations: 1/2 probability to switch
                if random.random() < 0.5:
                    current_param_index = 1 - current_param_index  # Switch between 0 and 1
            else:
                # For 3 or 4 combinations: use standard soft random rules
                if current_param_index == 0:  # Lowest H
                    if random.random() < 0.5:
                        current_param_index = min(1, num_params - 1)  # Move up
                    # else: stay
                elif current_param_index == num_params - 1:  # Highest H
                    if random.random() < 0.5:
                        current_param_index = max(0, num_params - 2)  # Move down
                    # else: stay
                else:  # Middle positions
                    choice = random.random()
                    if choice < 1/3:
                        pass  # Stay
                    elif choice < 2/3:
                        current_param_index -= 1  # Move down
                    else:
                        current_param_index += 1  # Move up
            
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time
        
        # Get current parameter
        current_param = param_set[current_param_index]
        
        # Generate job size
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])
        
        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        samples.append({"arrival_time": current_time, "job_size": job_size})
    
    return samples

def get_combination_folder_name(param_set):
    """
    Generate descriptive folder name based on parameter set.
    For BP: shows H values (e.g., 'H64_H512')
    For Normal: shows std values (e.g., 'std6_std9')
    """
    if param_set[0]["type"] == "BP":
        h_values = [str(int(p["H"])) for p in param_set]
        return "_".join([f"H{h}" for h in h_values])
    elif param_set[0]["type"] == "Normal":
        std_values = [str(int(p["std"])) for p in param_set]
        return "_".join([f"std{s}" for s in std_values])
    return "unknown"

def Save_file(num_jobs, i):
    """Save all job files including normal distribution cases."""
    os.makedirs("data", exist_ok=True)

    coherence_times = [pow(2, j) for j in range(1, 17, 1)]

    # # Process parameter sets (now including both BP and Normal)
    # for param_name, param_set in parameter_sets.items():
    #     param_folder = f"data/{param_name}_{i}"
    #     os.makedirs(param_folder, exist_ok=True)

    #     for avg_inter_arrival in inter_arrival_time:
    #         for param in tqdm.tqdm(param_set, desc=f"Processing {param_name}_{i}, inter_arrival={avg_inter_arrival}"):
    #             job_list = job_init(num_jobs, avg_inter_arrival, param)

    #             # Create filename based on parameter type
    #             if param["type"] == "BP":
    #                 bl = param["L"]
    #                 bh = param["H"]
    #                 filename = f"{param_folder}/({avg_inter_arrival}, {bl}_{bh}).csv"
    #             elif param["type"] == "Normal":
    #                 mean = param["mean"]
    #                 std = param["std"]
    #                 filename = f"{param_folder}/({avg_inter_arrival}, Normal_{mean}_{std}).csv"

    #             Write_csv.Write_raw(filename, job_list)

    # Generate Bounded_Pareto random jobs
    for ct in tqdm.tqdm(coherence_times, desc=f"Processing Bounded_Pareto random jobs _{i}"):
        bp_random_folder = f"data/Bounded_Pareto_random_{i}/freq_{ct}_{i}"
        os.makedirs(bp_random_folder, exist_ok=True)

        job_list = bounded_pareto_random_job_init(num_jobs, coherence_time=ct)
        filename = f"{bp_random_folder}/Bounded_Pareto_random_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)

    # Generate normal random jobs
    for ct in tqdm.tqdm(coherence_times, desc=f"Processing normal random jobs _{i}"):
        normal_random_folder = f"data/normal_random_{i}/freq_{ct}_{i}"
        os.makedirs(normal_random_folder, exist_ok=True)

        job_list = normal_random_job_init(num_jobs, coherence_time=ct)
        filename = f"{normal_random_folder}/normal_random_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)

    # Generate Bounded_Pareto soft random jobs
    bp_softrandom_base = f"data/Bounded_Pareto_softrandom_{i}"
    os.makedirs(bp_softrandom_base, exist_ok=True)

    for ct in tqdm.tqdm(coherence_times, desc=f"Processing Bounded_Pareto soft random jobs _{i}"):
        bp_softrandom_folder = f"{bp_softrandom_base}/freq_{ct}_{i}"
        os.makedirs(bp_softrandom_folder, exist_ok=True)

        job_list = bounded_pareto_soft_random_job_init(num_jobs, coherence_time=ct)
        filename = f"{bp_softrandom_folder}/Bounded_Pareto_softrandom_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)

    # Generate normal soft random jobs
    normal_softrandom_base = f"data/normal_softrandom_{i}"
    os.makedirs(normal_softrandom_base, exist_ok=True)

    for ct in tqdm.tqdm(coherence_times, desc=f"Processing normal soft random jobs _{i}"):
        normal_softrandom_folder = f"{normal_softrandom_base}/freq_{ct}_{i}"
        os.makedirs(normal_softrandom_folder, exist_ok=True)

        job_list = normal_soft_random_job_init(num_jobs, coherence_time=ct)
        filename = f"{normal_softrandom_folder}/normal_softrandom_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)

    # ==================== EXPERIMENTS ====================

    # Experiment 1: Fixed arrival rate, vary coherence_time
    exp1_base = f"data/experiment1_fixed_arrival_{i}"
    os.makedirs(exp1_base, exist_ok=True)

    for ct in tqdm.tqdm(coherence_times, desc=f"Processing Experiment 1 (fixed arrival) _{i}"):
        exp1_folder = f"{exp1_base}/freq_{ct}_{i}"
        os.makedirs(exp1_folder, exist_ok=True)

        job_list = experiment1_fixed_arrival_vary_coherence(num_jobs, fixed_inter_arrival=30, coherence_time=ct)
        filename = f"{exp1_folder}/exp1_fixed_arrival_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)

    # Experiment 2: Fixed job size, vary coherence_time
    # Test with different fixed parameters
    exp2_base = f"data/experiment2_fixed_jobsize_{i}"
    os.makedirs(exp2_base, exist_ok=True)

    for param_idx in range(len(bp_parameter_30)):
        param = bp_parameter_30[param_idx]
        param_folder = f"{exp2_base}/param_L{param['L']:.3f}_H{int(param['H'])}"
        os.makedirs(param_folder, exist_ok=True)

        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Experiment 2 (param {param_idx}) _{i}"):
            exp2_freq_folder = f"{param_folder}/freq_{ct}_{i}"
            os.makedirs(exp2_freq_folder, exist_ok=True)

            job_list = experiment2_fixed_jobsize_vary_coherence(num_jobs, fixed_param_index=param_idx, coherence_time=ct)
            filename = f"{exp2_freq_folder}/exp2_fixed_jobsize_param{param_idx}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)

    # Experiment 3: Record parameter switches
    exp3_base = f"data/experiment3_record_switches_{i}"
    os.makedirs(exp3_base, exist_ok=True)

    for ct in tqdm.tqdm(coherence_times, desc=f"Processing Experiment 3 (record switches) _{i}"):
        exp3_folder = f"{exp3_base}/freq_{ct}_{i}"
        os.makedirs(exp3_folder, exist_ok=True)

        job_list, switch_history = experiment3_record_switches(num_jobs, coherence_time=ct)

        # Save job list
        job_filename = f"{exp3_folder}/exp3_jobs_freq_{ct}.csv"
        Write_csv.Write_raw(job_filename, job_list)

        # Save switch history
        switch_filename = f"{exp3_folder}/exp3_switches_freq_{ct}.csv"
        if switch_history:
            import pandas as pd
            df_switches = pd.DataFrame(switch_history)
            df_switches.to_csv(switch_filename, index=False)

    # Experiment 4: Fixed inter-arrival = 20 (Overload: ρ=1.5)
    exp4_base = f"data/experiment4_fixed_arrival_20_{i}"
    os.makedirs(exp4_base, exist_ok=True)

    for ct in tqdm.tqdm(coherence_times, desc=f"Processing Experiment 4 (arrival=20) _{i}"):
        exp4_folder = f"{exp4_base}/freq_{ct}_{i}"
        os.makedirs(exp4_folder, exist_ok=True)

        job_list = experiment4_fixed_interarrival_20(num_jobs, coherence_time=ct)
        filename = f"{exp4_folder}/exp4_fixed_arrival20_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)

    # Experiment 5: Fixed inter-arrival = 30 (Balanced: ρ=1.0)
    exp5_base = f"data/experiment5_fixed_arrival_30_{i}"
    os.makedirs(exp5_base, exist_ok=True)

    for ct in tqdm.tqdm(coherence_times, desc=f"Processing Experiment 5 (arrival=30) _{i}"):
        exp5_folder = f"{exp5_base}/freq_{ct}_{i}"
        os.makedirs(exp5_folder, exist_ok=True)

        job_list = experiment5_fixed_interarrival_30(num_jobs, coherence_time=ct)
        filename = f"{exp5_folder}/exp5_fixed_arrival30_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)

    # Experiment 6: Fixed inter-arrival = 40 (Stable: ρ=0.75)
    exp6_base = f"data/experiment6_fixed_arrival_40_{i}"
    os.makedirs(exp6_base, exist_ok=True)

    for ct in tqdm.tqdm(coherence_times, desc=f"Processing Experiment 6 (arrival=40) _{i}"):
        exp6_folder = f"{exp6_base}/freq_{ct}_{i}"
        os.makedirs(exp6_folder, exist_ok=True)

        job_list = experiment6_fixed_interarrival_40(num_jobs, coherence_time=ct)
        filename = f"{exp6_folder}/exp6_fixed_arrival40_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)

    # Define combination sets from avg_30 BP parameters (sequential pairs, triplets, quadruplets)
    # Bounded Pareto combinations
    bp_two_combinations = [
        [bp_parameter_30[0], bp_parameter_30[1]],  # L=16.772 H=2^6, L=7.918 H=2^9
        [bp_parameter_30[1], bp_parameter_30[2]],  # L=7.918 H=2^9, L=5.649 H=2^12
        [bp_parameter_30[2], bp_parameter_30[3]],  # L=5.649 H=2^12, L=4.639 H=2^15
        [bp_parameter_30[3], bp_parameter_30[4]]   # L=4.639 H=2^15, L=4.073 H=2^18
    ]
    
    bp_three_combinations = [
        [bp_parameter_30[0], bp_parameter_30[1], bp_parameter_30[2]],  # indices 0,1,2
        [bp_parameter_30[1], bp_parameter_30[2], bp_parameter_30[3]],  # indices 1,2,3
        [bp_parameter_30[2], bp_parameter_30[3], bp_parameter_30[4]]   # indices 2,3,4
    ]
    
    bp_four_combinations = [
        [bp_parameter_30[0], bp_parameter_30[1], bp_parameter_30[2], bp_parameter_30[3]],  # indices 0,1,2,3
        [bp_parameter_30[1], bp_parameter_30[2], bp_parameter_30[3], bp_parameter_30[4]]   # indices 1,2,3,4
    ]
    
    # Normal distribution combinations from avg_30
    normal_two_combinations = [
        [normal_parameter_30[0], normal_parameter_30[1]],  # std=6, std=9
        [normal_parameter_30[1], normal_parameter_30[2]],  # std=9, std=12
        [normal_parameter_30[2], normal_parameter_30[3]],  # std=12, std=15
        [normal_parameter_30[3], normal_parameter_30[4]]   # std=15, std=18
    ]
    
    normal_three_combinations = [
        [normal_parameter_30[0], normal_parameter_30[1], normal_parameter_30[2]],  # indices 0,1,2
        [normal_parameter_30[1], normal_parameter_30[2], normal_parameter_30[3]],  # indices 1,2,3
        [normal_parameter_30[2], normal_parameter_30[3], normal_parameter_30[4]]   # indices 2,3,4
    ]
    
    normal_four_combinations = [
        [normal_parameter_30[0], normal_parameter_30[1], normal_parameter_30[2], normal_parameter_30[3]],  # indices 0,1,2,3
        [normal_parameter_30[1], normal_parameter_30[2], normal_parameter_30[3], normal_parameter_30[4]]   # indices 1,2,3,4
    ]
    
    # Generate Bounded Pareto combination_random jobs
    bp_combination_random_base = f"data/Bounded_Pareto_combination_random_{i}"
    os.makedirs(bp_combination_random_base, exist_ok=True)
    
    # BP Two-combination random
    for idx, param_set in enumerate(bp_two_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_two_comb_random_folder = f"{bp_combination_random_base}/two_combination_{combo_name}"
        os.makedirs(bp_two_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP two_combination_random {combo_name} _{i}"):
            freq_folder = f"{bp_two_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/pair_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)
    
    # BP Three-combination random
    for idx, param_set in enumerate(bp_three_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_three_comb_random_folder = f"{bp_combination_random_base}/three_combination_{combo_name}"
        os.makedirs(bp_three_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP three_combination_random {combo_name} _{i}"):
            freq_folder = f"{bp_three_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/triplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)
    
    # BP Four-combination random
    for idx, param_set in enumerate(bp_four_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_four_comb_random_folder = f"{bp_combination_random_base}/four_combination_{combo_name}"
        os.makedirs(bp_four_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP four_combination_random {combo_name} _{i}"):
            freq_folder = f"{bp_four_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/quadruplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)
    
    # Generate Normal combination_random jobs
    normal_combination_random_base = f"data/normal_combination_random_{i}"
    os.makedirs(normal_combination_random_base, exist_ok=True)
    
    # Normal Two-combination random
    for idx, param_set in enumerate(normal_two_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_two_comb_random_folder = f"{normal_combination_random_base}/two_combination_{combo_name}"
        os.makedirs(normal_two_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal two_combination_random {combo_name} _{i}"):
            freq_folder = f"{normal_two_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/pair_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)
    
    # Normal Three-combination random
    for idx, param_set in enumerate(normal_three_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_three_comb_random_folder = f"{normal_combination_random_base}/three_combination_{combo_name}"
        os.makedirs(normal_three_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal three_combination_random {combo_name} _{i}"):
            freq_folder = f"{normal_three_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/triplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)
    
    # Normal Four-combination random
    for idx, param_set in enumerate(normal_four_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_four_comb_random_folder = f"{normal_combination_random_base}/four_combination_{combo_name}"
        os.makedirs(normal_four_comb_random_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal four_combination_random {combo_name} _{i}"):
            freq_folder = f"{normal_four_comb_random_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_random_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/quadruplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)
    
    # Generate Bounded Pareto combination_softrandom jobs
    bp_combination_softrandom_base = f"data/Bounded_Pareto_combination_softrandom_{i}"
    os.makedirs(bp_combination_softrandom_base, exist_ok=True)
    
    # BP Two-combination softrandom
    for idx, param_set in enumerate(bp_two_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_two_comb_softrandom_folder = f"{bp_combination_softrandom_base}/two_combination_{combo_name}"
        os.makedirs(bp_two_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP two_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{bp_two_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/pair_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)
    
    # BP Three-combination softrandom
    for idx, param_set in enumerate(bp_three_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_three_comb_softrandom_folder = f"{bp_combination_softrandom_base}/three_combination_{combo_name}"
        os.makedirs(bp_three_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP three_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{bp_three_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/triplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)
    
    # BP Four-combination softrandom
    for idx, param_set in enumerate(bp_four_combinations):
        combo_name = get_combination_folder_name(param_set)
        bp_four_comb_softrandom_folder = f"{bp_combination_softrandom_base}/four_combination_{combo_name}"
        os.makedirs(bp_four_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing BP four_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{bp_four_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/quadruplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)
    
    # Generate Normal combination_softrandom jobs
    normal_combination_softrandom_base = f"data/normal_combination_softrandom_{i}"
    os.makedirs(normal_combination_softrandom_base, exist_ok=True)
    
    # Normal Two-combination softrandom
    for idx, param_set in enumerate(normal_two_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_two_comb_softrandom_folder = f"{normal_combination_softrandom_base}/two_combination_{combo_name}"
        os.makedirs(normal_two_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal two_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{normal_two_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/pair_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)
    
    # Normal Three-combination softrandom
    for idx, param_set in enumerate(normal_three_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_three_comb_softrandom_folder = f"{normal_combination_softrandom_base}/three_combination_{combo_name}"
        os.makedirs(normal_three_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal three_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{normal_three_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/triplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)
    
    # Normal Four-combination softrandom
    for idx, param_set in enumerate(normal_four_combinations):
        combo_name = get_combination_folder_name(param_set)
        normal_four_comb_softrandom_folder = f"{normal_combination_softrandom_base}/four_combination_{combo_name}"
        os.makedirs(normal_four_comb_softrandom_folder, exist_ok=True)
        
        for ct in tqdm.tqdm(coherence_times, desc=f"Processing Normal four_combination_softrandom {combo_name} _{i}"):
            freq_folder = f"{normal_four_comb_softrandom_folder}/freq_{ct}_{i}"
            os.makedirs(freq_folder, exist_ok=True)
            
            job_list = combination_softrandom_job_init(num_jobs, param_set, coherence_time=ct)
            filename = f"{freq_folder}/quadruplet_{idx+1}_freq_{ct}.csv"
            Write_csv.Write_raw(filename, job_list)

def experiment1_fixed_arrival_vary_coherence(num_jobs, fixed_inter_arrival=30, coherence_time=1):
    """
    實驗1：固定到達率，改變coherence_time

    只改變工作大小參數，到達率保持固定

    Parameters:
    num_jobs (int): Number of jobs to generate
    fixed_inter_arrival (float): Fixed inter-arrival time (default=30)
    coherence_time (int): Time units after which job size parameters may change

    Returns:
    list: Job list with fixed arrival rate
    """
    samples = []

    # Use only BP parameters from avg_30
    all_bp_parameters = bp_parameter_30

    # Initialize with random parameter but FIXED inter-arrival
    current_param = random.choice(all_bp_parameters)
    current_time = 0
    last_change_time = 0

    # Generate jobs one by one
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time)
        if current_time - last_change_time >= coherence_time:
            # Only change job size parameter, NOT arrival rate
            current_param = random.choice(all_bp_parameters)
            last_change_time = current_time

        # Generate job size
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])

        # Generate arrival time with FIXED inter-arrival
        inter_arrival = round(np.random.exponential(scale=fixed_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        samples.append({
            "arrival_time": current_time,
            "job_size": job_size
        })

    return samples

def experiment2_fixed_jobsize_vary_coherence(num_jobs, fixed_param_index=0, coherence_time=1):
    """
    實驗2：固定工作大小，改變coherence_time

    只改變到達率，工作大小參數保持固定

    Parameters:
    num_jobs (int): Number of jobs to generate
    fixed_param_index (int): Index of fixed parameter in bp_parameter_30 (0-4, default=0)
    coherence_time (int): Time units after which arrival rate may change

    Returns:
    list: Job list with fixed job size parameter
    """
    samples = []

    # Use a fixed BP parameter
    fixed_param = bp_parameter_30[fixed_param_index]

    # Initialize with random inter-arrival time
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    current_time = 0
    last_change_time = 0

    # Generate jobs one by one
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time)
        if current_time - last_change_time >= coherence_time:
            # Only change arrival rate, NOT job size parameter
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time

        # Generate job size with FIXED parameter
        job_size = math.ceil(generate_job_size(fixed_param, size=1)[0])

        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        samples.append({
            "arrival_time": current_time,
            "job_size": job_size
        })

    return samples

def experiment3_record_switches(num_jobs, coherence_time=1):
    """
    實驗3：記錄參數切換歷史

    在生成數據時記錄每次參數切換的詳細信息

    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): Time units after which parameters may change

    Returns:
    tuple: (job_list, switch_history)
        - job_list: List of jobs with arrival_time and job_size
        - switch_history: List of parameter switches with detailed info
    """
    samples = []
    switch_history = []

    # Use BP parameters from avg_30
    all_bp_parameters = bp_parameter_30

    # Initialize with random parameter and inter-arrival time
    current_param = random.choice(all_bp_parameters)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    current_time = 0
    last_change_time = 0

    # Record initial parameters
    switch_history.append({
        "switch_time": 0,
        "job_index": 0,
        "old_param_L": None,
        "old_param_H": None,
        "new_param_L": current_param["L"],
        "new_param_H": current_param["H"],
        "old_inter_arrival": None,
        "new_inter_arrival": current_avg_inter_arrival,
        "old_load": None,
        "new_load": 30.0 / current_avg_inter_arrival,  # Approximate load
        "duration_since_last_switch": 0
    })

    # Generate jobs one by one
    for job_idx in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time)
        if current_time - last_change_time >= coherence_time:
            # Record old parameters
            old_param = current_param
            old_inter_arrival = current_avg_inter_arrival
            old_load = 30.0 / old_inter_arrival

            # Change parameters
            current_param = random.choice(all_bp_parameters)
            current_avg_inter_arrival = random.choice(inter_arrival_time)

            # Calculate new load
            new_load = 30.0 / current_avg_inter_arrival

            # Record switch
            switch_history.append({
                "switch_time": current_time,
                "job_index": job_idx,
                "old_param_L": old_param["L"],
                "old_param_H": old_param["H"],
                "new_param_L": current_param["L"],
                "new_param_H": current_param["H"],
                "old_inter_arrival": old_inter_arrival,
                "new_inter_arrival": current_avg_inter_arrival,
                "old_load": old_load,
                "new_load": new_load,
                "duration_since_last_switch": current_time - last_change_time
            })

            last_change_time = current_time

        # Generate job size
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])

        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        samples.append({
            "arrival_time": current_time,
            "job_size": job_size,
            "param_L": current_param["L"],
            "param_H": current_param["H"],
            "inter_arrival_setting": current_avg_inter_arrival
        })

    return samples, switch_history

def experiment4_fixed_interarrival_20(num_jobs, coherence_time=1):
    """
    Experiment 4: Fixed inter-arrival time = 20 (Overload: ρ=1.5)

    Job size parameters switch between BP and Normal from avg_30.
    This creates an overload scenario since E[job_size]=30 and inter_arrival=20.

    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): Time units after which job size parameters may change

    Returns:
    list: Job list with fixed arrival rate = 20
    """
    samples = []

    # Combine BP and Normal parameters from avg_30
    all_parameters = bp_parameter_30 + normal_parameter_30

    # Initialize with random parameter but FIXED inter-arrival = 20
    current_param = random.choice(all_parameters)
    current_time = 0
    last_change_time = 0

    # Generate jobs one by one
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time)
        if current_time - last_change_time >= coherence_time:
            # Only change job size parameter, NOT arrival rate
            current_param = random.choice(all_parameters)
            last_change_time = current_time

        # Generate job size (can be BP or Normal)
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])

        # Generate arrival time with FIXED inter-arrival = 20
        inter_arrival = round(np.random.exponential(scale=20))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        samples.append({
            "arrival_time": current_time,
            "job_size": job_size
        })

    return samples

def experiment5_fixed_interarrival_30(num_jobs, coherence_time=1):
    """
    Experiment 5: Fixed inter-arrival time = 30 (Balanced: ρ=1.0)

    Job size parameters switch between BP and Normal from avg_30.
    This creates a critical load scenario since E[job_size]=30 and inter_arrival=30.

    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): Time units after which job size parameters may change

    Returns:
    list: Job list with fixed arrival rate = 30
    """
    samples = []

    # Combine BP and Normal parameters from avg_30
    all_parameters = bp_parameter_30 + normal_parameter_30

    # Initialize with random parameter but FIXED inter-arrival = 30
    current_param = random.choice(all_parameters)
    current_time = 0
    last_change_time = 0

    # Generate jobs one by one
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time)
        if current_time - last_change_time >= coherence_time:
            # Only change job size parameter, NOT arrival rate
            current_param = random.choice(all_parameters)
            last_change_time = current_time

        # Generate job size (can be BP or Normal)
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])

        # Generate arrival time with FIXED inter-arrival = 30
        inter_arrival = round(np.random.exponential(scale=30))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        samples.append({
            "arrival_time": current_time,
            "job_size": job_size
        })

    return samples

def experiment6_fixed_interarrival_40(num_jobs, coherence_time=1):
    """
    Experiment 6: Fixed inter-arrival time = 40 (Stable: ρ=0.75)

    Job size parameters switch between BP and Normal from avg_30.
    This creates a stable load scenario since E[job_size]=30 and inter_arrival=40.

    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): Time units after which job size parameters may change

    Returns:
    list: Job list with fixed arrival rate = 40
    """
    samples = []

    # Combine BP and Normal parameters from avg_30
    all_parameters = bp_parameter_30 + normal_parameter_30

    # Initialize with random parameter but FIXED inter-arrival = 40
    current_param = random.choice(all_parameters)
    current_time = 0
    last_change_time = 0

    # Generate jobs one by one
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time)
        if current_time - last_change_time >= coherence_time:
            # Only change job size parameter, NOT arrival rate
            current_param = random.choice(all_parameters)
            last_change_time = current_time

        # Generate job size (can be BP or Normal)
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])

        # Generate arrival time with FIXED inter-arrival = 40
        inter_arrival = round(np.random.exponential(scale=40))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        samples.append({
            "arrival_time": current_time,
            "job_size": job_size
        })

    return samples

def combination_fixed_arrival_job_init(num_jobs, param_set, fixed_inter_arrival, coherence_time=1):
    """
    Create jobs with FIXED inter-arrival time but RANDOM parameter switching.
    Similar to combination_random_job_init but with fixed arrival rate.

    Parameters:
    num_jobs (int): Number of jobs to generate
    param_set (list): List of parameters to choose from (2, 3, or 4 parameters)
    fixed_inter_arrival (int): Fixed mean inter-arrival time (20, 30, or 40)
    coherence_time (int): CPU time units after which parameters may change

    Returns:
    list: Job list with fixed arrival rate but random parameter switching
    """
    samples = []

    # Initialize with random parameter from the set
    current_param = random.choice(param_set)
    current_time = 0
    last_change_time = 0

    # Generate jobs one by one
    for _ in range(num_jobs):
        # Check if coherence_time has passed (based on CPU time)
        if current_time - last_change_time >= coherence_time:
            current_param = random.choice(param_set)  # Switch parameter
            last_change_time = current_time

        # Generate job size using current parameter
        job_size = math.ceil(generate_job_size(current_param, size=1)[0])

        # Generate arrival time with FIXED inter-arrival
        inter_arrival = round(np.random.exponential(scale=fixed_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival

        samples.append({"arrival_time": current_time, "job_size": job_size})

    return samples


def Save_fix_combination_files(num_jobs, num_replications=10):
    """
    Generate and save fixed arrival combination data (like Bounded_Pareto_combination).

    Creates folder structure:
    data/
      fix20_combination_1/
        two_combination_H64_H512/
          freq_2_1/
            pair_1_freq_2.csv
        three_combination_H64_H512_H4096/
          freq_2_1/
            triplet_1_freq_2.csv
        four_combination_H512_H4096_H32768_H262144/
          freq_2_1/
            quadruplet_1_freq_2.csv
      fix20_combination_2/
        ...
      fix30_combination_1/
        ...
      fix40_combination_1/
        ...

    Parameters:
    num_jobs (int): Number of jobs to generate per file
    num_replications (int): Number of replications for each fixed arrival time
    """
    # Fixed inter-arrival times: 20, 30, 40
    fixed_arrivals = {
        "fix20": 20,  # ρ = 30/20 = 1.5 (overload)
        "fix30": 30,  # ρ = 30/30 = 1.0 (critical)
        "fix40": 40   # ρ = 30/40 = 0.75 (stable)
    }

    # Use only BP parameters for combinations
    bp_params = bp_parameter_30

    # Define all combinations (matching existing structure)
    # Two combinations
    two_combinations = []
    for i in range(len(bp_params)):
        for j in range(i + 1, len(bp_params)):
            two_combinations.append([bp_params[i], bp_params[j]])

    # Three combinations
    three_combinations = []
    for i in range(len(bp_params)):
        for j in range(i + 1, len(bp_params)):
            for k in range(j + 1, len(bp_params)):
                three_combinations.append([bp_params[i], bp_params[j], bp_params[k]])

    # Four combinations
    four_combinations = []
    for i in range(len(bp_params)):
        for j in range(i + 1, len(bp_params)):
            for k in range(j + 1, len(bp_params)):
                for l in range(k + 1, len(bp_params)):
                    four_combinations.append([bp_params[i], bp_params[j], bp_params[k], bp_params[l]])

    # Coherence times (frequencies)
    coherence_times = [2**i for i in range(1, 17)]  # 2, 4, 8, ..., 65536

    print("=" * 80)
    print("生成固定到達率組合實驗資料")
    print("=" * 80)
    print(f"工作數量: {num_jobs}")
    print(f"重複次數: {num_replications}")
    print(f"固定到達率: {list(fixed_arrivals.values())}")
    print(f"2-組合數量: {len(two_combinations)}")
    print(f"3-組合數量: {len(three_combinations)}")
    print(f"4-組合數量: {len(four_combinations)}")
    print(f"Coherence times: {len(coherence_times)}")
    total_files = len(fixed_arrivals) * num_replications * (len(two_combinations) + len(three_combinations) + len(four_combinations)) * len(coherence_times)
    print(f"總檔案數: {total_files}")
    print("=" * 80)

    for arrival_name, arrival_rate in fixed_arrivals.items():
        print(f"\n處理 {arrival_name} (mean inter-arrival = {arrival_rate})...")

        for rep in tqdm.tqdm(range(1, num_replications + 1), desc=f"{arrival_name} combination replications"):
            folder_name = f"{arrival_name}_combination_{rep}"

            # Process two combinations
            for idx, param_set in enumerate(two_combinations, 1):
                # Create folder name like "two_combination_H64_H512"
                h_values = "_".join([f"H{int(p['H'])}" for p in param_set])
                comb_folder_name = f"two_combination_{h_values}"

                for coherence_time in coherence_times:
                    # Generate jobs
                    job_list = combination_fixed_arrival_job_init(
                        num_jobs=num_jobs,
                        param_set=param_set,
                        fixed_inter_arrival=arrival_rate,
                        coherence_time=coherence_time
                    )

                    # Create directory structure
                    freq_folder_name = f"freq_{coherence_time}_1"
                    csv_filename = f"pair_{idx}_freq_{coherence_time}.csv"

                    # Full path: data/fix20_combination_1/two_combination_H64_H512/freq_2_1/pair_1_freq_2.csv
                    folder_path = os.path.join("data", folder_name, comb_folder_name, freq_folder_name)
                    os.makedirs(folder_path, exist_ok=True)

                    csv_path = os.path.join(folder_path, csv_filename)
                    Write_csv.Write(csv_path, job_list)

            # Process three combinations
            for idx, param_set in enumerate(three_combinations, 1):
                h_values = "_".join([f"H{int(p['H'])}" for p in param_set])
                comb_folder_name = f"three_combination_{h_values}"

                for coherence_time in coherence_times:
                    job_list = combination_fixed_arrival_job_init(
                        num_jobs=num_jobs,
                        param_set=param_set,
                        fixed_inter_arrival=arrival_rate,
                        coherence_time=coherence_time
                    )

                    freq_folder_name = f"freq_{coherence_time}_1"
                    csv_filename = f"triplet_{idx}_freq_{coherence_time}.csv"

                    folder_path = os.path.join("data", folder_name, comb_folder_name, freq_folder_name)
                    os.makedirs(folder_path, exist_ok=True)

                    csv_path = os.path.join(folder_path, csv_filename)
                    Write_csv.Write(csv_path, job_list)

            # Process four combinations
            for idx, param_set in enumerate(four_combinations, 1):
                h_values = "_".join([f"H{int(p['H'])}" for p in param_set])
                comb_folder_name = f"four_combination_{h_values}"

                for coherence_time in coherence_times:
                    job_list = combination_fixed_arrival_job_init(
                        num_jobs=num_jobs,
                        param_set=param_set,
                        fixed_inter_arrival=arrival_rate,
                        coherence_time=coherence_time
                    )

                    freq_folder_name = f"freq_{coherence_time}_1"
                    csv_filename = f"quadruplet_{idx}_freq_{coherence_time}.csv"

                    folder_path = os.path.join("data", folder_name, comb_folder_name, freq_folder_name)
                    os.makedirs(folder_path, exist_ok=True)

                    csv_path = os.path.join(folder_path, csv_filename)
                    Write_csv.Write(csv_path, job_list)

    print("\n" + "=" * 80)
    print("✓ 資料生成完成！")
    print("=" * 80)


def analyze_jobs(job_list: List[Dict]) -> Dict:
    """
    分析工作列表，返回統計信息
    
    Parameters:
    job_list (list): 工作列表，每個工作包含 arrival_time 和 job_size
    
    Returns:
    dict: 包含各種統計信息的字典
    """
    if not job_list:
        return {}
    
    job_sizes = [job["job_size"] for job in job_list]
    arrival_times = [job["arrival_time"] for job in job_list]
    
    # 計算抵達時間間隔
    inter_arrivals = []
    for i in range(1, len(arrival_times)):
        inter_arrivals.append(arrival_times[i] - arrival_times[i-1])
    
    stats_dict = {
        # 工作大小統計
        "job_size_mean": np.mean(job_sizes),
        "job_size_std": np.std(job_sizes),
        "job_size_min": np.min(job_sizes),
        "job_size_max": np.max(job_sizes),
        "job_size_median": np.median(job_sizes),
        "job_size_q25": np.percentile(job_sizes, 25),
        "job_size_q75": np.percentile(job_sizes, 75),
        
        # 抵達時間統計
        "arrival_time_min": np.min(arrival_times),
        "arrival_time_max": np.max(arrival_times),
        "total_duration": arrival_times[-1] - arrival_times[0] if len(arrival_times) > 1 else 0,
        
        # 抵達間隔統計
        "inter_arrival_mean": np.mean(inter_arrivals) if inter_arrivals else 0,
        "inter_arrival_std": np.std(inter_arrivals) if inter_arrivals else 0,
        "inter_arrival_min": np.min(inter_arrivals) if inter_arrivals else 0,
        "inter_arrival_max": np.max(inter_arrivals) if inter_arrivals else 0,
        "inter_arrival_median": np.median(inter_arrivals) if inter_arrivals else 0,
        
        # 基本信息
        "num_jobs": len(job_list)
    }
    
    return stats_dict

def test_job_generation(num_jobs: int = 1000, verbose: bool = True) -> Dict:
    """
    測試不同工作生成函數的統計特性
    
    Parameters:
    num_jobs (int): 要生成的工作數量
    verbose (bool): 是否打印詳細信息
    
    Returns:
    dict: 包含所有測試結果的字典
    """
    results = {}
    
    # 測試 Bounded Pareto (avg_30)
    if verbose:
        print("\n" + "="*60)
        print("測試 Bounded Pareto 分布 (avg_30)")
        print("="*60)
    
    for i, param in enumerate(bp_parameter_30):
        job_list = job_init(num_jobs, 30, param)
        stats = analyze_jobs(job_list)
        results[f"BP_avg30_param{i}"] = stats
        
        if verbose:
            print(f"\n參數 {i}: L={param['L']:.2f}, H={param['H']:.0f}")
            print(f"  工作大小: 平均={stats['job_size_mean']:.2f}, "
                  f"標準差={stats['job_size_std']:.2f}, "
                  f"範圍=[{stats['job_size_min']}, {stats['job_size_max']}]")
            print(f"  抵達間隔: 平均={stats['inter_arrival_mean']:.2f}, "
                  f"標準差={stats['inter_arrival_std']:.2f}")
    
    # 測試 Normal 分布 (avg_30)
    if verbose:
        print("\n" + "="*60)
        print("測試 Normal 分布 (avg_30)")
        print("="*60)
    
    for i, param in enumerate(normal_parameter_30):
        job_list = job_init(num_jobs, 30, param)
        stats = analyze_jobs(job_list)
        results[f"Normal_avg30_param{i}"] = stats
        
        if verbose:
            print(f"\n參數 {i}: mean={param['mean']}, std={param['std']}")
            print(f"  工作大小: 平均={stats['job_size_mean']:.2f}, "
                  f"標準差={stats['job_size_std']:.2f}, "
                  f"範圍=[{stats['job_size_min']}, {stats['job_size_max']}]")
            print(f"  抵達間隔: 平均={stats['inter_arrival_mean']:.2f}, "
                  f"標準差={stats['inter_arrival_std']:.2f}")
    
    # 測試 Random 模式
    if verbose:
        print("\n" + "="*60)
        print("測試 Random 模式")
        print("="*60)
    
    coherence_times = [2, 128, 16384]
    for ct in coherence_times:
        # Bounded Pareto random
        job_list = bounded_pareto_random_job_init(num_jobs, coherence_time=ct)
        stats = analyze_jobs(job_list)
        results[f"BP_random_ct{ct}"] = stats
        
        if verbose:
            print(f"\nBounded Pareto Random (coherence_time={ct})")
            print(f"  工作大小: 平均={stats['job_size_mean']:.2f}, "
                  f"標準差={stats['job_size_std']:.2f}")
            print(f"  抵達間隔: 平均={stats['inter_arrival_mean']:.2f}, "
                  f"標準差={stats['inter_arrival_std']:.2f}")
        
        # Normal random
        job_list = normal_random_job_init(num_jobs, coherence_time=ct)
        stats = analyze_jobs(job_list)
        results[f"Normal_random_ct{ct}"] = stats
        
        if verbose:
            print(f"\nNormal Random (coherence_time={ct})")
            print(f"  工作大小: 平均={stats['job_size_mean']:.2f}, "
                  f"標準差={stats['job_size_std']:.2f}")
            print(f"  抵達間隔: 平均={stats['inter_arrival_mean']:.2f}, "
                  f"標準差={stats['inter_arrival_std']:.2f}")
    
    # 測試 Soft Random 模式
    if verbose:
        print("\n" + "="*60)
        print("測試 Soft Random 模式")
        print("="*60)
    
    for ct in coherence_times:
        # Bounded Pareto soft random
        job_list = bounded_pareto_soft_random_job_init(num_jobs, coherence_time=ct)
        stats = analyze_jobs(job_list)
        results[f"BP_softrandom_ct{ct}"] = stats
        
        if verbose:
            print(f"\nBounded Pareto Soft Random (coherence_time={ct})")
            print(f"  工作大小: 平均={stats['job_size_mean']:.2f}, "
                  f"標準差={stats['job_size_std']:.2f}")
            print(f"  抵達間隔: 平均={stats['inter_arrival_mean']:.2f}, "
                  f"標準差={stats['inter_arrival_std']:.2f}")
        
        # Normal soft random
        job_list = normal_soft_random_job_init(num_jobs, coherence_time=ct)
        stats = analyze_jobs(job_list)
        results[f"Normal_softrandom_ct{ct}"] = stats
        
        if verbose:
            print(f"\nNormal Soft Random (coherence_time={ct})")
            print(f"  工作大小: 平均={stats['job_size_mean']:.2f}, "
                  f"標準差={stats['job_size_std']:.2f}")
            print(f"  抵達間隔: 平均={stats['inter_arrival_mean']:.2f}, "
                  f"標準差={stats['inter_arrival_std']:.2f}")
    
    return results

def export_test_results_to_csv(results: Dict, filename: str = "test_results.csv"):
    """
    將測試結果導出為 CSV 文件
    
    Parameters:
    results (dict): test_job_generation() 返回的結果字典
    filename (str): 輸出文件名
    """
    df = pd.DataFrame.from_dict(results, orient='index')
    df.to_csv(filename)
    print(f"\n測試結果已保存到: {filename}")

def compare_distributions(num_jobs: int = 5000) -> pd.DataFrame:
    """
    比較不同分布的工作大小特性
    
    Parameters:
    num_jobs (int): 每個分布生成的工作數量
    
    Returns:
    DataFrame: 包含比較結果的數據框
    """
    comparison_data = []
    
    # BP 分布
    for i, param in enumerate(bp_parameter_30):
        job_list = job_init(num_jobs, 30, param)
        job_sizes = [job["job_size"] for job in job_list]
        
        comparison_data.append({
            "Type": "Bounded_Pareto",
            "Param_Index": i,
            "L": param["L"],
            "H": param["H"],
            "Mean": np.mean(job_sizes),
            "Std": np.std(job_sizes),
            "Min": np.min(job_sizes),
            "Max": np.max(job_sizes),
            "Median": np.median(job_sizes),
            "Q25": np.percentile(job_sizes, 25),
            "Q75": np.percentile(job_sizes, 75)
        })
    
    # Normal 分布
    for i, param in enumerate(normal_parameter_30):
        job_list = job_init(num_jobs, 30, param)
        job_sizes = [job["job_size"] for job in job_list]
        
        comparison_data.append({
            "Type": "Normal",
            "Param_Index": i,
            "L": param["mean"],
            "H": param["std"],
            "Mean": np.mean(job_sizes),
            "Std": np.std(job_sizes),
            "Min": np.min(job_sizes),
            "Max": np.max(job_sizes),
            "Median": np.median(job_sizes),
            "Q25": np.percentile(job_sizes, 25),
            "Q75": np.percentile(job_sizes, 75)
        })
    
    df = pd.DataFrame(comparison_data)
    return df

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Job initialization and testing')
    parser.add_argument('--mode', type=str, default='generate',
                       choices=['generate', 'test', 'compare', 'fix_combination'],
                       help='運行模式: generate=生成數據, test=運行測試, compare=比較分布, fix_combination=生成固定到達率組合數據')
    parser.add_argument('--num-jobs', type=int, default=10000,
                       help='測試時生成的工作數量')
    parser.add_argument('--num-replications', type=int, default=10,
                       help='固定到達率實驗的重複次數')
    parser.add_argument('--output', type=str, default='test_results.csv',
                       help='測試結果輸出文件名')

    args = parser.parse_args()

    if args.mode == 'generate':
        # 原始的數據生成模式
        for i in range(1, 11):
            Save_file(10000, i)

    elif args.mode == 'fix_combination':
        # 固定到達率組合實驗資料生成
        print("生成固定到達率組合實驗資料...")
        Save_fix_combination_files(num_jobs=args.num_jobs, num_replications=args.num_replications)

    elif args.mode == 'test':
        # 測試模式
        print("開始測試工作生成函數...")
        results = test_job_generation(num_jobs=args.num_jobs, verbose=True)
        export_test_results_to_csv(results, args.output)
        print("\n測試完成！")

    elif args.mode == 'compare':
        # 比較模式
        print("開始比較不同分布...")
        df = compare_distributions(num_jobs=args.num_jobs)
        print("\n分布比較結果:")
        print(df.to_string())

        output_file = args.output.replace('.csv', '_comparison.csv')
        df.to_csv(output_file, index=False)
        print(f"\n比較結果已保存到: {output_file}")