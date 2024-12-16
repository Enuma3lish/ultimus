from typing import List, Tuple, Optional

def RR_Selector(jobs: List[List[int]], current_time: int, time_quantum: int = 2) -> Tuple[Optional[int], int]:
    """
    Selects the next job to execute according to Round Robin scheduling.
    
    Args:
        jobs: List of [arrival_time, job_size] pairs
        current_time: Current system time
        time_quantum: Time quantum for Round Robin
    
    Returns:
        Tuple of (selected_job_index, execution_time)
        If no job is available, returns (None, next_arrival_time)
    """
    # Find jobs that have arrived by current_time
    available_jobs = [(i, job) for i, job in enumerate(jobs) if job[0] <= current_time]
    
    if not available_jobs:
        # If no jobs available, find next arrival time
        future_jobs = [(i, job) for i, job in enumerate(jobs) if job[0] > current_time]
        if future_jobs:
            return None, min(job[1][0] for job in future_jobs)
        return None, current_time
        
    # Select the first available job
    job_index = available_jobs[0][0]
    job = available_jobs[0][1]
    
    # Calculate execution time
    execution_time = min(time_quantum, job[1])
    
    return job_index, execution_time