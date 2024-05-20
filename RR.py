import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Rr(jobs):
    if not jobs:
        return 0, 0, 0, []  # Handle case with no jobs

    # Sort jobs by their arrival times
    jobs.sort(key=lambda x: x[0])
    current_time = jobs[0][0]  # Start at the arrival time of the first job
    queue = []
    job_logs = []
    flow_times = []

    # Initialize job details with remaining time and logging details
    for job in jobs:
        queue.append({
            'arrival_time': job[0],
            'remaining_time': job[1],
            'first_executed_time': None,
            'ifdone': False
        })
    
    # Process the jobs in round-robin fashion
    while queue:
        current_job = queue.pop(0)
        
        # Ensure the job does not start before its arrival time
        if current_job['first_executed_time'] is None:
            current_job['first_executed_time'] = max(current_time, current_job['arrival_time'])
            current_time = current_job['first_executed_time']
        
        # Execute the job for one unit of time
        current_job['remaining_time'] -= 1
        current_time += 1
        
        # Check if the job is completed
        if current_job['remaining_time'] == 0:
            current_job['ifdone'] = True
            flow_time = current_time - current_job['arrival_time']
            flow_times.append(flow_time)
            job_logs.append({
                'arrival_time': current_job['arrival_time'],
                'first_executed_time': current_job['first_executed_time'],
                'ifdone': current_job['ifdone']
            })
        else:
            # Re-enqueue the job if not completed
            queue.append(current_job)
    
    # Calculate the metrics
    n = len(flow_times)
    average_flow_time = sum(flow_times) / n
    #l1_norm_flow_time = sum(flow_times)  # Sum of absolute flow times
    l2_norm_flow_time = (sum(x**2 for x in flow_times) ** 0.5)  # Square root of sum of squares

    return average_flow_time, l2_norm_flow_time, job_logs
jobs = Read_csv("data/(30, 4.073).csv")
avg,l2,logs=Rr(jobs)
print(avg)
print(l2)