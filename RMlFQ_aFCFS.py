import random
import pandas as pd
from collections import deque
import csv
import math

def Read_csv(filename):
    """Read the CSV file into a DataFrame and convert it to a list of lists."""
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

def calculate_Bj(j):
    """Calculate Bj based on the index of the job (j)."""
    if j < 3:
        return 1
    else:
        return 1 - random.expovariate(12 * math.log(j))

def get_execution_time(i, met):
    """Determine execution time at level i given the median execution time (met)."""
    return (i + 1) * met

def calculate_starvation_threshold(level, quantum, r):
    """Calculate the starvation threshold for a job in queue level."""
    try:
        if level <= 3:
            result = quantum[level]**0.5
        else:
            result = (r**level) * quantum[level]
            
        
        # Cap the result to avoid overflow
        result = min(result, 1e12)
        
        return result
    except OverflowError as e:
        return 1e12  # Return a large but safe value in case of overflow

def detect_starvation(job_logs, queues, current_time):
    """Detect starvation based on waiting time threshold."""
    starvation_jobs = []
    for i, queue in enumerate(queues):
        for job_id, remaining_size, arrival_time, waiting_time in queue:
            threshold = job_logs[job_id]['starvation_threshold']
            if waiting_time >= threshold:
                starvation_jobs.append((i, job_id, remaining_size, arrival_time, waiting_time))
    return starvation_jobs

