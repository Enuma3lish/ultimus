
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

from math import sqrt

def Fcfs(jobs):
    """Schedules jobs using FCFS and calculates flow time metrics.

    Args:
        jobs: A list of lists where each inner list is [arrival_time, job_size].

    Returns:
        A tuple containing:
            - Average flow time
            - L2 norm of flow times
    """
    jobs.sort()  # Sort jobs by arrival time (in-place)

    current_time = 0
    flow_times = []

    for arrival_time, job_size in jobs:
        if current_time < arrival_time:
            current_time = arrival_time  # Advance time if the system would be idle
        finish_time = current_time + job_size
        flow_time = finish_time - arrival_time
        flow_times.append(flow_time)
        current_time = finish_time 

    average_flow_time = sum(flow_times) / len(jobs)

    squared_flow_times = [x ** 2 for x in flow_times]
    l2_norm_flow_time = sqrt(sum(squared_flow_times))

    return average_flow_time, l2_norm_flow_time
jobs = Read_csv("data/(32, 16.772).csv")
avg,l2=Fcfs(jobs)
print(f"Average Flow Time: {avg}")
print(f"L2 Norm Flow Time: {l2}")
# print(logs)
