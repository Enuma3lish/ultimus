import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def Mmlfq(jobs, quantum_multiplier, quantum_decrease, num_queues=100):
    # Initialize data structures
    queues = [[] for _ in range(num_queues)]
    job_logs = {i: {'arrival_time': job[0], 'first_executed_time': None, 'ifdone': False} for i, job in enumerate(jobs)}
    flow_times = []
    current_time = 0

    # Initialize quantum for each queue with first level at 30 units
    quantum = [pow(2,6)* (quantum_multiplier ** i) for i in range(num_queues)]

    # Sort jobs by arrival time and enqueue in the first queue
    jobs = sorted(jobs, key=lambda x: x[0])
    next_job_index = 0

    while next_job_index < len(jobs) or any(queues):
        # Enqueue jobs that have now arrived
        while next_job_index < len(jobs) and jobs[next_job_index][0] <= current_time:
            job_id = next_job_index
            job_size = jobs[next_job_index][1]
            arrival_time = jobs[next_job_index][0]
            queues[0].append((job_id, job_size, arrival_time))
            next_job_index += 1

        # Process jobs from the highest priority queue with available jobs
        for i in range(num_queues):
            if queues[i]:
                job_id, remaining_size, arrival_time = queues[i].pop(0)
                if job_logs[job_id]['first_executed_time'] is None:
                    job_logs[job_id]['first_executed_time'] = current_time
                # Execute job
                executed_time = min(remaining_size, quantum[i])
                remaining_size -= executed_time
                current_time += executed_time
                if remaining_size <= 0:
                    job_logs[job_id]['ifdone'] = True
                    flow_times.append(current_time - arrival_time)
                else:
                    # Decide if job should be demoted
                    next_queue = min(i + 1, num_queues - 1) if np.random.rand() < quantum_decrease else i
                    queues[next_queue].append((job_id, remaining_size, arrival_time))
                break

        # Advance time if no job was executed
        if all(len(queue) == 0 for queue in queues):
            current_time = max(current_time + 1, jobs[next_job_index][0] if next_job_index < len(jobs) else current_time)

    average_flow_time = np.mean(flow_times)
    l2_norm_flow_time = np.linalg.norm(flow_times, 2)

    return average_flow_time, l2_norm_flow_time, job_logs


# jobs = Read_csv("data/(28, 16.772).csv")
# avg,l2,logs=Mmlfq(jobs,1,0)
# print(avg)
# print(l2)
#print(logs)