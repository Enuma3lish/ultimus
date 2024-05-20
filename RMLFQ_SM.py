import pandas as pd
import math
import random
def Read_csv(filename):
    # Read the CSV file into a DataFrame
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
import random
import math

def calculate_Bj(j):
    """ Calculate Bj based on the number of jobs (j). """
    if j >= 3:
        U = random.uniform(0, 1)
        return U / j**-12
    else:
        return 1

def get_execution_time(i, Bj):
    """ Determine execution time at level i given Bj. """
    return 2**i * max(1, 2 - Bj)

def calculate_weights(p, num_active_queues):
    """ Calculate selection weights for active queues based on p. """
    if num_active_queues == 0:
        return []
    weights = [p**i for i in range(num_active_queues)]
    total_weight = sum(weights)
    normalized_weights = [w / total_weight for w in weights]
    return normalized_weights

def Rmlfq_sm(jobs, p):
    """ Simulate RMLF-sm algorithm with probability based queue selection. """
    time = 0
    jobs = sorted(jobs, key=lambda x: x[0])  # Sort by arrival time
    num_jobs = len(jobs)
    initial_levels = 3  # Initial number of queues
    queues = [[] for _ in range(initial_levels)]
    flow_times = []
    job_index = 0  # To track which job we are on for Bj calculations
    max_job_size = 0  # Track the maximum job size

    while jobs or any(queue for queue in queues if queue):
        # Load new jobs into the system if it's time or queue is empty
        while jobs and (jobs[0][0] <= time or not any(queue for queue in queues if queue)):
            arrival_time, job_size = jobs.pop(0)
            max_job_size = max(max_job_size, job_size)
            if time < arrival_time:
                time = arrival_time  # Adjust time to avoid idling
            Bj = calculate_Bj(job_index + 1)
            queues[0].append([job_size, time, Bj])  # Add job to first level
            job_index += 1

        # Adjust the number of levels dynamically based on the maximum job size
        required_levels = max(initial_levels, math.ceil(math.log2(max_job_size)))
        if required_levels > len(queues):
            queues.extend([[] for _ in range(required_levels - len(queues))])

        # Determine active queues and calculate weights for random selection
        active_queues = [i for i in range(required_levels) if queues[i]]
        if active_queues:
            if 0 in active_queues:
                # Always choose the first queue if it has items
                chosen_queue_index = 0
            else:
                # Calculate weights for the remaining active queues
                weights = calculate_weights(p, len(active_queues))
                chosen_queue_index = random.choices(active_queues, weights)[0]

            job_size, start_time, Bj = queues[chosen_queue_index].pop(0)
            exec_time = get_execution_time(chosen_queue_index, Bj)
            if job_size > exec_time:
                # Not completed, move to next level
                next_level = min(chosen_queue_index + 1, required_levels - 1)
                queues[next_level].append([job_size - exec_time, start_time, Bj])
            else:
                # Job completed
                flow_times.append(time - start_time + exec_time)
            time += exec_time
        else:
            # If all queues are empty and jobs remain, adjust time to next job's arrival
            if jobs:
                time = max(time, jobs[0][0])

    # Calculate average and L2-norm flow times
    average_flow_time = sum(flow_times) / num_jobs
    l2_norm_flow_time = sum(ft**2 for ft in flow_times)**0.5

    return average_flow_time, l2_norm_flow_time
jobs = Read_csv("data/(40, 4.073).csv")
avg,l2=Rmlfq_sm(jobs,0.0125)
print(avg)
print(l2)
#print(logs)