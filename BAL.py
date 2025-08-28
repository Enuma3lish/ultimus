import csv
import math
from SRPT_Selector import select_next_job as srpt_select_next_job
from BAL_Selector import select_starving_job

def Bal(jobs):
    current_time = 0
    completed_jobs = []
    job_queue = []
    total_jobs = len(jobs)
    jobs_pointer = 0
    starvation_threshold = total_jobs ** (2/3)
    
    # Assign job indices
    for idx, job in enumerate(jobs):
        job['job_index'] = idx
    
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x['arrival_time'])
    
    while len(completed_jobs) < total_jobs:
        # Add jobs that arrive at or before current time
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] <= current_time:
            job = jobs[jobs_pointer]
            job_copy = {
                'arrival_time': job['arrival_time'],
                'job_size': job['job_size'],
                'remaining_time': job['job_size'],
                'job_index': job['job_index'],
                'completion_time': None,
                'start_time': None,
                'starving_time': None,  # Time when job became starving
                'waiting_time_ratio': 0
            }
            job_queue.append(job_copy)
            jobs_pointer += 1
        
        # Update waiting_time_ratio for all jobs in queue
        for job in job_queue:
            if job['remaining_time'] > 0:
                job['waiting_time_ratio'] = (current_time - job['arrival_time']) / max(1, job['remaining_time'])
                # Check if job just became starving
                if job['waiting_time_ratio'] > starvation_threshold and job['starving_time'] is None:
                    job['starving_time'] = current_time
        
        # Separate starving and non-starving jobs
        starving_jobs = [job for job in job_queue if job['waiting_time_ratio'] > starvation_threshold]
        
        selected_job = None
        
        if starving_jobs:
            # Use BAL's starving job selection
            selected_job = select_starving_job(starving_jobs)
        else:
            # Use SRPT selector when no starving jobs
            selected_job = srpt_select_next_job(job_queue)
        
        # Process selected job
        if selected_job:
            job_queue.remove(selected_job)
            
            # Record start_time if not already set
            if selected_job['start_time'] is None:
                selected_job['start_time'] = current_time
            
            # Execute job for one time unit
            selected_job['remaining_time'] -= 1
            
            # Check if job is completed
            if selected_job['remaining_time'] == 0:
                selected_job['completion_time'] = current_time + 1
                completed_jobs.append(selected_job)
            else:
                # Re-add the job to the queue
                job_queue.append(selected_job)
        
        # Increment time
        current_time += 1
    
    # Calculate metrics
    total_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    if total_jobs > 0:
        avg_flow_time = total_flow_time / total_jobs
        l2_norm_flow_time = (sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs)) ** 0.5
    else:
        avg_flow_time = 0
        l2_norm_flow_time = 0
    
    return avg_flow_time, l2_norm_flow_time