import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Setf(jobs):
    """
    Perform Shortest Elapsed Time First (SETF) scheduling on a list of jobs.

    Parameters:
    - jobs: List of [arrival_time, job_size] for each job.

    Returns:
    - average_flow_time: The average flow time of the jobs.
    - l2_norm_flow_time: The L2-norm flow time of the jobs.
    - job_logs: A list of dictionaries, each containing the log of a job.
    """
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])

    # Initialize variables
    time = 0
    job_logs = []
    total_flow_time = 0
    flow_times_squared = []

    while jobs:
        # Filter jobs that have arrived
        available_jobs = [job for job in jobs if job[0] <= time]

        if available_jobs:
            # Select the job with the shortest remaining time
            shortest_job = min(available_jobs, key=lambda x: x[1])
            jobs.remove(shortest_job)
            
            # Execute the job
            start_time = max(shortest_job[0], time)
            completion_time = start_time + shortest_job[1]
            time = completion_time

            # Log job details
            job_logs.append({
                'arrival_time': shortest_job[0],
                'first_executed_time': start_time,
                'completion_time': completion_time,
                'ifdone': True
            })

            # Update metrics
            flow_time = completion_time - shortest_job[0]
            total_flow_time += flow_time
            flow_times_squared.append(flow_time**2)
        else:
            # If no jobs are available, advance time to the next job's arrival
            time = min(jobs, key=lambda x: x[0])[0]

    # Calculate metrics
    average_flow_time = total_flow_time / len(job_logs)
    l2_norm_flow_time = np.sqrt(sum(flow_times_squared))

    return average_flow_time, l2_norm_flow_time, job_logs
# jobs = Read_csv("data/(20, 4.073).csv")
# avg,l2,logs=Setf(jobs)
# print(avg)
# print(l2)
# print(logs)