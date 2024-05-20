import math
import numpy as np
import pandas as pd
import random
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def calculate_Bj(j):
    """ Calculate Bj based on the number of jobs (j). """
    if j >= 3:
        U = random.uniform(0, 1)
        return U / j**-12
    else:
        return 1

def get_execution_time(i, Bj):
    """ Determine execution time at level i given Bj. """
    return 2**i * max(1, 2 - Bj)

def Rmlfq(jobs):
    """ Simulate RMLF algorithm with updated conditions. """
    time = 0
    jobs = sorted(jobs, key=lambda x: x[0])  # Sort by arrival time
    num_jobs = len(jobs)
    levels = 100  # Fixed number of queues
    queues = [[] for _ in range(levels)]
    flow_times = []
    job_index = 0  # To track which job we are on for Bj calculations

    while jobs or any(queues):
        # Load new jobs into the system if it's time or queue is empty
        while jobs and (jobs[0][0] <= time or not any(queues)):
            arrival_time, job_size = jobs.pop(0)
            if time < arrival_time:
                time = arrival_time  # Adjust time to avoid idling
            Bj = calculate_Bj(job_index + 1)
            queues[0].append([job_size, time, Bj])  # Add job to first level
            job_index += 1

        # Process jobs in queues starting from the first level
        for i in range(levels):
            if queues[i]:
                job_size, start_time, Bj = queues[i].pop(0)
                exec_time = get_execution_time(i, Bj)
                if job_size > exec_time:
                    # Not completed, move to next level
                    next_level = min(i + 1, levels - 1)
                    queues[next_level].append([job_size - exec_time, start_time, Bj])
                else:
                    # Job completed
                    flow_times.append(time - start_time + exec_time)
                time += exec_time
                break
        else:
            # If all queues are empty and jobs remain, adjust time to next job's arrival
            if jobs:
                time = max(time, jobs[0][0])

    # Calculate average and L2-norm flow times
    average_flow_time = sum(flow_times) / num_jobs
    l2_norm_flow_time = sum(ft**2 for ft in flow_times)**0.5

    return average_flow_time, l2_norm_flow_time
# Example call with the job list
jobs = Read_csv("data/(40, 4.073).csv")
average_flow_time, l2_norm_flow_time= Rmlfq(jobs)
print(average_flow_time)
print(l2_norm_flow_time)
