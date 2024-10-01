# FCFS_Selector.py
def select_next_job(job_queue):
    # Select the tuple with the earliest arrival_time and lowest job_index to break ties
    selected_tuple = min(job_queue, key=lambda x: (x[0], x[1]))  # x[0] is 'arrival_time', x[1] is 'job_index'
    return selected_tuple
