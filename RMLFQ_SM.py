import random
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
def calculate_Bj(j):
    """ Calculate Bj based on the number of jobs (j). """
    if j >= 3:
        return 1 - j**-12
    else:
        return 1

def get_execution_time(i, Bj):
    """ Determine execution time at level i given Bj. """
    return 2**i * max(1, 2 - Bj)

def Rmlfq_sm(jobs, quantum_decrease):
    # Initialize data structures
    num_queues=100
    queues = [[] for _ in range(num_queues)]
    job_logs = {i: {'arrival_time': job[0], 'first_executed_time': None, 'ifdone': False} for i, job in enumerate(jobs)}
    flow_times = []
    current_time = 0

    # Calculate Bj for the total number of jobs
    Bj = calculate_Bj(len(jobs))

    # Initialize quantum for each queue
    quantum = [get_execution_time(i, Bj) * 30 for i in range(num_queues)]

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
        job_executed = False
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
                    if quantum_decrease > 0:
                        next_queue = min(i + 1, num_queues - 1) if random.random() < quantum_decrease else i
                    else:
                        next_queue = i + 1 if i + 1 < num_queues else i
                    queues[next_queue].append((job_id, remaining_size, arrival_time))
                job_executed = True
                break

        # Advance time if no job was executed
        if not job_executed:
            current_time = max(current_time + 1, jobs[next_job_index][0] if next_job_index < len(jobs) else current_time)

    # Calculate average flow time
    total_flow_time = sum(flow_times)
    average_flow_time = total_flow_time / len(flow_times)

    # Calculate L2 norm flow time
    squared_flow_times = [ft ** 2 for ft in flow_times]
    l2_norm_flow_time = (sum(squared_flow_times)) ** 0.5

    return average_flow_time, l2_norm_flow_time #,job_logs
jobs = Read_csv("data/(20, 4.073).csv")
avg,l2=Rmlfq_sm(jobs,0.03)
print(avg)
print(l2)
#print(logs)