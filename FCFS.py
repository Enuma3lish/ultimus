import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Fcfs(jobs):
    time = 0  # Current time
    job_logs = []  # Logs for each job
    flow_times = []  # Store flow times for each job to calculate metrics
    
    for job in jobs:
        arrival_time, job_size = job
        if time < arrival_time:
            time = arrival_time  # Wait for job to arrive if there is idle time
        first_executed_time = time
        time += job_size  # Update current time after job is done
        flow_time = time - arrival_time
        flow_times.append(flow_time)  # Add flow time for this job
        
        # Log for this job
        job_logs.append({
            'arrival_time': arrival_time,
            'first_executed_time': first_executed_time,
            'ifdone': True
        })
    
    # Calculate average flow time and L2-norm flow time
    avg_flow_time = np.mean(flow_times)
    l2_norm_flow_time = np.linalg.norm(flow_times)
    
    return avg_flow_time, l2_norm_flow_time, job_logs
jobs = Read_csv("data/(40, 16.772).csv")
avg,l2,logs=Fcfs(jobs)
print(avg)
print(l2)
# print(logs)
