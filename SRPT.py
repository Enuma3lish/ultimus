import heapq
import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Srpt(jobs):
    # Sort jobs by arrival time for processing
    jobs.sort(key=lambda x: x[0])
    
    current_time = 0  # Tracks the current time
    job_queue = []  # Priority queue for jobs based on remaining processing time
    current_job = None  # Currently running job
    flow_times = []  # To store flow times for each job

    while jobs or job_queue or current_job:
        # Add newly arrived jobs to the queue
        while jobs and jobs[0][0] <= current_time:
            job = jobs.pop(0)
            heapq.heappush(job_queue, (job[1], job[0], job))  # (remaining_time, arrival_time, job)

        # Check for preemption
        if current_job and job_queue and job_queue[0][0] < current_job[0]:
            # Preempt current job
            heapq.heappush(job_queue, (current_job[0], current_time - current_job[0] + current_job[1], current_job[2]))
            current_job = None

        # Schedule next job
        if not current_job and job_queue:
            remaining_time, arrival_time, job = heapq.heappop(job_queue)
            current_job = [remaining_time, arrival_time, job]  # Update current job with remaining time

        # If there's a job running, process it
        if current_job:
            current_job[0] -= 1  # Decrease remaining time
            if current_job[0] == 0:  # Job completed
                flow_time = current_time + 1 - current_job[2][0]  # Completion time - Arrival time
                flow_times.append(flow_time)
                current_job = None  # Reset current job

        current_time += 1  # Increment time

    # Calculate average flow time and flow time L2 norm
    average_flow_time = np.mean(flow_times)
    flow_time_l2_norm = np.linalg.norm(flow_times)
    print("Srpt Average Flow Time:", average_flow_time)
    print("Srpt Flow Time L2 Norm:", flow_time_l2_norm)
    return average_flow_time, flow_time_l2_norm

# # Example input
# jobs = Read_csv('(0.05, 16.772).csv')
# # Run the SRPT algorithm
# average_flow_time, flow_time_l2_norm = Srpt(jobs)

# print("Average Flow Time:", average_flow_time)
# print("Flow Time L2 Norm:", flow_time_l2_norm)
