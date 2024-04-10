import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

def Mmlfq(jobs, quantum_multiplier, quantum_decrease, num_queues=100):
    base_quantum = 30
    queues = [[] for _ in range(num_queues)]
    queue_time_quantums = [base_quantum * (quantum_multiplier ** i) for i in range(num_queues)]
    # Adjust queue_priorities to account for quantum_decrease directly in calculations
    queue_priorities = [1 / (i + 1) if quantum_decrease == 0 else quantum_decrease ** -i for i in range(num_queues)]
    current_time = 0
    job_completion_times = []
    job_logs = {}

    def add_job(arrival_time, job_size):
        job_id = len(job_logs) + 1
        job_logs[job_id] = {'arrival_time': arrival_time, 'first_executed_time': None, 'ifdone': False}
        queues[0].append({'job_id': job_id, 'arrival_time': arrival_time, 'job_size': job_size, 'remaining_time': job_size})

    def queue_selection():
        if quantum_decrease == 0:
            # Sequential selection for quantum_decrease == 0
            for i, q in enumerate(queues):
                if len(q) > 0:
                    return i
            return None
        else:
            # Weighted random selection for quantum_decrease != 0
            weights = [len(q) * queue_priorities[i] if len(q) > 0 else 0 for i, q in enumerate(queues)]
            total_weight = sum(weights)
            if total_weight > 0:
                normalized_weights = [w / total_weight for w in weights]
                return np.random.choice(range(num_queues), p=normalized_weights)
            return None

    def execute_job_from_queue(queue_index):
        nonlocal current_time
        if queues[queue_index]:
            job = queues[queue_index][0]
            job_id = job['job_id']
            time_quantum = min(queue_time_quantums[queue_index], job['remaining_time'])
            job['remaining_time'] -= time_quantum
            current_time += time_quantum
            
            if job_logs[job_id]['first_executed_time'] is None:
                job_logs[job_id]['first_executed_time'] = current_time
            
            if job['remaining_time'] <= 0:
                job_completion_times.append(current_time - job['arrival_time'])
                job_logs[job_id]['ifdone'] = True
                queues[queue_index].pop(0)
            elif queue_index < num_queues - 1:
                queues[queue_index].pop(0)
                queues[queue_index + 1].append(job)

    jobs.sort(key=lambda x: x[0])
    job_index = 0
    total_jobs = len(jobs)

    while len(job_completion_times) < total_jobs:
        while job_index < total_jobs and jobs[job_index][0] <= current_time:
            add_job(jobs[job_index][0], jobs[job_index][1])
            job_index += 1

        selected_queue = queue_selection()

        if selected_queue is not None:
            execute_job_from_queue(selected_queue)
        elif queues[0]:  # Fallback to ensure logic completeness, might be redundant
            execute_job_from_queue(0)

        if job_index < total_jobs and not any(q for q in queues if q):
            current_time = jobs[job_index][0]

    average_flow_time = np.mean(job_completion_times) if job_completion_times else 0
    l2_norm_flow_time = np.linalg.norm(job_completion_times)

    job_details_list = list(job_logs.values())

    return average_flow_time, l2_norm_flow_time, job_details_list

# jobs = Read_csv("data/(38, 16.772).csv")
# avg,l2,logs=Mmlfq(jobs,1.1,0)
# print(avg)
# print(l2)
#print(logs)