def select_next_job(waiting_queue):
        if not waiting_queue:
            return None
        
        best_job = waiting_queue[0]
        
        for job in waiting_queue:
            if job['arrival_time'] < best_job['arrival_time']:
                best_job = job
            elif job['arrival_time'] == best_job['arrival_time']:
                if job['job_size'] < best_job['job_size']:
                    best_job = job
                elif job['job_size'] == best_job['job_size']:
                    if job['job_index'] < best_job['job_index']:
                        best_job = job
        
        return best_job