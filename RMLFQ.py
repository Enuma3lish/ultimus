import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Rmlfq(jobs, num_queues=100, base_quantum=30, quantum_multiplier=1.1):
    queues = [[] for _ in range(num_queues)]
    queue_time_quantums = [base_quantum * (pow(quantum_multiplier, i)) for i in range(num_queues)]
    queue_priorities = [pow(5, -i) for i in range(num_queues)]
    current_time = 0
    job_completion_times = []

    def add_job(arrival_time, job_size):
        queues[0].append({'arrival_time': arrival_time, 'job_size': job_size, 'remaining_time': job_size})

    def weighted_random_queue_selection():
        nonlocal current_time  # Ensure current_time is treated as the enclosing scope's variable
        normalized_priorities = np.array(queue_priorities) / np.sum(queue_priorities)
        non_empty_queues = [i for i, q in enumerate(queues) if len(q) > 0]
        if non_empty_queues:
            non_empty_priorities = normalized_priorities[non_empty_queues]
            non_empty_priorities /= non_empty_priorities.sum()
            return np.random.choice(non_empty_queues, p=non_empty_priorities)
        return None

    def execute_job_from_queue(queue_index):
        nonlocal current_time  # Ensure current_time is treated as the enclosing scope's variable
        if queues[queue_index]:
            job = queues[queue_index][0]
            time_quantum = min(queue_time_quantums[queue_index], job['remaining_time'])
            job['remaining_time'] -= time_quantum
            current_time += time_quantum
            
            if job['remaining_time'] <= 0:
                job_completion_times.append(current_time - job['arrival_time'])
                queues[queue_index].pop(0)
            elif queue_index < num_queues - 1:
                queues[queue_index].pop(0)
                queues[queue_index + 1].append(job)

    # Sort jobs by arrival time to process in order
    jobs.sort(key=lambda x: x[0])
    job_index = 0
    total_jobs = len(jobs)

    while len(job_completion_times) < total_jobs:
        while job_index < total_jobs and jobs[job_index][0] <= current_time:
            add_job(jobs[job_index][0], jobs[job_index][1])
            job_index += 1

        if queues[0]:
            execute_job_from_queue(0)
        else:
            selected_queue = weighted_random_queue_selection()
            if selected_queue is not None:
                execute_job_from_queue(selected_queue)

        if job_index < total_jobs and not any(queues):
            current_time = jobs[job_index][0]

    average_flow_time = np.mean(job_completion_times) if job_completion_times else 0
    l2_norm_flow_time = np.linalg.norm(job_completion_times)

    return average_flow_time, l2_norm_flow_time


# Execute the fixed MLFQ System function
# jobs = Read_csv('(0.025, 16.772).csv')

# # Run the preemptive SETF algorithm
# average_flow_time, flow_time_l2_norm = Rmlfq(jobs)

# print("Average Flow Time:", average_flow_time)
# print("Flow Time L2 Norm:", flow_time_l2_norm)
