from typing import List, Tuple
from collections import deque
from RR_Selector import RR_Selector

def RR(jobs: List, time_quantum: int = 1) -> Tuple[float, float]:
    """
    Online Round Robin scheduler that processes jobs until completion.
    
    Args:
        jobs: List of jobs (either as lists or dictionaries)
             If lists: [[arrival_time, job_size], ...]
             If dicts: [{'arrival_time': float, 'job_size': float}, ...]
        time_quantum: Time quantum for Round Robin scheduling
    
    Returns:
        Tuple of (average_flow_time, l2_norm)
    """
    # Handle input jobs format - could be list of lists or list of dicts
    if isinstance(jobs[0], dict):
        jobs_list = [[job['arrival_time'], job['job_size']] for job in jobs]
    else:
        # Already in list format
        jobs_list = jobs
    
    # Sort jobs by arrival time
    jobs_list = sorted(jobs_list, key=lambda x: x[0])
    
    total_jobs = len(jobs_list)
    current_time = 0
    
    # Track remaining jobs and their original indices
    job_info = []  # [(original_index, arrival_time, remaining_time), ...]
    for i, (arrival, size) in enumerate(jobs_list):
        job_info.append((i, arrival, size))
    
    # Queue to manage ready jobs (Round Robin order)
    ready_queue = deque()
    
    completion_times = [0] * total_jobs
    total_flow_time = 0
    l2_norm_sum = 0
    completed_jobs = 0
    
    # Process jobs until all are completed
    while completed_jobs < total_jobs:
        # Use RR_Selector to update ready queue and get the next job
        selected_job_idx, execution_time, job_selected = RR_Selector(
            job_info, current_time, ready_queue, time_quantum
        )
        
        if job_selected:
            # Job was selected, execute it
            current_time += execution_time
            remaining = ready_queue[0][1] - execution_time  # Get the remaining time after execution
            orig_idx = ready_queue[0][0]
            
            if remaining <= 0:
                # Job is completed
                ready_queue.popleft()  # Remove job from queue
                completion_times[orig_idx] = current_time
                flow_time = completion_times[orig_idx] - jobs_list[orig_idx][0]
                total_flow_time += flow_time
                l2_norm_sum += flow_time ** 2
                completed_jobs += 1
            else:
                # Job is not completed, put it back at the end of the queue
                ready_queue.popleft()  # Remove from front
                ready_queue.append((orig_idx, remaining))  # Add to back
        else:
            # No jobs ready, advance time to next arrival
            if job_info:
                current_time = max(current_time, job_info[0][1])
            else:
                break  # No more jobs to process
    
    # Calculate final metrics
    avg_flow_time = total_flow_time / total_jobs
    l2_norm = l2_norm_sum ** 0.5
    
    return avg_flow_time, l2_norm
