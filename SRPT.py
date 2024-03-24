import numpy as np
from heapq import heappush, heappop
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Srpt(jobs):
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])
    n = len(jobs)
    current_time = 0
    queue = []  # Priority queue for (remaining_time, arrival_time, job_index)
    job_index = 0
    flow_times = [0] * n  # Completion time - Arrival time for each job
    
    while job_index < n or queue:
        if not queue:  # If queue is empty, jump to the next job arrival
            current_time = max(current_time, jobs[job_index][0])
        
        # Add all jobs that have arrived by the current time
        while job_index < n and jobs[job_index][0] <= current_time:
            heappush(queue, (jobs[job_index][1], jobs[job_index][0], job_index))
            job_index += 1
        
        if queue:
            remaining_time, arrival_time, index = heappop(queue)
            current_time += remaining_time  # Execute the job
            flow_times[index] = current_time - arrival_time  # Calculate flow time for the job
            
            # Update remaining times in queue (if needed)
            new_queue = []
            for rem_time, arr_time, idx in queue:
                heappush(new_queue, (rem_time, arr_time, idx))
            queue = new_queue
    
    average_flow_time = sum(flow_times) / n
    l2_norm_flow_time = np.sqrt(np.sum(np.square(flow_times)))
    
    return average_flow_time, l2_norm_flow_time
jobs = Read_csv("data/(26, 16.772).csv")
avg,l2=Srpt(jobs)
print(avg)
print(l2)
# # print(logs)
