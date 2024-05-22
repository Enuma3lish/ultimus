import math
import numpy as np
import pandas as pd
import random
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

def Rmlfq(jobs, num_queues=100):
    """Schedules jobs using the MLFQ algorithm with exponential distribution in first level.

    Args:
        jobs: List of [arrival_time, job_size] pairs.
        num_queues: Number of queues in the MLFQ system.

    Returns:
        Tuple of (average_flow_time, l2_norm_flow_time).
    """
    queues = [[] for _ in range(num_queues)]
    time = 0
    flow_times = []

    for j, (arrival_time, job_size) in enumerate(jobs, 1):  
        while time < arrival_time:
            for i, q in enumerate(queues):
                if q:
                    job = q[0]
                    target_time = 2 ** i * max(1, 2 - job[2])  

                    if time - job[0] + 1 >= target_time:  
                        q.pop(0)
                        if i < num_queues - 1:  
                            queues[i + 1].append(job)  # Demote
                    else:
                        job[1] -= 1  # Decrease the job size by the time it has run in the current quantum
                        if job[1] == 0: #If the job has completed running, record the flow time and remove it from the queue
                            flow_times.append(time - job[0] + 1)
                            q.pop(0)
                    break
            time += 1

        bj = 1 if j < 3 else 1 - random.expovariate(12 * math.log(j))
        queues[0].append([arrival_time, job_size, bj]) 

    while any(queues):  # Process remaining jobs
        for i, q in enumerate(queues):
            if q:
                job = q[0]
                flow_times.append(time - job[0] + 1)
                q.pop(0)
                break
        time += 1

    average_flow_time = sum(flow_times) / len(flow_times)
    l2_norm_flow_time = math.sqrt(sum(x*x for x in flow_times)) 
    return average_flow_time, l2_norm_flow_time


# Example call with the job list
jobs = Read_csv("data/(28, 4.073).csv")
average_flow_time, l2_norm_flow_time= Rmlfq(jobs)
print(average_flow_time)
print(l2_norm_flow_time)
