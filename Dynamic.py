import math
import csv
import copy
from SRPT_Selector import select_next_job as srpt_select_next_job
from FCFS_Selector import select_next_job as fcfs_select_next_job
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import csv
import math
from SRPT_Selector import select_next_job as srpt_select_next_job

def Srpt(jobs):
    current_time = 0
    completed_jobs = []
    job_queue = []
    total_jobs = len(jobs)
    jobs_pointer = 0

    # Assign job indices
    for idx, job in enumerate(jobs):
        job['job_index'] = idx

    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x['arrival_time'])

    while len(completed_jobs) < total_jobs:
        # Add jobs that arrive at the current time
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] <= current_time:
            job = jobs[jobs_pointer]
            job_copy = {
                'arrival_time': job['arrival_time'],
                'job_size': job['job_size'],
                'remaining_time': job['job_size'],
                'job_index': job['job_index'],
                'completion_time': None,
                'start_time': None
            }
            job_queue.append(job_copy)
            jobs_pointer += 1

        # Select the next job
        selected_job = srpt_select_next_job(job_queue) if job_queue else None

        # Process selected job
        if selected_job:
            job_queue.remove(selected_job)

            # Record start_time if not already set
            if selected_job['start_time'] is None:
                selected_job['start_time'] = current_time

            selected_job['remaining_time'] -= 1

            # Check if job is completed
            if selected_job['remaining_time'] == 0:
                selected_job['completion_time'] = current_time + 1  # Adjusted here
                completed_jobs.append(selected_job)
            else:
                # Re-add the job to the queue
                job_queue.append(selected_job)

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

def Fcfs(jobs):
    current_time = 0
    completed_jobs = []
    waiting_queue = []
    total_jobs = len(jobs)
    jobs_pointer = 0
    current_job = None

    # Assign job indices
    for idx, job in enumerate(jobs):
        job['job_index'] = idx

    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x['arrival_time'])

    while len(completed_jobs) < total_jobs:
        # Add jobs that arrive at the current time
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] <= current_time:
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

        # Select the next job using the FCFS selector
        if current_job is None and waiting_queue:
            current_job = fcfs_select_next_job(waiting_queue)
            if current_job:
                waiting_queue.remove(current_job)
                # Record start_time if not already set
                if current_job['start_time'] is None:
                    current_job['start_time'] = current_time

        # Process current job
        if current_job:
            current_job['remaining_time'] -= 1

            # Check if job is completed
            if current_job['remaining_time'] == 0:
                current_job['completion_time'] = current_time + 1
                completed_jobs.append(current_job)
                current_job = None

        # Increment time
        current_time += 1

    # Calculate metrics
    total_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    if total_jobs > 0:
        avg_flow_time = total_flow_time / total_jobs
        l2_norm_flow_time = (sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs))**0.5
    else:
        avg_flow_time = 0
        l2_norm_flow_time = 0

    return avg_flow_time, l2_norm_flow_time

def DYNAMIC(jobs, nJobsPerRound):
    total_jobs = len(jobs)

    # If nJobsPerRound is greater than or equal to total_jobs, use SRPT for all jobs
    # if nJobsPerRound >= total_jobs:
    #     print(f"Checkpoint ({nJobsPerRound}) >= Total jobs ({total_jobs}). Using SRPT for all jobs.")
    #     return Srpt(jobs)

    current_time = 0
    active_jobs = []
    completed_jobs = []
    n_arrival_jobs = 0
    n_completed_jobs = 0
    is_srpt_better = True  # Start with SRPT by default
    jobs_pointer = 0
    jobs_in_round = []
    current_job = None

    # Assign job indices and initialize jobs
    for idx, job in enumerate(jobs):
        job['job_index'] = idx
        job['remaining_time'] = job['job_size']
        job['completion_time'] = None

    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x['arrival_time'])

    while n_completed_jobs < total_jobs:
        # Check for new job arrivals
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] == current_time:
            job = jobs[jobs_pointer]
            job_copy = job.copy()
            active_jobs.append(job_copy)
            jobs_in_round.append(job_copy)
            n_arrival_jobs += 1
            jobs_pointer += 1

        # Checkpoint logic
        if n_arrival_jobs >= nJobsPerRound:
            if jobs_in_round:
                # Simulate SRPT and FCFS on the new jobs only
                srpt_avg, srpt_l2 = Srpt(jobs_in_round)
                fcfs_avg, fcfs_l2 = Fcfs(jobs_in_round)
                is_srpt_better = srpt_l2 <= fcfs_l2
                print(f"Checkpoint reached at total of {jobs_pointer} jobs:")
                print(f"SRPT - L2: {srpt_l2:.2f}")
                print(f"FCFS - L2: {fcfs_l2:.2f}")
                print(f"Switching to {'SRPT' if is_srpt_better else 'FCFS'}")
            jobs_in_round = []
            n_arrival_jobs = 0  # Reset the arrival counter

        # Select next job based on the current scheduling policy
        if is_srpt_better:
            # SRPT mode: preemptive scheduling
            selected_job = srpt_select_next_job(active_jobs) 
        else:
            # FCFS mode: non-preemptive scheduling
            selected_job = fcfs_select_next_job(active_jobs)

        # Process current job
        if selected_job:
            active_jobs.remove(selected_job)
            selected_job['remaining_time'] -= 1
            if selected_job['remaining_time'] == 0:
                selected_job['completion_time'] = current_time + 1
                completed_jobs.append(selected_job)
                n_completed_jobs += 1
            else:
                active_jobs.append(selected_job)            

        # Increment time
        current_time += 1

    # Calculate metrics
    total_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    if total_jobs > 0:
        avg_flow_time = total_flow_time / total_jobs
        l2_norm_flow_time = math.sqrt(sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs))
    else:
        avg_flow_time = 0
        l2_norm_flow_time = 0

    return avg_flow_time, l2_norm_flow_time
def read_jobs_from_csv(filename):
    try:
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            return [{'arrival_time': float(row['arrival_time']), 'job_size': float(row['job_size'])} for row in reader]
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return []
    except csv.Error as e:
        logger.error(f"Error reading CSV file: {e}")
        return []

# def main():
#     filename = 'data/(22, 4.073).csv'  # Replace with your input file name
#     jobs = read_jobs_from_csv(filename)
#     avg_flow_time, l2_norm = DYNAMIC(jobs, 1000)  # Set your desired checkpoint value
#     print(f"\nAverage Flow Time: {avg_flow_time}")
#     print(f"L2 Norm of Flow Time: {l2_norm}")

# if __name__ == "__main__":
#     main()
