import pandas as pd
import numpy as np
import random
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
# Calculate average and maximum flow times without using heapq

def Rmlfq(jobs):
    # Constants
    NUM_QUEUES = 100
    MAX_TIME_LIMIT = 2**99  # Maximum time limit for the lowest priority queue

    # Initialize queues and time limits
    queues = [[] for _ in range(NUM_QUEUES)]
    time_limits = [min(2**i, MAX_TIME_LIMIT) for i in range(NUM_QUEUES)]

    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])

    # Metrics
    total_flow_time = 0
    max_flow_time = 0

    # Simulation
    current_time = 0
    completed_jobs = 0
    job_index = 0  # Index to keep track of the next job to be introduced
    flow_arr = []
    while completed_jobs < len(jobs) or any(queues):
        # Add new jobs to the highest priority queue if they have arrived
        while job_index < len(jobs) and jobs[job_index][0] <= current_time:
            _, job_size = jobs[job_index]
            queues[0].append((job_index, job_size))
            job_index += 1

        executed = False
        for queue_index in range(NUM_QUEUES):
            if queues[queue_index]:
                # Execute jobs in the current queue based on its time limit
                queue_time_limit = time_limits[queue_index]
                new_queue = []
                for job in queues[queue_index]:
                    job_id, job_time = job
                    execute_time = min(job_time, queue_time_limit)
                    job_time -= execute_time
                    current_time += execute_time

                    if job_time > 0:
                        # Job not completed, move to the next lower priority queue
                        next_queue_index = min(queue_index + 1, NUM_QUEUES - 1)
                        queues[next_queue_index].append((job_id, job_time))
                    else:
                        # Job completed
                        completed_jobs += 1
                        flow_time = current_time - jobs[job_id][0]  # Subtract arrival time for flow time
                        total_flow_time += flow_time
                        max_flow_time = max(max_flow_time, flow_time)

                executed = True
                queues[queue_index] = new_queue  # Update the current queue

            # Weighted random selection of non-empty queues (excluding the current queue)
            weights = [len(queue) * (NUM_QUEUES - i) for i, queue in enumerate(queues) if i != queue_index and queue]
            if weights and executed:
                weighted_queues = [(i, queue) for i, queue in enumerate(queues) if i != queue_index and queue]
                selected_queue_index, selected_queue = random.choices(weighted_queues, weights=weights, k=1)[0]

                # Execute one job from the selected queue
                job_id, job_time = selected_queue.pop(0)
                execute_time = min(job_time, time_limits[selected_queue_index])
                job_time -= execute_time
                current_time += execute_time

                if job_time > 0:
                    # Job not completed, move to the next lower priority queue
                    next_queue_index = min(selected_queue_index + 1, NUM_QUEUES - 1)
                    queues[next_queue_index].append((job_id, job_time))
                else:
                    # Job completed
                    completed_jobs += 1
                    flow_time = current_time - jobs[job_id][0]  # Subtract arrival time for flow time
                    flow_arr.append(flow_time)
                    total_flow_time += flow_time
                    max_flow_time = max(max_flow_time, flow_time)

            if executed:
                break  # Move to the next time unit after executing jobs from a queue

        # If no jobs were executed and there are still jobs pending, increment current time
        if not executed and job_index < len(jobs):
            current_time = max(current_time + 1, jobs[job_index][0])
    flow_time_l2_norm = np.linalg.norm(flow_arr)
    # Calculate average and maximum flow times
    average_flow_time = total_flow_time / len(jobs)
    print(f"rmlfq Maximum Flow Time: {max_flow_time}")
    print(f"rmlfq flow time L2-norm: {flow_time_l2_norm}")
    return average_flow_time,flow_time_l2_norm