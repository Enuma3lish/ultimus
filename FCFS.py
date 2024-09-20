import csv
import math
import os

class Job:
    def __init__(self, job_id, arrival_time, job_size):
        self.job_id = job_id         # Unique identifier for the job
        self.arrival_time = arrival_time
        self.remaining_time = job_size
        self.job_size = job_size     # Original job size for logging
        self.start_time = None
        self.end_time = None
        self.flow_time = None

def FCFS_Selector(active_jobs):
    """
    Selects the job with the earliest arrival time from the active jobs.

    :param active_jobs: List of active Job objects.
    :return: The selected Job object to execute next.
    """
    if not active_jobs:
        return None
    # Select the job with the earliest arrival time
    selected_job = min(active_jobs, key=lambda job: job.arrival_time)
    return selected_job

def Fcfs(file_path):
    """
    FCFS scheduling function that reads job data from a CSV file, schedules jobs using
    the First-Come-First-Serve (FCFS) algorithm (non-preemptive), and logs job details.

    :param file_path: Path to the CSV file with jobs data in the format (arrival_time, job_size)
    :return: (average_flow_time, l2_norm_flow_time)
    """
    # Read jobs from the CSV file
    jobs, filename = read_jobs_from_csv(file_path)
    total_jobs = len(jobs)
    current_time = 0
    n_completed_jobs = 0
    completed_jobs = []
    active_jobs = []  # List to store active jobs
    job_index = 0     # Index to track jobs in the job list
    current_job = None  # The job currently being processed

    # Prepare the execution log
    execution_log = []

    # Sort all jobs based on arrival time
    jobs.sort(key=lambda job: job.arrival_time)

    while n_completed_jobs < total_jobs:
        # Check for new job arrivals at current time
        while job_index < total_jobs and jobs[job_index].arrival_time <= current_time:
            active_jobs.append(jobs[job_index])
            job_index += 1

        if current_job:
            # Continue processing current_job to completion
            process_time = current_job.remaining_time

            # While processing current_job, check for new job arrivals
            for _ in range(process_time):
                current_time += 1
                current_job.remaining_time -= 1

                # Check for new arrivals at current_time
                while job_index < total_jobs and jobs[job_index].arrival_time == current_time:
                    active_jobs.append(jobs[job_index])
                    job_index += 1

            # Job completed
            current_job.end_time = current_time
            current_job.flow_time = current_job.end_time - current_job.arrival_time
            completed_jobs.append(current_job)
            n_completed_jobs += 1
            current_job = None
        else:
            # No current job, select a new one
            selected_job = FCFS_Selector(active_jobs)
            if selected_job:
                current_job = selected_job
                active_jobs.remove(current_job)
                if current_job.start_time is None:
                    current_job.start_time = current_time
                    # Log the job's arrival time, first executed time, and job size
                    execution_log.append([
                        current_job.arrival_time,
                        current_job.start_time,
                        current_job.job_size
                    ])
            else:
                # No jobs to process, increment current_time
                current_time += 1
                # Check for new arrivals at current_time
                while job_index < total_jobs and jobs[job_index].arrival_time == current_time:
                    active_jobs.append(jobs[job_index])
                    job_index += 1

    # Create the output log filename based on the input filename
    output_filename = filename.replace('.csv', '_fcfs_execution_log.csv')
    output_filepath = os.path.join('log', output_filename)

    # Record the execution log
    save_execution_log(output_filepath, execution_log)

    # Calculate average flow time and L2 norm flow time
    average_flow_time = calculate_average_flow_time(completed_jobs)
    l2_norm_flow_time = calculate_l2_norm_flow_time(completed_jobs)

    # Return the calculated values
    return average_flow_time, l2_norm_flow_time

def calculate_average_flow_time(completed_jobs):
    total_flow_time = sum(job.flow_time for job in completed_jobs)
    return total_flow_time / len(completed_jobs)

def calculate_l2_norm_flow_time(completed_jobs):
    squared_flow_times = sum(job.flow_time ** 2 for job in completed_jobs)
    return math.sqrt(squared_flow_times)

def read_jobs_from_csv(file_path):
    jobs = []
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row
        job_id = 1
        for row in reader:
            arrival_time = int(row[0])
            job_size = int(row[1])
            jobs.append(Job(job_id, arrival_time, job_size))
            job_id += 1
    return jobs, os.path.basename(file_path)  # Return jobs and the filename

def save_execution_log(output_filename, log_data):
    """
    Save the job execution log to a CSV file in the format (arrival_time, first_executed_time, job_size).

    :param output_filename: The path to the CSV log file.
    :param log_data: A list of log entries with job details.
    """
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)  # Ensure the log directory exists
    with open(output_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["arrival_time", "first_executed_time", "job_size"])  # CSV header
        writer.writerows(log_data)
    print(f"Execution log saved to {output_filename}")

# Example usage
average_flow_time, l2_norm_flow_time = Fcfs('data/(24, 7.918).csv')
print(f"Average Flow Time: {average_flow_time}")
print(f"L2 Norm Flow Time: {l2_norm_flow_time}")
