import numpy as np
import pandas as pd
from math import sqrt
import heapq

def Read_csv(filename):
    # Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

def Setf(jobs):
    time = 0
    total_flow_time = 0
    squared_flow_time = 0
    completed_jobs = 0
    current_job = None
    job_heap = []  # min-heap to store jobs based on elapsed time
    job_execution_times = {}
    job_counter = 0  # used to break ties in the heap

    for arrival_time, job_size in jobs:
        # Process all jobs that have completed before this new job arrives
        while job_heap and time < arrival_time:
            if not current_job:
                _, _, current_job = heapq.heappop(job_heap)
            
            job_arrival, job_size = current_job
            elapsed_time = job_execution_times[current_job]
            remaining_time = job_size - elapsed_time
            
            if time + remaining_time <= arrival_time:
                # Job completes before next arrival
                time += remaining_time
                flow_time = time - job_arrival
                total_flow_time += flow_time
                squared_flow_time += flow_time ** 2
                completed_jobs += 1
                current_job = None
            else:
                # Job is interrupted by new arrival
                run_time = arrival_time - time
                job_execution_times[current_job] += run_time
                heapq.heappush(job_heap, (job_execution_times[current_job], job_counter, current_job))
                job_counter += 1
                time = arrival_time
                break
        
        if time < arrival_time:
            time = arrival_time

        # Add newly arrived job
        new_job = (arrival_time, job_size)
        job_execution_times[new_job] = 0
        heapq.heappush(job_heap, (0, job_counter, new_job))
        job_counter += 1

        # Select the job with the shortest elapsed time
        if not current_job or job_execution_times[new_job] < job_execution_times[current_job]:
            if current_job:
                heapq.heappush(job_heap, (job_execution_times[current_job], job_counter, current_job))
                job_counter += 1
            current_job = new_job

    # Process remaining jobs after all arrivals
    while current_job or job_heap:
        if not current_job and job_heap:
            _, _, current_job = heapq.heappop(job_heap)

        if current_job:
            job_arrival, job_size = current_job
            elapsed_time = job_execution_times[current_job]
            remaining_time = job_size - elapsed_time
            
            time += remaining_time
            flow_time = time - job_arrival
            total_flow_time += flow_time
            squared_flow_time += flow_time ** 2
            completed_jobs += 1
            current_job = None

    average_flow_time = total_flow_time / completed_jobs if completed_jobs > 0 else 0
    l2_norm_flow_time = sqrt(squared_flow_time)

    return average_flow_time, l2_norm_flow_time

# # Example usage
# jobs = Read_csv("data/(20, 16.772).csv")
# avg, l2 = Setf(jobs)
# print(f"Average flow time: {avg}")
# print(f"L2 norm of flow time: {l2}")