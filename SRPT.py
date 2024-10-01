import heapq
import csv
from SRPT_Selector import select_next_job  # Import the selector function

def Srpt(jobs):
    current_time = 0
    completed_jobs = []
    job_queue = []
    job_index = 0 

    jobs.sort(key=lambda x: x['arrival_time'])  # Sort jobs by arrival time

    while jobs or job_queue:
        # Add jobs that have arrived by the current time to the queue
        while jobs and jobs[0]['arrival_time'] <= current_time:
            job = jobs.pop(0)
            job['remaining_time'] = job['job_size']
            job['job_index'] = job_index 
            job_index += 1
            heapq.heappush(job_queue, (job['remaining_time'], job['arrival_time'], job['job_index'], job))

        if job_queue:
            # Select the next job based on SRPT using the selector function
            selected_tuple = select_next_job(job_queue)
            next_job = selected_tuple[3]  # Extract the job dictionary from the tuple

            # Determine the time until the next event (job completion or next job arrival)
            if jobs:
                next_arrival_time = jobs[0]['arrival_time']
                time_until_next_arrival = next_arrival_time - current_time
                time_until_completion = next_job['remaining_time']
                time_to_next_event = min(time_until_completion, time_until_next_arrival)
            else:
                time_to_next_event = next_job['remaining_time']

            current_time += time_to_next_event
            next_job['remaining_time'] -= time_to_next_event

            # If job is completed, record its completion time
            if next_job['remaining_time'] <= 0:
                next_job['completion_time'] = current_time
                completed_jobs.append(next_job)
            else:
                # Reinsert the job back into the queue with its updated remaining time
                heapq.heappush(job_queue, (next_job['remaining_time'], next_job['arrival_time'], next_job['job_index'], next_job))

        else:
            # If no jobs in the queue, advance time to the next job arrival
            if jobs:
                current_time = jobs[0]['arrival_time']
            else:
                break

    # Compute flow times
    avg_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs) / len(completed_jobs) if completed_jobs else 0
    l2_norm_flow_time = (sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs)) ** 0.5 if completed_jobs else 0

    return avg_flow_time, l2_norm_flow_time

def read_jobs_from_csv(filename):
    jobs = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file) 
        for row in reader:
            arrival_time = float(row['arrival_time'])
            job_size = float(row['job_size'])
            jobs.append({'arrival_time': arrival_time, 'job_size': job_size})
    return jobs

# Example usage with CSV file
jobs = read_jobs_from_csv('data/(28, 16.772).csv') 
avg_flow_time, l2_norm_flow_time = Srpt(jobs)
print("Average Flow Time:", avg_flow_time)
print("L2 Norm Flow Time:", l2_norm_flow_time)