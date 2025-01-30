from math import sqrt
from typing import List, Tuple
from SETF_Selector import SETFSelector

def Setf(jobs: List[Tuple[float, float]]) -> Tuple[float, float]:
    current_time = 0
    total_flow_time = 0
    squared_flow_time = 0
    completed_jobs = 0
    
    # Initialize job selector
    selector = SETFSelector()
    
    # Sort jobs by arrival time
    sorted_jobs = sorted(jobs, key=lambda x: x[0])
    n_jobs = len(sorted_jobs)
    job_pointer = 0
    
    while job_pointer < n_jobs or selector.has_active_jobs():
        # 1. Determine next event time
        next_arrival = sorted_jobs[job_pointer][0] if job_pointer < n_jobs else float('inf')
        
        # If no active jobs, jump to next arrival
        if not selector.has_active_jobs():
            current_time = next_arrival
            if job_pointer < n_jobs:
                selector.add_job(job_pointer, *sorted_jobs[job_pointer])
                job_pointer += 1
            continue
        
        # 2. Get job with shortest elapsed time
        next_job = selector.get_next_job()
        elapsed, job_id, arrival_time, size = next_job
        remaining = size - selector.job_elapsed[job_id]
        
        # 3. Determine how long to run current job
        if job_pointer < n_jobs:
            run_time = min(remaining, next_arrival - current_time)
        else:
            run_time = remaining
            
        # 4. Update job progress and time
        current_time += run_time
        selector.update_job_progress(job_id, run_time)
        
        # 5. Check if job completed
        if selector.is_job_completed(job_id, size):
            flow_time = current_time - arrival_time
            total_flow_time += flow_time
            squared_flow_time += flow_time * flow_time
            completed_jobs += 1
        else:
            selector.requeue_job(job_id, arrival_time, size)
            
        # 6. Add any new arrivals
        while job_pointer < n_jobs and sorted_jobs[job_pointer][0] <= current_time:
            selector.add_job(job_pointer, *sorted_jobs[job_pointer])
            job_pointer += 1
    
    if completed_jobs == 0:
        return 0.0, 0.0
        
    average_flow_time = total_flow_time / completed_jobs
    l2_norm_flow_time = sqrt(squared_flow_time)
    
    return average_flow_time, l2_norm_flow_time