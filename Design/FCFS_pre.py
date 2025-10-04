import pandas as pd
from math import sqrt

def Read_csv(filename):
    # Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

def Fcfs(jobs):
    """Schedules jobs using FCFS and calculates flow time metrics.

    Args:
        jobs: A list of lists where each inner list is [arrival_time, job_size].

    Returns:
        A tuple containing:
            - Average flow time
            - L2 norm of flow times
            - Schedule list of (time, job)
    """
    # Assign a job index to each job for identification
    jobs = [(arrival_time, job_size, idx) for idx, (arrival_time, job_size) in enumerate(jobs)]
    jobs.sort()  # Sort jobs by arrival time (in-place)

    current_time = 0
    flow_times = []
    schedule = []
    n = len(jobs)
    completion_times = [0] * n

    for arrival_time, job_size, job_index in jobs:
        # If the system is idle, record idle times
        if current_time < arrival_time:
            for t in range(current_time, arrival_time):
                schedule.append((t, 'Idle'))
            current_time = arrival_time  # Advance time to the arrival of the next job

        # Process the job and record the schedule
        for t in range(current_time, current_time + job_size):
            schedule.append((t, f'Job {job_index}'))
        finish_time = current_time + job_size
        flow_time = finish_time - arrival_time
        flow_times.append(flow_time)
        completion_times[job_index] = finish_time
        current_time = finish_time

    # Calculate average flow time and L2 norm
    average_flow_time = sum(flow_times) / n
    squared_flow_times = [x ** 2 for x in flow_times]
    l2_norm_flow_time = sqrt(sum(squared_flow_times))

    # Save the schedule to a CSV file
    schedule_df = pd.DataFrame(schedule, columns=['Time', 'Job'])
    schedule_df.to_csv('FCFS_schedule.csv', index=False)

    return average_flow_time, l2_norm_flow_time, schedule

# Read jobs from the CSV file
jobs = Read_csv("data/(26, 7.918).csv")
avg_flow_time, l2_norm, schedule = Fcfs(jobs)
print(f"Average Flow Time: {avg_flow_time}")
print(f"L2 Norm Flow Time: {l2_norm}")
