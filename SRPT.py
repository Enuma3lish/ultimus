import csv
import math
import os
import heapq

class Job:
    def __init__(self, job_id, arrival_time, job_size):
        self.job_id = job_id         # Unique identifier for the job
        self.arrival_time = arrival_time
        self.remaining_time = job_size
        self.job_size = job_size     # Original job size for logging
        self.start_time = None
        self.end_time = None
        self.flow_time = None

    def __lt__(self, other):
        # Comparison method for heapq to sort jobs by remaining_time and arrival_time
        if self.remaining_time == other.remaining_time:
            return self.arrival_time < other.arrival_time
        return self.remaining_time < other.remaining_time

def SRPT_selector(active_jobs):
    """
    Selects the job with the smallest remaining job size from the active jobs.

    :param active_jobs: List of active Job objects.
    :return: The selected Job object to execute next.
    """
    if not active_jobs:
        return None
    # Use a min-heap to efficiently find the job with the smallest remaining time
    heapq.heapify(active_jobs)
    selected_job = heapq.heappop(active_jobs)
    return selected_job

def Srpt(file_path):
    """
    SRPT scheduling function that reads job data from a CSV file, schedules jobs using
    the Shortest Remaining Processing Time (SRPT) algorithm, and logs job details.

    :param file_path: Path to the CSV file with jobs data in the format (arrival_time, job_size)
    :return: (average_flow_time, l2_norm_flow_time)
    """
    # Read jobs from the CSV file
    jobs, filename = read_jobs_from_csv(file_path)
    total_jobs = len(jobs)
    current_time = 0
    n_completed_jobs = 0
    completed_jobs = []
    active_jobs = []  # List to store active jobs (heap)
    job_index = 0     # Index to track jobs in the job list
    current_job = None  # The job currently being processed

    # Prepare the execution log
    execution_log = []

    # Sort all jobs based on arrival time
    jobs.sort(key=lambda job: job.arrival_time)

    while n_completed_jobs < total_jobs:
        # Check for new job arrivals at current time
        while job_index < total_jobs and jobs[job_index].arrival_time <= current_time:
            heapq.heappush(active_jobs, jobs[job_index])
            job_index += 1

        # Use SRPT_selector to select the next job
        if active_jobs:
            selected_job = SRPT_selector(active_jobs)
            # If the job hasn't started yet, set the start time
            if selected_job.start_time is None:
                selected_job.start_time = current_time
                # Log the job's arrival time, first executed time, and job size
                execution_log.append([
                    selected_job.arrival_time,
                    selected_job.start_time,
                    selected_job.job_size
                ])

            # Execute the selected job for 1 time unit
            selected_job.remaining_time -= 1
            current_time += 1

            # If the job is completed, record completion
            if selected_job.remaining_time == 0:
                selected_job.end_time = current_time
                selected_job.flow_time = selected_job.end_time - selected_job.arrival_time
                completed_jobs.append(selected_job)
                n_completed_jobs += 1
            else:
                # If the job is not finished, push it back into active_jobs
                heapq.heappush(active_jobs, selected_job)
        else:
            # No jobs to process, increment current_time
            current_time += 1

    # Create the output log filename based on the input filename
    output_filename = filename.replace('.csv', '_srpt_execution_log.csv')
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
            arrival_time = int(float(row[0]))
            job_size = int(float(row[1]))
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
average_flow_time, l2_norm_flow_time = Srpt('data/(24, 7.918).csv')
print(f"Average Flow Time: {average_flow_time}")
print(f"L2 Norm Flow Time: {l2_norm_flow_time}")
