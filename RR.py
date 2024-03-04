import numpy as np

def round_robin_scheduling(jobs_input, time_quantum=2):
    # Initialize job details for logging and calculations
    jobs = [{'arrival_time': job[0], 'job_size': job[1], 'start_time': None, 'completion_time': None, 'remaining_size': job[1]} for job in jobs_input]
    
    # Simulation variables
    time = 0
    queue = []
    completed_jobs = 0

    # Function to add eligible jobs to the queue
    def add_to_queue(time, jobs, queue):
        for job in jobs:
            if job['arrival_time'] <= time and job not in queue and job['remaining_size'] > 0:
                queue.append(job)

    # Round-Robin Scheduling
    while completed_jobs < len(jobs):
        add_to_queue(time, jobs, queue)
        if queue:
            current_job = queue.pop(0)
            if current_job['start_time'] is None:
                current_job['start_time'] = time
            execution_time = min(time_quantum, current_job['remaining_size'])
            current_job['remaining_size'] -= execution_time
            time += execution_time
            if current_job['remaining_size'] == 0:
                current_job['completion_time'] = time
                completed_jobs += 1
            else:
                add_to_queue(time, jobs, queue)
                queue.append(current_job)  # Re-add the job at the end of the queue if not completed
        else:
            time += 1  # Increment time if no jobs are ready to run

    # Ensure all jobs have a completion time
    for job in jobs:
        if job['completion_time'] is None:
            job['completion_time'] = time  # Safeguard, but investigate why this would happen

    # Calculate metrics
    average_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in jobs) / len(jobs)
    l2_norm_flow_time = np.sqrt(sum((job['completion_time'] - job['arrival_time'])**2 for job in jobs))

    # Generate logs
    job_logs = [{'arrival_time': job['arrival_time'], 'first_executed_time': job['start_time'], 'ifdone': job['completion_time'] is not None} for job in jobs]

    return average_flow_time, l2_norm_flow_time, job_logs

# Example usage
jobs_input = [[0, 3], [2, 6], [4, 4], [6, 5], [8, 2]]
average_flow_time, l2_norm_flow_time, job_logs = round_robin_scheduling(jobs_input)
print("Average Flow Time:", average_flow_time)
print("L2-norm Flow Time:", l2_norm_flow_time)
print("Job Logs:", job_logs)
