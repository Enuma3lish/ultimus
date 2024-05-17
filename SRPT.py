import numpy as np
from heapq import heappush, heappop
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Srpt(jobs):
    jobs.sort(key=lambda x: x[0])  # Sort jobs based on arrival time
    n = len(jobs)
    current_time = 0
    queue = []  # Priority queue for (remaining_time, arrival_time, job_index)
    job_index = 0
    flow_times = [0] * n
    execution_times = [0] * n  # Track execution time for preemption
    logs = [{'arrival_time': job[0], 'first_executed_time': None, 'ifdone': False} for job in jobs]
    
    while job_index < n or queue:
        # If no jobs in the queue, move current time to the arrival of the next job
        if not queue and job_index < n:
            current_time = max(current_time, jobs[job_index][0])
        
        # Push all jobs that have arrived by the current time into the queue
        while job_index < n and jobs[job_index][0] <= current_time:
            remaining_time = jobs[job_index][1] - execution_times[job_index]
            heappush(queue, (remaining_time, jobs[job_index][0], job_index))
            job_index += 1
        
        # Process the job with the shortest remaining time
        if queue:
            remaining_time, arrival_time, index = heappop(queue)
            next_job_time = jobs[job_index][0] if job_index < n else float('inf')
            time_to_next_job = next_job_time - current_time
            
            # Determine if current job can be completed before next job arrives
            if remaining_time <= time_to_next_job:
                execution_slice = remaining_time
            else:
                execution_slice = time_to_next_job
                heappush(queue, (remaining_time - execution_slice, arrival_time, index))  # Reinsert with updated remaining time
            
            # Update current time and execution times
            current_time += execution_slice
            execution_times[index] += execution_slice
            
            # Log the first execution time if not already logged
            if logs[index]['first_executed_time'] is None:
                logs[index]['first_executed_time'] = current_time - execution_slice
            
            # Check if the job is completed
            if execution_times[index] == jobs[index][1]:
                flow_times[index] = current_time - arrival_time
                logs[index]['ifdone'] = True  # Mark job as done
    
    # Calculate norms and average flow time
    average_flow_time = sum(flow_times) / n
    # l1_norm_flow_time = sum(flow_times)  # Sum of absolute flow times
    l2_norm_flow_time = (sum(x**2 for x in flow_times) ** 0.5)
    
    return average_flow_time,l2_norm_flow_time, logs

jobs = Read_csv("data/(20, 4.073).csv")
avg_flow_time, l2_norm, logs = Srpt(jobs)
print(f"Average Flow Time: {avg_flow_time}")
print(f"L2-Norm of Flow Times: {l2_norm}")
# print("Logs:")
# for log in logs:
#     print(log)
# print(logs)
