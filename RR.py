import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Rr(jobs, time_quantum=4):
    clock = 0
    queue = []
    job_logs = []
    completed_jobs = 0
    total_flow_time = 0
    flow_times = []
    
    jobs.sort(key=lambda x: x[0])  # Ensure jobs are sorted by arrival time
    job_index = 0  # To track the addition of jobs to the queue

    while completed_jobs < len(jobs) or queue:
        # Add jobs that have arrived to the queue
        while job_index < len(jobs) and jobs[job_index][0] <= clock:
            job = jobs[job_index]
            queue.append({'arrival_time': job[0], 'remaining_time': job[1], 'first_executed_time': None, 'ifdone': False})
            job_index += 1
        
        if queue:
            current_job = queue.pop(0)
            if current_job['first_executed_time'] is None:
                current_job['first_executed_time'] = clock
                
            exec_time = min(current_job['remaining_time'], time_quantum)
            clock += exec_time
            current_job['remaining_time'] -= exec_time
            
            if current_job['remaining_time'] == 0:
                current_job['ifdone'] = True
                completed_jobs += 1
                total_flow_time += clock - current_job['arrival_time']
                flow_times.append(clock - current_job['arrival_time'])
                job_logs.append(current_job)
            else:
                queue.append(current_job)
        else:
            # If no jobs in queue but still jobs to process
            if job_index < len(jobs):
                clock = jobs[job_index][0]  # Move clock to next job's arrival time
            else:
                clock += 1  # Or increment clock waiting for next job
    
    average_flow_time = total_flow_time / len(job_logs)
    l2_norm_flow_time = np.linalg.norm(flow_times, 2)

    formatted_job_logs = [{'arrival_time': job['arrival_time'],
                           'first_executed_time': job['first_executed_time'],
                           'ifdone': job['ifdone']} for job in job_logs]
    
    return average_flow_time, l2_norm_flow_time,formatted_job_logs

# jobs = Read_csv("data/(20, 4.073).csv")
# avg,l2,logs=Rr(jobs)
# print(avg)
# print(l2)
# print(logs)