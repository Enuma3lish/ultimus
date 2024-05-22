import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Setf(jobs):
    # Convert jobs to tuples for immutability and use as dictionary keys
    jobs = [(arrival_time, job_size) for arrival_time, job_size in jobs]

    time = 0
    total_flow_time = 0
    squared_flow_time = 0
    completed_jobs = 0
    current_job = None
    remaining_jobs = []
    job_execution_start_times = {}
    job_execution_times = {job: 0 for job in jobs}  # Track the elapsed time for each job

    while jobs or current_job or remaining_jobs:
        # Move newly arrived jobs to the remaining jobs list
        while jobs and jobs[0][0] <= time:
            remaining_jobs.append(jobs.pop(0))
            if not jobs:
                break

        # Sort remaining jobs by elapsed time (job size - time run)
        if current_job:
            remaining_jobs.append(current_job)
        remaining_jobs.sort(key=lambda job: job_execution_times[job])

        if remaining_jobs:
            current_job = remaining_jobs.pop(0)
            arrival_time, job_size = current_job

            if current_job not in job_execution_start_times:
                job_execution_start_times[current_job] = time

            if jobs and jobs[0][0] < time + job_size - job_execution_times[current_job]:
                next_arrival_time = jobs[0][0]
                run_time = next_arrival_time - time
                job_execution_times[current_job] += run_time
                current_job = (arrival_time, job_size)
                time = next_arrival_time
            else:
                run_time = job_size - job_execution_times[current_job]
                job_execution_times[current_job] += run_time
                time += run_time
                flow_time = time - arrival_time
                total_flow_time += flow_time
                squared_flow_time += flow_time ** 2
                completed_jobs += 1
                current_job = None
        else:
            if jobs:
                time = jobs[0][0]

    average_flow_time = total_flow_time / completed_jobs
    l2_norm_flow_time = squared_flow_time ** 0.5

    # Ensure each job was first executed at or after its arrival time
    for job, start_time in job_execution_start_times.items():
        arrival_time, _ = job
        if start_time < arrival_time:
            raise ValueError(f"Job with arrival time {arrival_time} was first executed at {start_time}")

    return average_flow_time, l2_norm_flow_time

# jobs = Read_csv("data/(28, 4.073).csv")
# avg,l2=Setf(jobs)
# print(avg)
# print(l2)
# print(logs)