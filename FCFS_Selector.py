def select_next_job(waiting_queue):
    """
    Select the next job to execute based on FCFS (First-Come, First-Served) policy.
    
    Selection criteria (in order of priority):
    1. Earliest arrival time
    2. If arrival times are equal, smallest job size
    3. If both are equal, smallest job index
    
    Args:
        waiting_queue: List of jobs waiting to be processed
        
    Returns:
        The job that should be executed next, or None if queue is empty
    """
    if not waiting_queue:
        return None
    
    best_job = waiting_queue[0]
    
    for job in waiting_queue:
        # Primary criterion: Earlier arrival time
        if job['arrival_time'] < best_job['arrival_time']:
            best_job = job
        elif job['arrival_time'] == best_job['arrival_time']:
            # Tie-breaker 1: Smaller job size
            if job['job_size'] < best_job['job_size']:
                best_job = job
            elif job['job_size'] == best_job['job_size']:
                # Tie-breaker 2: Smaller job index
                if job['job_index'] < best_job['job_index']:
                    best_job = job
    
    return best_job