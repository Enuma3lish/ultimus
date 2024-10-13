def select_next_job(job_queue):
    if not job_queue:
        return None

    # Initialize the first job as the best candidate
    best_job = job_queue[0]

    # Iterate through the job_queue
    for job in job_queue:
        # Compare remaining times (job size)
        if job['remaining_time'] < best_job['remaining_time']:
            best_job = job
        # If remaining times are equal, compare arrival times
        elif job['remaining_time'] == best_job['remaining_time'] and job['arrival_time'] < best_job['arrival_time']:
            best_job = job
        # If remaining times and arrival times are equal, compare job IDs
        elif job['arrival_time'] == best_job['arrival_time'] and job['job_index'] == best_job['job_index'] and job['job_index'] < best_job['job_index']:
            best_job = job

    return best_job