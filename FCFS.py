import math
import csv
from FCFS_Selector import select_next_job
import time

def create_log_file():
    with open('FCFS_time_slot_log.csv', 'w', newline='') as log_file:
        log_writer = csv.writer(log_file)
        log_writer.writerow(['time_slot', 'executed_job_id'])

def log_execution(time_slot, job_id=None):
    with open('FCFS_time_slot_log.csv', 'a', newline='') as log_file:
        log_writer = csv.writer(log_file)
        log_writer.writerow([time_slot, '' if job_id is None else job_id])

def Fcfs(jobs):
    current_time = 0
    completed_jobs = []
    waiting_queue = []
    total_jobs = len(jobs)
    jobs_pointer = 0
    current_job = None

    # Create log file
    create_log_file()

    # Assign job indices
    for idx, job in enumerate(jobs):
        job['job_index'] = idx

    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x['arrival_time'])

    while len(completed_jobs) < total_jobs:
        # Add jobs that arrive at the current time
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] == current_time:
            job = jobs[jobs_pointer]
            # Copy job to avoid modifying the original
            job_copy = {
                'arrival_time': job['arrival_time'],
                'job_size': job['job_size'],
                'remaining_time': job['job_size'],
                'job_index': job['job_index'],
                'completion_time': None,
                'start_time': None
            }
            waiting_queue.append(job_copy)
            jobs_pointer += 1

        # Select the next job using the select_next_job function
        if waiting_queue:
            current_job = select_next_job(waiting_queue)
            if current_job:
                waiting_queue.remove(current_job)
                # Record start_time if not already set
                if current_job['start_time'] is None:
                    current_job['start_time'] = current_time

        # Process current job and log execution
        if current_job:
            # Log the execution with the job's index
            log_execution(current_time, current_job['job_index'])
            
            current_job['remaining_time'] -= 1

            # Check if job is completed
            if current_job['remaining_time'] == 0:
                current_job['completion_time'] = current_time + 1
                print(current_job)
                completed_jobs.append(current_job)
                current_job = None
            else:
                waiting_queue.append(current_job)
        else:
            # Log empty time slot
            log_execution(current_time)

        # Increment time
        current_time += 1

    # Calculate metrics
    total_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    if total_jobs > 0:
        avg_flow_time = total_flow_time / total_jobs
        l2_norm_flow_time = (sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs)) ** 0.5
    else:
        avg_flow_time = 0
        l2_norm_flow_time = 0

    return avg_flow_time, l2_norm_flow_time

def read_jobs_from_csv(filename):
    jobs = []
    try:
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                arrival_time = float(row['arrival_time'])
                job_size = float(row['job_size'])
                jobs.append({'arrival_time': arrival_time, 'job_size': job_size})
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except csv.Error as e:
        print(f"Error reading CSV file: {e}")
    return jobs

# def main():
#     filename = 'data/(30, 7.918).csv'
#     #filename = 'data/(22, 16.772).csv'
#     jobs = read_jobs_from_csv(filename)
#     if jobs:
#         avg_flow_time, l2_norm = Fcfs(jobs)
#         print(f"Average Flow Time: {avg_flow_time}")
#         print(f"L2 Norm of Flow Time: {l2_norm}")
#         # Run the checker
#         # from Checker import Checker
#         # result = Checker(filename, 'FCFS_time_slot_log.csv')
#         # print(f"Checker result: {result}")
#     else:
#         print("No jobs were loaded. Please check the input file.")

# if __name__ == "__main__":
#     main()