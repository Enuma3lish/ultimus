import numpy as np
from collections import deque
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Mlfq(jobs, num_queues=100):
    queues = [deque() for _ in range(num_queues)]
    time_quanta = [2 ** i for i in range(num_queues)]
    
    current_time = 0
    flow_times = []
    jobs_in_system = len(jobs)
    logs = []  # Initialize logs list
    
    # Convert job tuples to lists to allow modification
    jobs = [[job[0], job[1]] for job in jobs]  # Format: [arrival_time, job_size]
    jobs.sort(key=lambda x: x[0])
    job_index = 0

    while jobs_in_system > 0:
        while job_index < len(jobs) and jobs[job_index][0] <= current_time:
            queues[0].append([jobs[job_index], current_time, 0, None, False])  # Include job as list
            job_index += 1

        for i, queue in enumerate(queues):
            if queue:
                job, start_time, _, first_executed_time, _ = queue.popleft()
                quantum = min(time_quanta[i], job[1])
                
                if first_executed_time is None:
                    first_executed_time = current_time
                
                job[1] -= quantum
                current_time += quantum
                
                if job[1] == 0:
                    flow_times.append(current_time - job[0])
                    jobs_in_system -= 1
                    logs.append({'arrival_time': job[0], 'first_executed_time': first_executed_time, 'ifdone': True})
                elif i < num_queues - 1:
                    queues[i + 1].append([job, start_time, i + 1, first_executed_time, False])
                else:
                    queues[i].append([job, start_time, i, first_executed_time, False])
                
                break
        else:
            if job_index < len(jobs):
                current_time = jobs[job_index][0]
            else:
                current_time += 1

    average_flow_time = np.mean(flow_times)
    flow_time_l2_norm = np.linalg.norm(flow_times)

    return average_flow_time, flow_time_l2_norm