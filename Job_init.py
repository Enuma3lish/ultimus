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

def generate_bounded_pareto(alpha, xmin, xmax, size=1):
    """
    Correctly generate bounded Pareto distributed random values.
    
    Parameters:
    alpha (float): Shape parameter
    xmin (float): Lower bound
    xmax (float): Upper bound
    size (int): Number of samples to generate
    
    Returns:
    Array of bounded Pareto random variables
    """
    # Calculate the CDF values at xmin and xmax
    cdf_xmin = 1 - (xmin / xmax) ** alpha
    
    # Generate uniform random values between 0 and cdf_xmin
    u = np.random.uniform(0, cdf_xmin, size=size)
    
    # Transform to bounded Pareto using inverse CDF
    x = xmin / ((1 - u) ** (1 / alpha))
    
    return x

def job_init(num_jobs, avg_inter_arrival_time, xmin, xmax):
    """
    Create jobs with a correctly bounded Pareto distribution for job sizes.
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    avg_inter_arrival_time (float): Average inter-arrival time
    xmin (float): Lower bound for job sizes
    xmax (float): Upper bound for job sizes
    """
    alpha = 1.1
    samples = []
    
    # Generate job sizes using the correct bounded Pareto
    job_sizes = [math.ceil(size) for size in generate_bounded_pareto(alpha, xmin, xmax, size=num_jobs)]
    
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
    for k in range(num_jobs):
        samples.append({"arrival_time": arrival_times[k], "job_size": job_sizes[k]})
    return samples

def random_job_init(num_jobs, coherence_time=1):
    """
    Create jobs with randomly selected parameters that properly simulate an online scenario
    where both bounded Pareto parameters and inter-arrival times change after coherence_time units of time.
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): Time units after which parameters may change
    """
    samples = []
    all_parameters = []
    for param_set in parameter_sets.values():
        all_parameters.extend(param_set)
    
    # Initialize with random parameter set and inter-arrival time
    current_param = random.choice(all_parameters)
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    current_time = 0
    last_change_time = 0  # Track when parameters were last changed
    
    # Generate jobs one by one in an online manner
    for _ in range(num_jobs):
        # Check if we need to change the parameter set and inter-arrival time based on elapsed time
        if current_time - last_change_time >= coherence_time:
            current_param = random.choice(all_parameters)
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            last_change_time = current_time  # Update the last change time
        
        # Get bounds from current parameter set
        xmin, xmax = current_param["L"], current_param["H"]
        
        # Generate a single job size using bounded Pareto
        job_size = math.ceil(generate_bounded_pareto(1.1, xmin, xmax, size=1)[0])
        
        # Generate arrival time using current inter-arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        # Add job to samples
        samples.append({"arrival_time": current_time, "job_size": job_size})
    
    return samples