def calculate_r(job_sizes):
    """Calculate the result r based on the median finished job size."""
    if len(job_sizes) < 2:
        return 2
    sorted_sizes = sorted(job_sizes)
    median_size = sorted_sizes[len(sorted_sizes) // 2]
    mfj = max(job_sizes)  # Maximum job size of finished jobs
    return mfj / median_size

def calculate_met(finished_job_sizes, met):
    """Calculate the median execution time (met) based on the finished job sizes."""
    if len(finished_job_sizes) < 2:
        return met
    sorted_sizes = sorted(finished_job_sizes)
    median_size = sorted_sizes[len(sorted_sizes) // 2]
    average_size = sum(finished_job_sizes) / len(finished_job_sizes)

    #print(f"Initial met: {met}, Median size: {median_size}, Average size: {average_size}")
    met = median_size
    if average_size >= 1.1 * median_size and average_size < 4* median_size:
         return met *4
    else:
        return met 
    
    # elif average_size >= 1.2 * median_size:
    #     median_size *= 1.5
def Rmlfq_aFCFS(jobs, num_queues=100):
    # Initialize data structures
    queues = [deque() for _ in range(num_queues)]
    job_logs = {i: {'arrival_time': job[0], 'first_executed_time': None, 'ifdone': False, 'waiting_time': 0, 'starvation_threshold': 30, 'final_threshold': None, 'finished_time': None, 'finished_queue': None, 'scheduling_queue': None, 'job_size': job[1]} for i, job in enumerate(jobs)}
    flow_times = []
    finished_job_sizes = []
    current_time = 0

    # Track the execution order of jobs larger than 30
    large_jobs_execution_order = []

    # Sort jobs by arrival time and enqueue in the first queue
    jobs = sorted(jobs, key=lambda x: x[0])
    next_job_index = 0
    job_completion_order = []
    met = 2  # Initial maximum execution time

    while next_job_index < len(jobs) or any(queues):
        # Enqueue jobs that have now arrived
        while next_job_index < len(jobs) and jobs[next_job_index][0] <= current_time:
            job_id = next_job_index
            job_size = jobs[next_job_index][1]
            arrival_time = jobs[next_job_index][0]
            Bj = calculate_Bj(job_id)
            quantum = [get_execution_time(i, met) for i in range(num_queues)]
            job_logs[job_id]['starvation_threshold'] = 30  # Initial threshold
            queues[0].append((job_id, job_size, arrival_time, 0))
            next_job_index += 1

        # Detect starvation
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
                executed_time = min(remaining_size, quantum[starvation_level])
                remaining_size -= executed_time
                current_time += executed_time
                job_logs[job_id]['waiting_time'] = current_time - arrival_time - (jobs[job_id][1] - remaining_size)
                if remaining_size <= 0:
                    job_logs[job_id]['ifdone'] = True
                    job_logs[job_id]['finished_time'] = current_time
                    job_logs[job_id]['finished_queue'] = starvation_level
                    job_logs[job_id]['final_threshold'] = job_logs[job_id]['starvation_threshold']
                    flow_times.append(current_time - arrival_time)
                    finished_job_sizes.append(jobs[job_id][1])
                    job_completion_order.append(job_id)
                    if jobs[job_id][1] > 30:
                        large_jobs_execution_order.append(job_id)
                    if len(finished_job_sizes) > 1:
                        r = calculate_r(finished_job_sizes)
                        met = calculate_met(finished_job_sizes, met)
                else:
                    next_queue = min(starvation_level + 1, num_queues - 1)
                    if len(finished_job_sizes) > 1:
                        r = calculate_r(finished_job_sizes)
                        met = calculate_met(finished_job_sizes, met)
                    else:
                        r = 2  # Default to 2 if not enough data points
                    new_threshold = calculate_starvation_threshold(next_queue, quantum, r)
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
            executed_time = min(remaining_size, quantum[i])
            remaining_size -= executed_time
            current_time += executed_time
            job_logs[job_id]['waiting_time'] = current_time - arrival_time - (jobs[job_id][1] - remaining_size)
            if remaining_size <= 0:
                job_logs[job_id]['ifdone'] = True
                job_logs[job_id]['finished_time'] = current_time
                job_logs[job_id]['finished_queue'] = i
                job_logs[job_id]['final_threshold'] = job_logs[job_id]['starvation_threshold']
                flow_times.append(current_time - arrival_time)
                finished_job_sizes.append(jobs[job_id][1])
                job_completion_order.append(job_id)
                if jobs[job_id][1] > 30:
                    large_jobs_execution_order.append(job_id)
                if len(finished_job_sizes) > 1:
                    r = calculate_r(finished_job_sizes)
                    met = calculate_met(finished_job_sizes, met)
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
                        executed_time = min(remaining_size, quantum[0])
                        remaining_size -= executed_time
                        current_time += executed_time
                        job_logs[job_id]['waiting_time'] = current_time - arrival_time - (jobs[job_id][1] - remaining_size)
                        if remaining_size <= 0:
                            job_logs[job_id]['ifdone'] = True
                            job_logs[job_id]['finished_time'] = current_time
                            job_logs[job_id]['finished_queue'] = 0
                            job_logs[job_id]['final_threshold'] = job_logs[job_id]['starvation_threshold']
                            flow_times.append(current_time - arrival_time)
                            finished_job_sizes.append(jobs[job_id][1])
                            job_completion_order.append(job_id)
                            if jobs[job_id][1] > 30:
                                large_jobs_execution_order.append(job_id)
                            if len(finished_job_sizes) > 1:
                                r = calculate_r(finished_job_sizes)
                                met = calculate_met(finished_job_sizes, met)
                        else:
                            queues[1].append((job_id, remaining_size, arrival_time, waiting_time + executed_time))
                    # After handling first queue, go back to the original queue
                    continue
                # Otherwise, continue with the current job
                next_queue = min(i + 1, num_queues - 1)
                if len(finished_job_sizes) > 1:
                    r = calculate_r(finished_job_sizes)
                    met = calculate_met(finished_job_sizes, met)
                else:
                    r = 2  # Default to 2 if not enough data points
                job_logs[job_id]['starvation_threshold'] = calculate_starvation_threshold(next_queue, quantum, r)
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

    return average_flow_time, l2_norm_flow_time

# Example usage:
jobs = Read_csv("data/(22, 4.639).csv")    
avg_flow_time, l2_norm = Rmlfq_aFCFS(jobs, num_queues=100)
print(f"Average Flow Time: {avg_flow_time}")
print(f"L2-Norm of Flow Times: {l2_norm}")
