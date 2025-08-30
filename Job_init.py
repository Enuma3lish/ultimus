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

def random_job_init(num_jobs, avg_inter_arrival_time, coherence_time=1):
    """
    Create jobs with randomly selected parameters that properly simulate an online scenario
    where parameters change after coherence_time jobs.
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    avg_inter_arrival_time (float): Average inter-arrival time
    coherence_time (int): Number of jobs to use the same parameter set before potentially changing
    """
    samples = []
    all_parameters = []
    for param_set in parameter_sets.values():
        all_parameters.extend(param_set)
    
    # Initialize with a random parameter set
    current_param = random.choice(all_parameters)
    current_time = 0
    jobs_with_current_param = 0
    
    # Generate jobs one by one in an online manner
    for _ in range(num_jobs):
        # Check if we need to change the parameter set
        if jobs_with_current_param >= coherence_time:
            current_param = random.choice(all_parameters)
            jobs_with_current_param = 0
        
        # Get bounds from current parameter set
        xmin, xmax = current_param["L"], current_param["H"]
        
        # Generate a single job size using bounded Pareto
        job_size = math.ceil(generate_bounded_pareto(1.1, xmin, xmax, size=1)[0])
        
        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=avg_inter_arrival_time))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        # Add job to samples
        samples.append({"arrival_time": current_time, "job_size": job_size})
        
        # Increment counter for jobs with current param
        jobs_with_current_param += 1
    
    return samples

def soft_random_job_init(num_jobs, avg_inter_arrival_time, coherence_time=1):
    """
    Create jobs with soft randomness in an online manner.
    First chooses a parameter set family (30, 60, 90) randomly, then smoothly transitions
    between parameters within that family using probabilistic rules.
    
    Transition Rules:
    - First parameter (highest L): 1/2 to move to next index (lower L), 1/2 to stay
    - Last parameter (lowest L): 1/2 to move to previous index (higher L), 1/2 to stay  
    - Middle parameters: 1/3 to stay, 1/3 to move to previous index (higher L), 1/3 to move to next index (lower L)
    
    Parameters:
    num_jobs (int): Number of jobs to generate
    avg_inter_arrival_time (float): Average inter-arrival time
    coherence_time (int): Number of jobs before potentially selecting new parameters
    """
    samples = []
    param_set_keys = list(parameter_sets.keys())  # ["avg_30", "avg_60", "avg_90"]
    
    # Step 1: Randomly choose one of the three parameter set families
    current_param_set_key = random.choice(param_set_keys)
    current_param_set = parameter_sets[current_param_set_key]
    
    # Step 2: Start with a random parameter within the chosen family
    current_param_index = random.randint(0, len(current_param_set) - 1)
    
    current_time = 0
    jobs_since_last_change = 0  # Counter for jobs since last parameter change
    
    # Generate jobs one by one in an online manner
    for _ in range(num_jobs):
        # Check if we need to potentially change the parameter within the same family
        if jobs_since_last_change >= coherence_time:
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
            
            # Reset job counter
            jobs_since_last_change = 0
        
        # Get bounds from current parameter
        current_param = current_param_set[current_param_index]
        xmin, xmax = current_param["L"], current_param["H"]
        
        # Generate a single job size using bounded Pareto
        job_size = math.ceil(generate_bounded_pareto(1.1, xmin, xmax, size=1)[0])
        
        # Generate arrival time
        inter_arrival = round(np.random.exponential(scale=avg_inter_arrival_time))
        inter_arrival = max(1, inter_arrival)
        current_time += inter_arrival
        
        # Add job to samples
        samples.append({"arrival_time": current_time, "job_size": job_size})
        
        # Increment job counter
        jobs_since_last_change += 1
    
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
    
    # Generate and save job lists for each coherence time
    for ct in coherence_times:
        for avg_inter_arrival in tqdm.tqdm(inter_arrival_time, desc=f"Processing freq_{ct}"):
            # Generate job list with random parameters and specified coherence time
            job_list = random_job_init(num_jobs, avg_inter_arrival, coherence_time=ct)
            
            # Save to the frequency-specific folder
            filename = f"data/freq_{ct}/({avg_inter_arrival}).csv"
            Write_csv.Write_raw(filename, job_list)
    
    # Create soft random folder and generate soft random job lists for each coherence time
    os.makedirs("data/softrandom", exist_ok=True)
    
    # Create coherence time subfolders within softrandom
    for ct in coherence_times:
        softrandom_folder = f"data/softrandom/freq_{ct}"
        os.makedirs(softrandom_folder, exist_ok=True)
        
        for avg_inter_arrival in tqdm.tqdm(inter_arrival_time, desc=f"Processing soft random freq_{ct}"):
            # Generate job list with soft random parameters and specified coherence time
            job_list = soft_random_job_init(num_jobs, avg_inter_arrival, coherence_time=ct)
            
            # Save to the soft random coherence-specific folder
            filename = f"{softrandom_folder}/({avg_inter_arrival}).csv"
            Write_csv.Write_raw(filename, job_list)

if __name__ == "__main__":
    Save_file(1000)