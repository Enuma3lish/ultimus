import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Sjf(jobs):
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])
    time = 0
    waiting_time = []
    job_logs = []
    jobs_queue = []
    
    while jobs or jobs_queue:
        # Add jobs to the queue if they have arrived
        while jobs and jobs[0][0] <= time:
            jobs_queue.append(jobs.pop(0) + [time, False])  # Add start time and completion status
        
        # Sort jobs in queue by job size
        jobs_queue.sort(key=lambda x: x[1])
        
        if jobs_queue:
            job = jobs_queue.pop(0)
            time += job[1]  # Execute the job
            flow_time = time - job[0]
            waiting_time.append(flow_time)
            job_logs.append({"arrival_time": job[0], "first_executed_time": job[2], "ifdone": True})
        else:
            time += 1  # If no jobs are ready to be executed, increment time
    
    # Calculate average flow time
    total_flow_time = sum(waiting_time)
    avg_flow_time = total_flow_time / len(waiting_time) if waiting_time else 0
    
    # Calculate L2 norm of flow time
    l2_norm_flow_time = (sum(f ** 2 for f in waiting_time)) ** 0.5
    
    return avg_flow_time, l2_norm_flow_time

# jobs = Read_csv("data/(20, 16.772).csv")
# avg,l2=Sjf(jobs)
# print(avg)
# print(l2)