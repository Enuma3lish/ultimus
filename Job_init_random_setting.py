import numpy as np
import scipy.stats as stats
import Write_csv
import math
import random
import os

# Define inter-arrival times
inter_arrival_time = [i for i in range(20, 41, 2)]

bp_parameter = [
    {"L": 56.300, "H": pow(2, 6)},
    {"L": 18.900, "H": pow(2, 9)},
    {"L": 12.400, "H": pow(2, 12)},
    {"L": 9.800, "H": pow(2, 15)},
    {"L": 8.500, "H": pow(2, 18)},
    {"L": 32.300, "H": pow(2, 9)},
    {"L": 19.700, "H": pow(2, 12)},
    {"L": 15.300, "H": pow(2, 15)},
    {"L": 13.000, "H": pow(2, 18)},
    {"L": 16.772, "H": pow(2, 6)},
    {"L": 7.918, "H": pow(2, 9)},
    {"L": 5.649, "H": pow(2, 12)},
    {"L": 4.639, "H": pow(2, 15)},
    {"L": 4.073, "H": pow(2, 18)},
    {"L": 56.300, "H": pow(2, 6)},
    {"L": 18.900, "H": pow(2, 9)},
    {"L": 12.400, "H": pow(2, 12)},
    {"L": 9.800, "H": pow(2, 15)},
    {"L": 8.500, "H": pow(2, 18)},
    {"L": 32.300, "H": pow(2, 9)},
    {"L": 19.700, "H": pow(2, 12)},
    {"L": 15.300, "H": pow(2, 15)},
    {"L": 13.000, "H": pow(2, 18)}
]

def generate_job_size(xmin, xmax, alpha=1.1):
    pareto = stats.pareto(b=alpha)
    while True:
        raw_sample = math.ceil(pareto.rvs(size=1)[0])
        if xmin <= raw_sample <= xmax:
            return raw_sample

def job_init(total_jobs, jobs_per_random, avg_inter_arrival_time):
    samples = []
    current_time = 0
    
    # Calculate how many random selections we need
    num_random_selections = math.ceil(total_jobs / jobs_per_random)
    
    jobs_created = 0
    for _ in range(num_random_selections):
        # Randomly select a bp_parameter set
        bp = random.choice(bp_parameter)
        
        # Generate jobs_per_random jobs with this bp_parameter
        remaining_jobs = min(jobs_per_random, total_jobs - jobs_created)
        for _ in range(remaining_jobs):
            # Generate inter-arrival time
            inter_arrival = max(1, round(np.random.exponential(scale=avg_inter_arrival_time)))
            current_time += inter_arrival
            
            # Generate job size using the selected bp_parameter
            job_size = generate_job_size(bp["L"], bp["H"])
            
            # Store the job with its parameters
            samples.append({
                "arrival_time": current_time,
                "job_size": job_size
            })
            
            jobs_created += 1
            
        if jobs_created >= total_jobs:
            break
    
    return samples

def Save_file(total_jobs, jobs_per_random):
    for avg_inter_arrival in inter_arrival_time:
        # Create directory if it doesn't exist
        directory = f"{jobs_per_random}_random_data"
        os.makedirs(directory, exist_ok=True)
        
        # For each inter-arrival time, generate jobs with specified number of jobs per random selection
        job_list = job_init(total_jobs, jobs_per_random, avg_inter_arrival)
        # Format the filename with just the inter_arrival time
        filename = f"{directory}/inter_arrival_{avg_inter_arrival}.csv"
        Write_csv.Write_raw(filename, job_list)

if __name__ == "__main__":
    # Example: 1000 total jobs, with 50 jobs per random selection
    jsettings = [1,25,50,100]
    # 100,200,400,1000,2000,4000,10000]
    for i in jsettings:
        Save_file(100, i)