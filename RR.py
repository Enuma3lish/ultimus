from collections import deque
import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Rr(jobs, time_quantum=1):
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])
    
    time = 0
    queue = deque()  # Queue to manage the round-robin scheduling
    job_index = 0
    flow_times = []
    
    # Continue until all jobs are processed
    while job_index < len(jobs) or queue:
        # Add jobs to the queue that have arrived
        while job_index < len(jobs) and jobs[job_index][0] <= time:
            queue.append(jobs[job_index] + [time])  # Append arrival time for flow time calculation
            job_index += 1

        if queue:
            # Pop the next job in the queue
            current_job = queue.popleft()
            # Decrease job size by time quantum and increase current time
            current_job[1] -= time_quantum
            time += time_quantum
            
            # Check if the job is completed
            if current_job[1] > 0:
                # If not, add it back to the end of the queue
                queue.append(current_job)
            else:
                # If completed, calculate the flow time and store it
                flow_time = time - current_job[0]
                flow_times.append(flow_time)
        else:
            # If no jobs are in the queue, move to the next time where a job arrives
            time = jobs[job_index][0] if job_index < len(jobs) else time + 1

    # Calculate average flow time and flow time L2 norm
    average_flow_time = np.mean(flow_times)
    flow_time_l2_norm = np.linalg.norm(flow_times)
    print(f"Rr average Flow Time: {average_flow_time}")
    print(f"Rr flow time L2-norm: {flow_time_l2_norm}")
    return average_flow_time, flow_time_l2_norm

# Example input
# jobs = Read_csv('(0.025, 16.772).csv')

# # Run the Round-Robin algorithm
# average_flow_time, flow_time_l2_norm = Rr(jobs)

# print("Average Flow Time:", average_flow_time)
# print("Flow Time L2 Norm:", flow_time_l2_norm)