def soft_random_job_init(num_jobs, coherence_time=1):
    """
    Create jobs with soft randomness in an online manner.
    First chooses a parameter set family (30, 60, 90) randomly, then smoothly transitions
    between parameters within that family using probabilistic rules.
    Inter-arrival times are also randomly selected and change every coherence_time units of time.
    
    Transition Rules:
    - First parameter (highest L): 1/2 to move to next index (lower L), 1/2 to stay
    - Last parameter (lowest L): 1/2 to move to previous index (higher L), 1/2 to stay  
    - Middle parameters: 1/3 to stay, 1/3 to move to previous index (higher L), 1/3 to move to next index (lower L)
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    coherence_time (int): Time units after which parameters may change
    """
    samples = []
    param_set_keys = list(parameter_sets.keys())  # ["avg_30", "avg_60", "avg_90"]
    
    # Step 1: Randomly choose one of the three parameter set families
    current_param_set_key = random.choice(param_set_keys)
    current_param_set = parameter_sets[current_param_set_key]
    
    # Step 2: Start with a random parameter within the chosen family
    current_param_index = random.randint(0, len(current_param_set) - 1)
    
    # Step 3: Initialize with a random inter-arrival time
    current_avg_inter_arrival = random.choice(inter_arrival_time)
    
    current_time = 0
    last_change_time = 0  # Track when parameters were last changed
    
    # Generate jobs one by one in an online manner
    for _ in range(num_jobs):
        # Check if we need to potentially change the parameter within the same family and inter-arrival time based on elapsed time
        if current_time - last_change_time >= coherence_time:
            num_params = len(current_param_set)
            
            # Apply smooth transition rules based on current position
            if current_param_index == 0:  # First parameter (highest L value)
                # 1/2 to go to next index (lower L), 1/2 to stay
                if random.random() < 0.5:
                    current_param_index = 1  # move to next parameter (lower L)
                # else stay at index 0
                
            elif current_param_index == num_params - 1:  # Last parameter (lowest L value)
                # 1/2 to go to previous index (higher L), 1/2 to stay
                if random.random() < 0.5:
                    current_param_index = num_params - 2  # move to previous parameter (higher L)
                # else stay at last index
                
            else:  # Middle parameters
                # 1/3 to stay, 1/3 to go to previous index (higher L), 1/3 to go to next index (lower L)
                choice = random.random()
                if choice < 1/3:
                    # stay at current index
                    pass
                elif choice < 2/3:
                    # go to previous index (higher L value)
                    current_param_index -= 1
                else:
                    # go to next index (lower L value)
                    current_param_index += 1
            
            # Randomly select new inter-arrival time
            current_avg_inter_arrival = random.choice(inter_arrival_time)
            
            # Reset time tracker
            last_change_time = current_time
        
        # Get bounds from current parameter
        current_param = current_param_set[current_param_index]
        xmin, xmax = current_param["L"], current_param["H"]
        
        # Generate a single job size using bounded Pareto
        job_size = math.ceil(generate_bounded_pareto(1.1, xmin, xmax, size=1)[0])
        
        # Generate arrival time using current inter-arrival time
        inter_arrival = round(np.random.exponential(scale=current_avg_inter_arrival))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        # Add job to samples
        samples.append({"arrival_time": current_time, "job_size": job_size})
    
    return samples

def Save_file(num_jobs, i):
    # Create base data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Create frequency/coherence time folders WITH the _i suffix
    coherence_times = [pow(2, j) for j in range(1, 17, 1)]
    for ct in coherence_times:
        freq_folder = f"data/freq_{ct}_{i}"
        os.makedirs(freq_folder, exist_ok=True)
    
    # Process normal parameter sets (30, 60, 90)
    for param_name, param_set in parameter_sets.items():
        # Create folder for this parameter set WITH the _i suffix
        param_folder = f"data/{param_name}_{i}"
        os.makedirs(param_folder, exist_ok=True)
        
        for avg_inter_arrival in inter_arrival_time:
            for b in tqdm.tqdm(param_set, desc=f"Processing {param_name}_{i}, inter_arrival={avg_inter_arrival}"):
                job_list = job_init(num_jobs, avg_inter_arrival, b["L"], b["H"])
                bl = b["L"]
                bh = b["H"]
                # Format the filename using the CORRECT folder path with _i suffix
                filename = f"{param_folder}/({avg_inter_arrival}, {bl}_{bh}).csv"
                Write_csv.Write_raw(filename, job_list)
    
    # Generate and save job lists for each coherence time
    for ct in tqdm.tqdm(coherence_times, desc=f"Processing random jobs _{i}"):
        # Generate job list with random parameters and specified coherence time
        job_list = random_job_init(num_jobs, coherence_time=ct)
        
        # Save to the frequency-specific folder WITH the _i suffix
        filename = f"data/freq_{ct}_{i}/random_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)
    
    # Create soft random folder WITH the _i suffix
    softrandom_base = f"data/softrandom_{i}"
    os.makedirs(softrandom_base, exist_ok=True)
    
    # Create coherence time subfolders within softrandom_{i}
    for ct in tqdm.tqdm(coherence_times, desc=f"Processing soft random jobs _{i}"):
        softrandom_folder = f"{softrandom_base}/freq_{ct}_{i}"
        os.makedirs(softrandom_folder, exist_ok=True)
        
        # Generate job list with soft random parameters and specified coherence time
        job_list = soft_random_job_init(num_jobs, coherence_time=ct)
        
        # Save to the soft random coherence-specific folder with coherence time in filename
        filename = f"{softrandom_folder}/softrandom_freq_{ct}.csv"
        Write_csv.Write_raw(filename, job_list)

if __name__ == "__main__":
    for i in range(1, 11):
        Save_file(1000, i)