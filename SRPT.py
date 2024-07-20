import heapq
import pandas as pd
import numpy as np

def Read_csv(filename):
    # Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

def Srpt(jobs):
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])
    
    current_time = 0
    total_flow_time = 0
    total_flow_time_squared = 0
    n = len(jobs)
    job_queue = []
    index = 0
    first_executed = [False] * n
    flow_times = []
    logs = []

    while index < n or job_queue:
        # Add all jobs that have arrived by current_time to the priority queue
        while index < n and jobs[index][0] <= current_time:
            heapq.heappush(job_queue, (jobs[index][1], index))
            index += 1

        if job_queue:
            # Get the job with the shortest remaining processing time
            remaining_time, job_index = heapq.heappop(job_queue)
            
            if not first_executed[job_index]:
                first_executed[job_index] = True
                current_time = max(current_time, jobs[job_index][0])

            # Process the job
            current_time += 1
            remaining_time -= 1
            logs.append([current_time, job_index, remaining_time])
            
            if remaining_time > 0:
                heapq.heappush(job_queue, (remaining_time, job_index))
            else:
                # Job is finished
                flow_time = current_time - jobs[job_index][0]
                flow_times.append(flow_time)
                total_flow_time += flow_time
                total_flow_time_squared += flow_time ** 2
        else:
            # If no jobs are ready to execute, move time forward
            if index < n:
                current_time = jobs[index][0]
    
    # Calculate average flow time
    average_flow_time = total_flow_time / n
    
    # Calculate L2 norm of the flow time
    l2_norm_flow_time = total_flow_time_squared ** 0.5
    
    return average_flow_time, l2_norm_flow_time, logs

def Save_logs_to_csv(logs, filename):
    # Convert logs to a DataFrame
    log_df = pd.DataFrame(logs, columns=["Current Time", "Job Index", "Remaining Time"])
    # Save DataFrame to a CSV file
    log_df.to_csv(filename, index=False)

jobs = Read_csv("data/(32, 4.073).csv")
#jobs = Read_csv("data/(30, 16.772).csv")
avg_flow_time, l2_norm,logs = Srpt(jobs)
print(avg_flow_time)
print(l2_norm)
