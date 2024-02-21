import numpy as np
from collections import deque
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Mlfq(jobs, num_queues=100):
    # Initialize queues and time quanta
    queues = [deque() for _ in range(num_queues)]
    time_quanta = [2 ** i for i in range(num_queues)]
    
    current_time = 0
    flow_times = []
    jobs_in_system = len(jobs)
    
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])
    job_index = 0

    while jobs_in_system > 0:
        # Enqueue newly arrived jobs in the top-level queue
        while job_index < len(jobs) and jobs[job_index][0] <= current_time:
            queues[0].append([jobs[job_index], current_time, 0])  # Job, start time, current queue level
            job_index += 1

        # Find the highest-priority non-empty queue
        for i, queue in enumerate(queues):
            if queue:
                job, start_time, _ = queue.popleft()
                quantum = min(time_quanta[i], job[1])
                job[1] -= quantum
                current_time += quantum
                
                if job[1] == 0:  # Job completed
                    flow_times.append(current_time - job[0])
                    jobs_in_system -= 1
                elif i < num_queues - 1:  # Move to next lower-priority queue
                    queues[i + 1].append([job, start_time, i + 1])
                else:  # Last queue is round-robin
                    queues[i].append([job, start_time, i])
                
                break  # Process one job at a time
        else:
            # If no jobs are available, advance time
            if job_index < len(jobs):
                current_time = jobs[job_index][0]
            else:
                current_time += 1  # Idle time

    # Calculate average flow time and flow time L2 norm
    average_flow_time = np.mean(flow_times)
    flow_time_l2_norm = np.linalg.norm(flow_times)

    return average_flow_time, flow_time_l2_norm

# Example input
jobs = Read_csv('(0.05, 16.772).csv')

# Run the MLFQ algorithm
average_flow_time, flow_time_l2_norm = Mlfq(jobs)

print("Average Flow Time:", average_flow_time)
print("Flow Time L2 Norm:", flow_time_l2_norm)
