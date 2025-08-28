def select_next_job(waiting_queue):
    if not waiting_queue:
        return None

    # Initialize the first job as the best candidate
    best_job = waiting_queue[0]

    # Iterate through the waiting_queue
    for job in waiting_queue:
        # Compare arrival times
        if job['arrival_time'] < best_job['arrival_time']:
            best_job = job
        # If arrival times are equal, compare job sizes
        elif job['arrival_time'] == best_job['arrival_time'] and job['job_size'] < best_job['job_size']:
            best_job = job
        # If arrival times and job sizes are equal, compare job IDs
        elif job['arrival_time'] == best_job['arrival_time'] and job['job_size'] == best_job['job_size'] and job['job_index'] < best_job['job_index']:
            best_job = job

    return best_job