import numpy as np
import pandas as pd
from heapq import heapify, heappush, heappop
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Bal(jobs):
    jobs.sort(key=lambda x: x[0])
    n = len(jobs)
    current_time = 0
    queue = []
    job_index = 0
    flow_times = [0] * n
    logs = [{} for _ in range(n)]  # Initialize logs for each job
    starvation_threshold = n ** (2/3)
    
    while job_index < n or queue:
        if not queue:
            current_time = max(current_time, jobs[job_index][0])
        
        while job_index < n and jobs[job_index][0] <= current_time:
            heappush(queue, (jobs[job_index][1], jobs[job_index][0], job_index, 0))
            if job_index not in logs:  # Initialize log if not already done
                logs[job_index] = {'arrival_time': jobs[job_index][0], 'first_executed_time': None, 'ifdone': False}
            job_index += 1

        new_queue = []
        for remaining_time, arrival_time, index, _ in queue:
            waiting_time_ratio = (current_time - arrival_time) / max(1, remaining_time)
            heappush(new_queue, (remaining_time, arrival_time, index, waiting_time_ratio))
        queue = new_queue
        
        starving_job = None
        for job in queue:
            if job[3] > starvation_threshold:
                starving_job = job
                break
        
        if starving_job:
            queue.remove(starving_job)
            selected_job = starving_job
        else:
            queue.sort(key=lambda x: (x[0], x[3]))
            selected_job = queue.pop(0)
        
        remaining_time, arrival_time, index, _ = selected_job
        # Log first execution time
        if logs[index]['first_executed_time'] is None:
            logs[index]['first_executed_time'] = current_time
        current_time += remaining_time
        flow_times[index] = current_time - arrival_time
        logs[index]['ifdone'] = True  # Mark job as done
        
        queue = [(rem_time, arr_time, idx, wtr) for rem_time, arr_time, idx, wtr in queue]
        heapify(queue)
    
    average_flow_time = sum(flow_times) / n
    l2_norm_flow_time = (sum(x**2 for x in flow_times) ** 0.5)  # np.sqrt(np.sum(np.square(flow_times))) simplified
    
    return average_flow_time, l2_norm_flow_time, logs


# Example input and running the function
# jobs = Read_csv("data/(40, 16.772).csv")
# average_flow_time, l2_norm_flow_time,logs= Bal(jobs)

# print(average_flow_time)
# print(l2_norm_flow_time)
# print(logs)