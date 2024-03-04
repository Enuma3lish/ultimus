import numpy as np

def Sjf(jobs):
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])
    time = 0
    waiting_time = []
    job_logs = []
    jobs_queue = []
    
    while jobs or jobs_queue:
        # Add jobs to the queue if they have arrived
        while jobs and jobs[0][0] <= time:
            jobs_queue.append(jobs.pop(0) + [time, False])  # Add start time and completion status
        
        # Sort jobs in queue by job size
        jobs_queue.sort(key=lambda x: x[1])
        
        if jobs_queue:
            job = jobs_queue.pop(0)
            time += job[1]  # Execute the job
            waiting_time.append(time - job[0])
            job_logs.append({"arrival_time": job[0], "first_executed_time": job[2], "ifdone": True})
        else:
            time += 1  # If no jobs are ready to be executed, increment time

    # Calculate average and L2-norm of flow time
    avg_flow_time = np.mean(waiting_time)
    l2_norm_flow_time = np.linalg.norm(waiting_time)
    
    return avg_flow_time, l2_norm_flow_time, job_logs

# Example input
jobs = [[0, 3], [2, 6], [4, 1], [6, 5]]

avg_flow_time, l2_norm_flow_time, job_logs = Sjf(jobs)
print(avg_flow_time, l2_norm_flow_time, job_logs)
