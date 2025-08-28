import heapq
import pandas as pd
import numpy as np

def Read_csv(filename):
    # Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

def Srpt(jobs):
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])
    
    n = len(jobs)
    time = 0
    total_flow_time = 0
    total_flow_time_squared = 0
    job_queue = []
    index = 0
    remaining_times = [job[1] for job in jobs]
    start_times = [-1] * n
    completion_times = [0] * n
    flow_times = []
    schedule = []
    
    while index < n or job_queue:
        # Add any jobs that arrive at current time to the job_queue
        while index < n and jobs[index][0] <= time:
            heapq.heappush(job_queue, (remaining_times[index], index))
            index += 1
        
        if job_queue:
            # Get the job with the shortest remaining processing time
            remaining_time, job_index = heapq.heappop(job_queue)
            if start_times[job_index] == -1:
                start_times[job_index] = time  # Record the first time the job is executed
            
            # Process the job for 1 time unit
            remaining_time -= 1
            remaining_times[job_index] = remaining_time
            schedule.append((time, f'Job {job_index}'))  # Record the job being processed at current time
            
            if remaining_time > 0:
                heapq.heappush(job_queue, (remaining_time, job_index))
            else:
                # Job is finished
                completion_times[job_index] = time + 1
                flow_time = completion_times[job_index] - jobs[job_index][0]
                flow_times.append(flow_time)
                total_flow_time += flow_time
                total_flow_time_squared += flow_time ** 2
        else:
            # System is idle at current time
            schedule.append((time, 'Idle'))  # Use 'Idle' to indicate idle
        time += 1
    
    # Calculate average flow time
    average_flow_time = total_flow_time / n
    # Calculate L2 norm of the flow time
    l2_norm_flow_time = total_flow_time_squared ** 0.5
    
    # Save the schedule to a CSV file
    schedule_df = pd.DataFrame(schedule, columns=['Time', 'Job'])
    schedule_df.to_csv('srpt_schedule.csv', index=False)
    
    return average_flow_time, l2_norm_flow_time, schedule

jobs = Read_csv("data/(20, 16.772).csv")
avg_flow_time, l2_norm, schedule = Srpt(jobs)
print("Average Flow Time:", avg_flow_time)
print("L2 Norm of Flow Time:", l2_norm)
