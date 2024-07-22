import random
import pandas as pd
from collections import deque
import math
import re
import csv

def extract_second_number_from_filename(filename):
    """Extract the second number from the filename."""
    match = re.search(r'\((\d+),\s*([\d.]+)\)', filename)
    if match:
        return float(match.group(2))
    return None

def Read_csv(filename):
    """Read the CSV file into a DataFrame and convert it to a list of lists."""
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

def calculate_Bj(j, level):
    """Calculate Bj based on the index of the job (j) and the level."""
    if j < 3:
        return 5
    else:
        return 4**(level+1)*max(5, 6 - random.expovariate(12 * math.log(j)))

def get_execution_time(level, Bj):
    """Determine execution time at level given the Bj."""
    try:
        result = Bj
        # Cap the result to avoid overflow
        result = min(result, 1e12)
        return result
    except OverflowError:
        return 1e12  # Return a large but safe value in case of overflow

def calculate_starvation_threshold(min_finished_job_size, level):
    """Calculate the starvation threshold for a job in a queue level."""
    thr = min_finished_job_size
    if level <= 2:
        return thr**0.5
    else:
        thr = pow(2, 14)**level
        return thr

def detect_starvation(job_logs, queues, current_time):
    """Detect starvation based on waiting time threshold."""
    starvation_jobs = []
    for i, queue in enumerate(queues[1:], start=1):  # Skip the first queue
        for job_id, remaining_size, arrival_time, waiting_time in queue:
            threshold = job_logs[job_id]['starvation_threshold']
            if waiting_time >= threshold:
                job_logs[job_id]['is_starved'] = True
                job_logs[job_id]['starvation_count'] += 1
                starvation_jobs.append((i, job_id, remaining_size, arrival_time, waiting_time))
    return starvation_jobs

def calculate_min_job_size(finished_job_sizes):
    """Calculate the minimum job size of finished jobs."""
    if len(finished_job_sizes) == 0:
        return float('inf')
    return min(finished_job_sizes)

