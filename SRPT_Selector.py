def select_next_job(job_queue):
        if not job_queue:
            return None
        best_job = job_queue[0]
        
        for job in job_queue:
            if job['remaining_time'] < best_job['remaining_time']:
                best_job = job
            elif job['remaining_time'] == best_job['remaining_time']:
                if job['arrival_time'] < best_job['arrival_time']:
                    best_job = job
                elif job['arrival_time'] == best_job['arrival_time']:
                    if job['job_index'] < best_job['job_index']:
                        best_job = job
        
        return best_job