import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
import heapq
from math import sqrt

class Task:
    def __init__(self, arrival_time, job_size):
        self.arrival_time = arrival_time
        self.job_size = job_size
        self.service_time = 0  # How much service time has been provided
        self.first_executed_time = None  # Track the first executed time
        self.completion_time = None  # Track the completion time

    def __lt__(self, other):
        return self.service_time < other.service_time

def Setf(tasks):
    current_time = 0
    ready_queue = []
    job_logs = []  # Logging for each job

    while tasks or ready_queue:
        # Move tasks that have arrived to the ready queue
        while tasks and tasks[0][0] <= current_time:
            task_info = tasks.pop(0)
            heapq.heappush(ready_queue, Task(*task_info))
        
        if ready_queue:
            current_task = heapq.heappop(ready_queue)
            if current_task.first_executed_time is None:
                current_task.first_executed_time = current_time

            # Simulate task running for 1 unit of time
            current_task.service_time += 1

            if current_task.service_time == current_task.job_size:
                # Task is completed
                current_task.completion_time = current_time + 1
                job_logs.append({
                    'arrival_time': current_task.arrival_time,
                    'first_executed_time': current_task.first_executed_time,
                    'completion_time': current_task.completion_time,
                    'ifdone': True
                })
            else:
                # Task needs more service time
                heapq.heappush(ready_queue, current_task)
        
        current_time += 1

    # Calculate average flow time and L2-norm flow time using job_logs
    completion_times = [log['completion_time'] - log['arrival_time'] for log in job_logs]
    average_flow_time = sum(completion_times) / len(completion_times)
    l2_norm_flow_time = sqrt(sum(x**2 for x in completion_times))

    return average_flow_time, l2_norm_flow_time, job_logs

jobs = Read_csv("data/(32, 16.772).csv")
avg,l2,logs=Setf(jobs)
print(avg)
print(l2)
# print(logs)