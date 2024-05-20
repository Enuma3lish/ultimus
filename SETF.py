import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Setf(jobs):
    """
    Implements the Shortest Elapsed Time First scheduling algorithm.

    Parameters:
    jobs (list of list): A list of [arrival_time, job_size] pairs for each job.

    Returns:
    float: The average flow time.
    float: The L2 norm of flow time.
    """

    # Sort jobs by arrival time initially
    jobs.sort(key=lambda x: x[0])

    # Initialize variables
    time = 0
    completed_jobs = 0
    flow_times = []
    elapsed_time = []
    
    while jobs or elapsed_time:
        # Add new jobs to the elapsed_time list
        while jobs and jobs[0][0] <= time:
            job = jobs.pop(0)
            elapsed_time.append(job)
        
        if elapsed_time:
            # Sort the elapsed_time list by job size (shortest job first)
            elapsed_time.sort(key=lambda x: x[1])
            
            # Process the job with the shortest job size
            job = elapsed_time.pop(0)
            arrival_time, job_size = job
            start_time = max(time, arrival_time)
            finish_time = start_time + job_size
            flow_time = finish_time - arrival_time
            
            flow_times.append(flow_time)
            time = finish_time
            completed_jobs += 1
        else:
            # If no jobs are ready, move time forward to the arrival time of the next job
            if jobs:
                time = jobs[0][0]

    average_flow_time = sum(flow_times) / completed_jobs
    l2_norm_flow_time = np.sqrt(sum([ft**2 for ft in flow_times]))
    
    return average_flow_time, l2_norm_flow_time

jobs = Read_csv("data/(40, 4.073).csv")
avg,l2=Setf(jobs)
print(avg)
print(l2)
# print(logs)