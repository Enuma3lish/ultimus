import numpy as np
import pandas as pd

def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Rmlfq(jobs, num_queues=100, base_quantum=30, quantum_multiplier=2):
    queues = [[] for _ in range(num_queues)]
    queue_time_quantums = [base_quantum * (pow(quantum_multiplier, i)) for i in range(num_queues)]
    current_time = 0
    job_completion_times = []
    job_logs = []  # Initialize the job log list

    def add_job(arrival_time, job_size):
        job_log = {'arrival_time': arrival_time, 'first_executed_time': None, 'ifdone': False}
        job_logs.append(job_log)  # Append job log to list
        job_id = len(job_logs)  # Use current length of job_logs as the job ID
        queues[0].append({'job_id': job_id, 'arrival_time': arrival_time, 'job_size': job_size, 'remaining_time': job_size})
        return job_id

    def weighted_random_queue_selection():
        non_empty_queues = [i for i, q in enumerate(queues) if len(q) > 0]
        if len(non_empty_queues) > 2:
            # Calculate weights for each non-empty queue using the specified formula
            weights = [pow(2, -pow(2, -i)) for i in non_empty_queues]
            total_weight = sum(weights)
            adjusted_probabilities = [w / total_weight for w in weights]
            return np.random.choice(non_empty_queues, p=adjusted_probabilities)
        elif len(non_empty_queues) == 1 and non_empty_queues[0] == 0:
            # If only queue 0 has jobs, execute from queue 0 directly
            return 0
        # If there are only 2 non-empty queues or fewer, return the one with the highest priority (lowest index)
        return non_empty_queues[0] if non_empty_queues else None

    def execute_job_from_queue(queue_index):
        nonlocal current_time  # Ensure current_time is treated as the enclosing scope's variable
        if queues[queue_index]:
            job = queues[queue_index][0]
            job_id = job['job_id']
            time_quantum = min(queue_time_quantums[queue_index], job['remaining_time'])
            job['remaining_time'] -= time_quantum
            current_time += time_quantum
            
            # Update the first executed time if this is the first execution
            if job_logs[job_id - 1]['first_executed_time'] is None:
                job_logs[job_id - 1]['first_executed_time'] = current_time
            
            if job['remaining_time'] <= 0:
                job_completion_times.append(current_time - job['arrival_time'])
                job_logs[job_id - 1]['ifdone'] = True  # Mark the job as done in the log
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

        selected_queue = weighted_random_queue_selection()
        if selected_queue is not None:
            execute_job_from_queue(selected_queue)
        else:
            # If no suitable queue is found (e.g., all jobs are done), possibly advance time to the next job's arrival
            if job_index < total_jobs and not any(queue for queue in queues if queue):
                current_time = jobs[job_index][0]

    average_flow_time = np.mean(job_completion_times) if job_completion_times else 0
    l2_norm_flow_time = np.linalg.norm(job_completion_times)
    return average_flow_time, l2_norm_flow_time, job_logs

#Example call with the job list
jobs = Read_csv("data/(40, 4.073).csv")
average_flow_time, l2_norm_flow_time, job_logs = Rmlfq(jobs)
print(average_flow_time)
print(l2_norm_flow_time)
# print(job_logs)
