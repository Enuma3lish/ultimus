import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Prmlfq(jobs_input):
    def generate_beta(j):
        u = np.random.uniform(0, 1)
        x = -np.log(1 - u) / (τ * np.log(j))
        return x

    def calculate_time_quantum(i, beta_j):
        return 2**i * max(1, 2 - beta_j)
    
    τ = 12
    jobs = sorted([(j[0], j[1], idx) for idx, j in enumerate(jobs_input)], key=lambda x: x[0])
    n = len(jobs)
    completion_times = [0] * n
    i_values = [0] * n  # Track the power of 2 multiplier for each job
    job_logs = {idx: [] for idx in range(n)}  # Dictionary to record execution logs for each job

    # Initialize metrics
    total_flow_time = 0

    # Simulate job execution
    current_time = 0
    while jobs:
        # Check if the next job has arrived; if not, move to the next job's arrival time
        if jobs[0][0] > current_time:
            current_time = jobs[0][0]

        arrival_time, job_size, index = jobs.pop(0)

        # Generate βj
        beta_j = generate_beta(index + 3)  # Assuming j starts from 3

        # Calculate initial time quantum
        time_quantum = calculate_time_quantum(i_values[index], beta_j)

        while job_size > 0:
            execute_time = min(time_quantum, job_size)
            job_logs[index].append({'start_time': current_time, 'execute_time': execute_time})
            current_time += execute_time
            job_size -= execute_time

            # Update time quantum if job is unfinished
            if job_size > 0:
                i_values[index] += 1
                time_quantum = calculate_time_quantum(i_values[index], beta_j)

        completion_times[index] = current_time
        total_flow_time += (completion_times[index] - arrival_time)

    # Calculate metrics
    average_flow_time = total_flow_time / n
    flow_times = [completion_times[i] - jobs_input[i][0] for i in range(n)]
    l2_norm_flow_time = np.linalg.norm(flow_times, 2)

    return average_flow_time, l2_norm_flow_time, job_logs

# Re-executing the combined function with the example jobs list
jobs = Read_csv('data/(20, 16.772).csv')
# Run the SRPT algorithm
average_flow_time, flow_time_l2_norm,log= Prmlfq(jobs)

# print("Arrival log",arrival_log)
print("work log",log)
print("Average Flow Time:", average_flow_time)
print("Flow Time L2 Norm:", flow_time_l2_norm)
