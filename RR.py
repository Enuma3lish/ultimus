from collections import deque
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

def Rr(jobs, time_quantum=1):
    # Sort jobs by arrival time
    jobs = sorted(jobs, key=lambda x: x[0])
    n = len(jobs)
    queue = deque()
    current_time = 0
    total_flow_time = 0
    l2_norm_sum = 0

    i = 0
    while i < n or queue:
        # Add jobs that have arrived by the current time to the queue
        while i < n and jobs[i][0] <= current_time:
            queue.append(jobs[i])
            i += 1

        if queue:
            job = queue.popleft()
            arrival_time, job_size = job
            execution_time = min(time_quantum, job_size)
            # Ensure the job starts no earlier than its arrival time
            start_time = max(current_time, arrival_time)
            current_time = start_time + execution_time
            remaining_time = job_size - execution_time

            if remaining_time > 0:
                queue.append([arrival_time, remaining_time])
            else:
                flow_time = current_time - arrival_time
                total_flow_time += flow_time
                l2_norm_sum += flow_time ** 2
        else:
            # If the queue is empty, jump to the next job's arrival time
            if i < n:
                current_time = jobs[i][0]

    average_flow_time = total_flow_time / n
    l2_norm = l2_norm_sum ** 0.5

    return average_flow_time, l2_norm
jobs = Read_csv("data/(20, 16.772).csv")
avg,l2=Rr(jobs)
print(avg)
print(l2)