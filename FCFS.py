import csv
from FCFS_Selector import select_next_job

def Fcfs(jobs):
    current_time = 0
    completed_jobs = []
    waiting_queue = []
    next_arrival_index = 0
    total_jobs = len(jobs)
    job_index = 0  # Initialize job_index

    # Ensure jobs is a list of dictionaries and sort by 'arrival_time'
    jobs.sort(key=lambda x: x['arrival_time'])

    while len(completed_jobs) < total_jobs:
        # Add new arrivals to the waiting queue
        while next_arrival_index < total_jobs and jobs[next_arrival_index]['arrival_time'] <= current_time:
            job = jobs[next_arrival_index]
            job['remaining_time'] = job['job_size']
            job['start_time'] = None
            job['completion_time'] = None
            job['job_index'] = job_index  # Assign job_index
            job_index += 1
            # Add job as a tuple: (arrival_time, job_index, job)
            waiting_queue.append((job['arrival_time'], job['job_index'], job))
            next_arrival_index += 1

        if waiting_queue:
            # Select the next job to process using select_next_job
            next_job_tuple = select_next_job(waiting_queue)
            next_job = next_job_tuple[2]  # Extract the job dictionary from the tuple
            if next_job['start_time'] is None:
                next_job['start_time'] = current_time
            next_job['remaining_time'] -= 1
            if next_job['remaining_time'] <= 0:
                next_job['completion_time'] = current_time + 1
                completed_jobs.append(next_job)
                waiting_queue.remove(next_job_tuple)  # Remove the entire tuple from the queue
        else:
            # No jobs in queue; advance current_time to next job arrival
            if next_arrival_index < total_jobs:
                current_time = jobs[next_arrival_index]['arrival_time']
            else:
                break  # All jobs are processed

        current_time += 1

    # Compute flow times
    flow_times = [job['completion_time'] - job['arrival_time'] for job in completed_jobs]
    avg_flow_time = sum(flow_times) / len(flow_times) if completed_jobs else 0
    l2_norm_flow_time = (sum(flow_time ** 2 for flow_time in flow_times)) ** 0.5 if completed_jobs else 0

    return avg_flow_time, l2_norm_flow_time

def read_jobs_from_csv(filename):
    jobs = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)  # Use DictReader to read CSV into dictionaries
        for row in reader:
            arrival_time = float(row['arrival_time'])
            job_size = float(row['job_size'])
            jobs.append({'arrival_time': arrival_time, 'job_size': job_size})
    return jobs

# Example usage with CSV file
jobs = read_jobs_from_csv('data/(28, 16.772).csv')
avg_flow_time, l2_norm_flow_time = Fcfs(jobs)
print("Average Flow Time:", avg_flow_time)
print("L2 Norm Flow Time:", l2_norm_flow_time)