def Rmlfq_aFCFS(jobs, second_number, num_queues=100):
    # Initialize data structures
    queues = [deque() for _ in range(num_queues)]
    job_logs = {i: {'arrival_time': job[0], 'first_executed_time': None, 'ifdone': False, 'waiting_time': 0, 'starvation_threshold': None, 'finished_time': None, 'finished_queue': None, 'scheduling_queue': None, 'job_size': job[1], 'finish_threshold': None, 'finish_level': None, 'is_starved': False, 'starvation_count': 0} for i, job in enumerate(jobs)}
    flow_times = []
    finished_job_sizes = []
    current_time = 0

    # Initialize a dictionary to keep track of the number of jobs finished in each queue
    finished_jobs_distribution = {i: 0 for i in range(num_queues)}

    # Sort jobs by arrival time and enqueue in the first queue
    jobs = sorted(jobs, key=lambda x: x[0])
    next_job_index = 0
    job_completion_order = []

    while next_job_index < len(jobs) or any(queues):
        # Enqueue jobs that have now arrived
        while next_job_index < len(jobs) and jobs[next_job_index][0] <= current_time:
            job_id = next_job_index
            job_size = jobs[next_job_index][1]
            arrival_time = jobs[next_job_index][0]
            job_logs[job_id]['starvation_threshold'] = 0  # Initial threshold
            queues[0].append((job_id, job_size, arrival_time, 0))
            next_job_index += 1

        # Detect starvation (excluding the first queue)
        starvation_jobs = detect_starvation(job_logs, queues, current_time)

        while starvation_jobs:
            # Process the lowest index starvation queue
            starvation_jobs.sort()
            starvation_level = starvation_jobs[0][0]

            while queues[starvation_level]:
                job_id, remaining_size, arrival_time, waiting_time = queues[starvation_level].popleft()
                job_logs[job_id]['scheduling_queue'] = starvation_level
                if job_logs[job_id]['first_executed_time'] is None:
                    job_logs[job_id]['first_executed_time'] = current_time
                Bj = calculate_Bj(job_id, starvation_level)
                executed_time = min(remaining_size, get_execution_time(starvation_level, Bj))
                remaining_size -= executed_time
                current_time += executed_time
                job_logs[job_id]['waiting_time'] = current_time - arrival_time - (jobs[job_id][1] - remaining_size)
                if remaining_size <= 0:
                    job_logs[job_id]['ifdone'] = True
                    job_logs[job_id]['finished_time'] = current_time
                    job_logs[job_id]['finished_queue'] = starvation_level
                    job_logs[job_id]['finish_threshold'] = job_logs[job_id]['starvation_threshold']
                    job_logs[job_id]['finish_level'] = starvation_level
                    flow_times.append(current_time - arrival_time)
                    finished_job_sizes.append(jobs[job_id][1])
                    job_completion_order.append(job_id)
                    # Update the finished jobs distribution
                    finished_jobs_distribution[starvation_level] += 1
                else:
                    next_queue = min(starvation_level + 1, num_queues - 1)
                    min_finished_job_size = calculate_min_job_size(finished_job_sizes) if finished_job_sizes else 1
                    new_threshold = calculate_starvation_threshold(min_finished_job_size, next_queue)
                    job_logs[job_id]['starvation_threshold'] = new_threshold
                    queues[next_queue].append((job_id, remaining_size, arrival_time, waiting_time + executed_time))

            # Re-detect starvation after handling the current starvation queue
            starvation_jobs = detect_starvation(job_logs, queues, current_time)

        # Check if the first queue is not empty
        if queues[0]:
            i = 0
        else:
            # Find the next queue with jobs
            i = next((index for index, queue in enumerate(queues) if queue), None)
            if i is None:
                current_time += 1
                continue

        # Process jobs from the first queue or next available queue
        if queues[i]:
            job_id, remaining_size, arrival_time, waiting_time = queues[i].popleft()
            job_logs[job_id]['scheduling_queue'] = i
            if job_logs[job_id]['first_executed_time'] is None:
                job_logs[job_id]['first_executed_time'] = current_time
            # Execute job
            Bj = calculate_Bj(job_id, i)
            executed_time = min(remaining_size, get_execution_time(i, Bj))
            remaining_size -= executed_time
            current_time += executed_time
            job_logs[job_id]['waiting_time'] = current_time - arrival_time - (jobs[job_id][1] - remaining_size)
            if remaining_size <= 0:
                job_logs[job_id]['ifdone'] = True
                job_logs[job_id]['finished_time'] = current_time
                job_logs[job_id]['finished_queue'] = i
                job_logs[job_id]['finish_threshold'] = job_logs[job_id]['starvation_threshold']
                job_logs[job_id]['finish_level'] = i
                flow_times.append(current_time - arrival_time)
                finished_job_sizes.append(jobs[job_id][1])
                job_completion_order.append(job_id)
                # Update the finished jobs distribution
                finished_jobs_distribution[i] += 1
            else:
                # Check for new arrivals in the first queue
                if queues[0]:
                    # Put the current job back to the current queue
                    queues[i].appendleft((job_id, remaining_size, arrival_time, waiting_time))
                    # Handle jobs in the first queue
                    while queues[0]:
                        job_id, remaining_size, arrival_time, waiting_time = queues[0].popleft()
                        job_logs[job_id]['scheduling_queue'] = 0
                        if job_logs[job_id]['first_executed_time'] is None:
                            job_logs[job_id]['first_executed_time'] = current_time
                        Bj = calculate_Bj(job_id, 0)
                        executed_time = min(remaining_size, get_execution_time(0, Bj))
                        remaining_size -= executed_time
                        current_time += executed_time
                        job_logs[job_id]['waiting_time'] = current_time - arrival_time - (jobs[job_id][1] - remaining_size)
                        if remaining_size <= 0:
                            job_logs[job_id]['ifdone'] = True
                            job_logs[job_id]['finished_time'] = current_time
                            job_logs[job_id]['finished_queue'] = 0
                            job_logs[job_id]['finish_threshold'] = job_logs[job_id]['starvation_threshold']
                            job_logs[job_id]['finish_level'] = 0
                            flow_times.append(current_time - arrival_time)
                            finished_job_sizes.append(jobs[job_id][1])
                            job_completion_order.append(job_id)
                            # Update the finished jobs distribution
                            finished_jobs_distribution[0] += 1
                        else:
                            queues[1].append((job_id, remaining_size, arrival_time, waiting_time + executed_time))
                    # After handling first queue, go back to the original queue
                    continue
                # Otherwise, continue with the current job
                next_queue = min(i + 1, num_queues - 1)
                min_finished_job_size = calculate_min_job_size(finished_job_sizes) if finished_job_sizes else 1
                new_threshold = calculate_starvation_threshold(min_finished_job_size, next_queue)
                job_logs[job_id]['starvation_threshold'] = new_threshold
                queues[next_queue].append((job_id, remaining_size, arrival_time, waiting_time + executed_time))

        # Increment waiting time for all jobs in the queues
        for queue in queues:
            for j in range(len(queue)):
                job_id, remaining_size, arrival_time, waiting_time = queue[j]
                queue[j] = (job_id, remaining_size, arrival_time, waiting_time + 1)

    # Calculate average flow time
    total_flow_time = sum(flow_times)
    average_flow_time = total_flow_time / len(flow_times)

    # Calculate L2 norm flow time
    squared_flow_times = [ft ** 2 for ft in flow_times]
    l2_norm_flow_time = sum(squared_flow_times) ** 0.5

    # Write the job logs to a CSV file
    with open('job_logs.csv', 'w', newline='') as csvfile:
        fieldnames = ['job_id', 'arrival_time', 'job_size', 'finished_time', 'finished_queue', 'finish_threshold', 'finish_level', 'is_starved', 'starvation_count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for job_id, log in job_logs.items():
            if log['ifdone']:
                writer.writerow({
                    'job_id': job_id,
                    'arrival_time': log['arrival_time'],
                    'job_size': log['job_size'],
                    'finished_time': log['finished_time'],
                    'finished_queue': log['finished_queue'],
                    'finish_threshold': log['finish_threshold'],
                    'finish_level': log['finish_level'],
                    'is_starved': log['is_starved'],
                    'starvation_count': log['starvation_count']
                })

    # Write the finished jobs distribution to a CSV file
    with open('finished_jobs_distribution.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Queue Level', 'Number of Finished Jobs'])
        for level, count in finished_jobs_distribution.items():
            writer.writerow([level, count])

    return average_flow_time, l2_norm_flow_time

# Example usage:
filename = "data/(26, 7.918).csv"
jobs = Read_csv(filename)
second_number = extract_second_number_from_filename(filename)
avg_flow_time, l2_norm = Rmlfq_aFCFS(jobs, second_number, num_queues=100)
print(f"Average Flow Time: {avg_flow_time}")
print(f"L2-Norm of Flow Times: {l2_norm}")
