import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

import numpy as np

def Smlfq(jobs):
    """
    Simulate a Modified Multilevel Feedback Queue (MLFQ) with 100 queues, where at each execution cycle,
    the system calculates the total service time for each job within each queue. The job from the queue with the smallest
    total service time is executed. If the job in this period is not finished, it will be placed into the next level of the queue.
    This version includes logging of job execution details.
    
    Parameters:
    - jobs: A list of [arrival_time, job_size] for each job.
    
    Returns:
    - average_flow_time: The average flow time of the jobs.
    - l2_norm_flow_time: The L2-norm flow time of the jobs.
    - job_logs: A list of logs with execution details for each job.
    """
    num_queues = 100
    queues = [[] for _ in range(num_queues)]
    time = 0
    completed_jobs = []
    job_service_times = [0] * len(jobs)
    job_remaining_times = [job[1] for job in jobs]  # Time remaining for job completion
    first_executed_times = [None] * len(jobs)
    job_logs = []

    while len(completed_jobs) < len(jobs) or any(queue for queue in queues if queue):
        # Add arriving jobs to the highest priority queue
        for job_id, job in enumerate(jobs):
            if job[0] == time and job_id not in sum(queues, []):  # Prevent re-queuing jobs
                queues[0].append(job_id)
        
        # Calculate total service time for each queue
        queue_service_times = [sum(job_remaining_times[job_id] for job_id in queue) for queue in queues]
        
        # Find the queue with the smallest total service time that is not empty
        queue_indices = [i for i, queue in enumerate(queues) if queue]
        if not queue_indices:  # Skip if all queues are empty
            time += 1
            continue

        selected_queue_index = min(queue_indices, key=lambda i: queue_service_times[i])
        job_id = queues[selected_queue_index][0]  # Always pick the first job in the queue
        
        # Mark the first execution time if it has not been set
        if first_executed_times[job_id] is None:
            first_executed_times[job_id] = time
        
        job_remaining_times[job_id] -= 1
        job_service_times[job_id] += 1

        if job_remaining_times[job_id] == 0:
            # Job completed
            completed_jobs.append(job_id)
            completion_time = time + 1
            job_logs.append({
                'arrival_time': jobs[job_id][0],
                'first_executed_time': first_executed_times[job_id],
                'completion_time': completion_time,
                'ifdone': True
            })
            queues[selected_queue_index].pop(0)  # Remove completed job from queue
        else:
            # Move the job to the next level if not completed
            queues[selected_queue_index].pop(0)  # Remove from current queue
            next_level = min(selected_queue_index + 1, num_queues - 1)  # Ensure it doesn't exceed the max queue level
            queues[next_level].append(job_id)
        
        time += 1

    # Calculate metrics
    flow_times = [log['completion_time'] - log['arrival_time'] for log in job_logs]
    average_flow_time = np.mean(flow_times)
    l2_norm_flow_time = np.linalg.norm(flow_times)

    return average_flow_time, l2_norm_flow_time, job_logs

# jobs = Read_csv("data/(32, 16.772).csv")
# avg,l2,logs=Smlfq(jobs)
# print(avg)
# print(l2)
# print(logs)