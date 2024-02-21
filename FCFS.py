import pandas as pd
import numpy as np
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Fcfs(processes):
    # Sort processes by arrival time
    processes.sort(key=lambda x: x[0])

    n = len(processes)
    current_time = 0
    total_flow_time = 0
    flow_time_arr = []
    for process in processes:
        arrival_time, job_size = process

        # If the current time is less than the arrival time, fast-forward the time
        if current_time < arrival_time:
            current_time = arrival_time

        # Calculate completion time for the process
        completion_time = current_time + job_size

        # Flow time is completion time minus arrival time
        flow_time = completion_time - arrival_time
        flow_time_arr.append(flow_time)
        total_flow_time += flow_time

        # Update the current time for the next process
        current_time = completion_time
    flow_time_l2_norm = np.linalg.norm(flow_time_arr)
    # Calculate average flow time
    print(f"FCFS flow time L2-norm: {flow_time_l2_norm}")
    print(f"FCFS l2 Flow Time L2 Norm:, {flow_time_l2_norm}")
    average_flow_time = total_flow_time / n
    return average_flow_time,flow_time_l2_norm