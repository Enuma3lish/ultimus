def select_starving_job(starving_jobs):
    """
    Select the starving job based on BAL criteria:
    1. Job that became starving first (smallest ti - the time when job became starving)
    2. Ties broken by largest waiting_time_ratio (γi)
    3. Further ties broken by smallest job index
    
    Args:
        starving_jobs: List of jobs that are currently starving
                      Each job should have 'starving_time', 'waiting_time_ratio', and 'job_index'
    
    Returns:
        The selected starving job or None if list is empty
    """
    if not starving_jobs:
        return None
    
    # Initialize the first job as the best candidate
    best_job = starving_jobs[0]
    
    # Iterate through starving jobs
    for job in starving_jobs:
        # Compare ti (time when job became starving) - choose earliest
        if job['starving_time'] < best_job['starving_time']:
            best_job = job
        # If ti are equal, compare waiting_time_ratio (γi) - choose largest
        elif (job['starving_time'] == best_job['starving_time'] and 
              job['waiting_time_ratio'] > best_job['waiting_time_ratio']):
            best_job = job
        # If both are equal, compare job index - choose smallest
        elif (job['starving_time'] == best_job['starving_time'] and 
              job['waiting_time_ratio'] == best_job['waiting_time_ratio'] and 
              job['job_index'] < best_job['job_index']):
            best_job = job
    
    return best_job

import heapq

def select_starving_job_optimized(starving_jobs):
    """
    Optimized BAL selector using a heap.
    Priority (min-heap):
      1) earliest starving_time
      2) largest waiting_time_ratio (so we push negative for max)
      3) smallest job_index
    Returns a job dict from the input list (not removed from the original list).
    """
    if not starving_jobs:
        return None
    if len(starving_jobs) <= 10:
        return select_starving_job(starving_jobs)
    heap = []
    for j in starving_jobs:
        heap.append((j.get('starving_time', 0), -float(j.get('waiting_time_ratio', 0)), int(j.get('job_index', 0)), j))
    heapq.heapify(heap)
    return heapq.heappop(heap)[-1]
