import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Sjf(jobs):
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])
    
    current_time = 0
    waiting_jobs = []
    flow_times = []
    
    while jobs or waiting_jobs:
        # Add jobs to the waiting list that have arrived by the current time
        while jobs and jobs[0][0] <= current_time:
            waiting_jobs.append(jobs.pop(0))
        
        if waiting_jobs:
            # Select the job with the shortest job size from the waiting list
            waiting_jobs.sort(key=lambda x: x[1])
            current_job = waiting_jobs.pop(0)
            
            # Wait if there's no job to process until at least one job arrives
            if current_time < current_job[0]:
                current_time = current_job[0]
            
            # Process the selected job
            start_time = current_time
            current_time += current_job[1]
            completion_time = current_time
            
            # Calculate the flow time for the current job
            flow_time = completion_time - current_job[0]
            flow_times.append(flow_time)
        else:
            # If no jobs are waiting and jobs are still to arrive, jump to the next arrival time
            if jobs:
                current_time = jobs[0][0]
    
    # Calculate average flow time and flow time L2 norm
    average_flow_time = np.mean(flow_times)
    flow_time_l2_norm = np.linalg.norm(flow_times)
    print("SJF Average Flow Time:", average_flow_time)
    print("SJF Flow Time L2 Norm:", flow_time_l2_norm)
    return average_flow_time, flow_time_l2_norm

# # Example input
# jobs = Read_csv('(0.025, 16.772).csv')

# # Run the SJF algorithm
# average_flow_time, flow_time_l2_norm = Sjf(jobs)

# print("Average Flow Time:", average_flow_time)
# print("Flow Time L2 Norm:", flow_time_l2_norm)
