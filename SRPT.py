import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Srpt(jobs_input):
    """
    Simulates the Shortest Remaining Processing Time (SRPT) scheduling algorithm.
    
    Args:
    - jobs_input: A list of [arrival_time, job_size] for each job.
    
    Returns:
    - average_flow_time: The average flow time of all jobs.
    - l2_norm_flow_time: The L2-norm flow time of all jobs.
    - logs: A list of logs for each job, including arrival time, first executed time, and completion status.
    """
    # Initialize variables
    current_time = 0
    jobs = sorted(jobs_input, key=lambda x: x[0])  # Sort jobs by arrival time
    job_queue = []
    completed_jobs = []

    while jobs or job_queue or any(not job['completed'] for job in job_queue):
        # Add arriving jobs to the queue
        while jobs and jobs[0][0] <= current_time:
            job = jobs.pop(0)
            job_queue.append({'arrival_time': job[0], 'job_size': job[1], 'remaining_time': job[1], 'start_time': None, 'completed': False})
        
        if job_queue:
            # Select the job with the shortest remaining time
            job_queue.sort(key=lambda x: x['remaining_time'])
            current_job = job_queue[0]
            
            # Execute job
            if current_job['start_time'] is None:
                current_job['start_time'] = current_time
            current_job['remaining_time'] -= 1
            
            # Check if job is completed
            if current_job['remaining_time'] <= 0:
                current_job['completed'] = True
                completed_jobs.append(job_queue.pop(0))  # Remove completed job from queue

        current_time += 1  # Increment time

    # Calculate metrics and generate logs
    average_flow_time = sum(job['start_time'] - job['arrival_time'] + job['job_size'] for job in completed_jobs) / len(completed_jobs)
    flow_times = [job['start_time'] - job['arrival_time'] + job['job_size'] for job in completed_jobs]
    l2_norm_flow_time = np.linalg.norm(flow_times, 2)
    logs = [{'arrival_time': job['arrival_time'], 'first_executed_time': job['start_time'], 'ifdone': job['completed']} for job in completed_jobs]

    return average_flow_time, l2_norm_flow_time, logs
# jobs = Read_csv("data/(40, 4.073).csv")
# avg,l2,logs=Srpt(jobs)
# print(avg)
# print(l2)
# # print(logs)
