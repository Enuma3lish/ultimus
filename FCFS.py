import numpy as np

def simulate_fcfs(jobs):
    time = 0  # Current time
    job_logs = []  # Logs for each job
    flow_times = []  # Store flow times for each job to calculate metrics
    
    for job in jobs:
        arrival_time, job_size = job
        if time < arrival_time:
            time = arrival_time  # Wait for job to arrive if there is idle time
        first_executed_time = time
        time += job_size  # Update current time after job is done
        flow_time = time - arrival_time
        flow_times.append(flow_time)  # Add flow time for this job
        
        # Log for this job
        job_logs.append({
            'arrival_time': arrival_time,
            'first_executed_time': first_executed_time,
            'ifdone': True
        })
    
    # Calculate average flow time and L2-norm flow time
    avg_flow_time = np.mean(flow_times)
    l2_norm_flow_time = np.linalg.norm(flow_times)
    
    return avg_flow_time, l2_norm_flow_time, job_logs

# Example jobs input: [[arrival_time, job_size], ...]
jobs = [[0, 3], [2, 6], [4, 4], [6, 5]]

avg_flow_time, l2_norm_flow_time, job_logs = simulate_fcfs(jobs)
print(avg_flow_time,l2_norm_flow_time,job_logs)
