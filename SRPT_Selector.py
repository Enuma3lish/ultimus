import heapq

def select_next_job(job_queue):
    if job_queue:
        # Return the entire tuple, including remaining_time, arrival_time, job_index, and job
        return heapq.heappop(job_queue)
    return None