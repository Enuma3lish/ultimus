import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Bal(jobs_input):
    jobs = [(job[0], job[1], i) for i, job in enumerate(jobs_input)]  # Include original index
    jobs.sort(key=lambda x: x[0])  # Sort by arrival time
    
    n = len(jobs)
    completion_times = [0] * n
    current_time = 0
    job_queue = []
    executed_jobs = 0
    
    while executed_jobs < n or job_queue:
        # Add jobs to the queue that have arrived
        while jobs and jobs[0][0] <= current_time:
            job_queue.append(jobs.pop(0))
        
        # Check for starvation
        starving_job = None
        for job in job_queue:
            waiting_time = current_time - job[0]
            if waiting_time > (n ** (2 / 3)):
                starving_job = job
                break
        
        if starving_job:
            # Handle the starving job first
            job_to_execute = starving_job
            job_queue.remove(starving_job)
        elif job_queue:
            # Proceed with SRPT for non-starving jobs
            job_queue.sort(key=lambda x: x[1])  # Sort by job size
            job_to_execute = job_queue.pop(0)
        else:
            job_to_execute = None
        
        if job_to_execute:
            # Execute the job
            idx = job_to_execute[2]
            execution_time = job_to_execute[1]
            completion_times[idx] = current_time + execution_time
            current_time += execution_time
            executed_jobs += 1
        else:
            # Increment time if no jobs are ready
            current_time += 1
    
    # Calculate metrics
    flow_times = [completion_times[i] - jobs_input[i][0] for i in range(n)]
    average_flow_time = sum(flow_times) / n
    l2_norm_flow_time = np.linalg.norm(flow_times, 2)
    
    return average_flow_time, l2_norm_flow_time

# Example input and running the function
jobs = Read_csv("data/(28, 16.772).csv")
average_flow_time, l2_norm_flow_time= Bal(jobs)

print(average_flow_time)
print(l2_norm_flow_time)
# print(max_flow_time, min_flow_time)
