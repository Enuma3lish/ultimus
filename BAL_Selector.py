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