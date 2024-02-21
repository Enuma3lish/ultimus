import heapq
import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Setf(jobs):
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])
    
    current_time = 0
    flow_times = []
    job_queue = []  # Priority queue for jobs, prioritized by elapsed execution time
    current_job = None
    jobs_in_progress = {}

    while jobs or job_queue or current_job:
        # Add newly arrived jobs to the queue
        while jobs and jobs[0][0] <= current_time:
            job = jobs.pop(0)
            heapq.heappush(job_queue, (0, job))  # Initialize elapsed execution time as 0
        
        # Update current job's elapsed execution time
        if current_job:
            elapsed_time, job = current_job
            elapsed_time += 1
            remaining_time = job[1] - elapsed_time
            if remaining_time > 0:
                heapq.heappush(job_queue, (elapsed_time, job))  # Requeue with updated elapsed time
            else:
                flow_times.append(current_time - job[0])
            current_job = None
        
        # Fetch the next job
        if not current_job and job_queue:
            elapsed_time, job = heapq.heappop(job_queue)
            current_job = (elapsed_time, job)
        
        # Increment time
        current_time += 1

    # Calculate average flow time and flow time L2 norm
    average_flow_time = np.mean(flow_times)
    flow_time_l2_norm = np.linalg.norm(flow_times)
    print("Average Flow Time:", average_flow_time)
    print("Flow Time L2 Norm:", flow_time_l2_norm)
    return average_flow_time, flow_time_l2_norm

# Example input
# jobs = Read_csv('(0.05, 16.772).csv')

# # Run the preemptive SETF algorithm
# average_flow_time, flow_time_l2_norm = Setf(jobs)

# print("Average Flow Time:", average_flow_time)
# print("Flow Time L2 Norm:", flow_time_l2_norm)
