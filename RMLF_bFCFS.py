import random
import math
from math import log2, ceil
import pandas as pd

def Read_csv(filename):
    """Read the CSV file into a list of lists."""
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

def calculate_Bj(j):
    """Calculate Bj based on the index of the job (j)."""
    if j < 3:
        return 1
    else:
        return 1 - random.expovariate(12 * math.log(j))

def Rmlf_bFCFS(jobs, initial_num_queues=2):
    """Schedules jobs using the RMLF and FCFS modes.

    Args:
        jobs: List of [arrival_time, job_size] pairs.
        initial_num_queues: Initial number of queues in the MLFQ system.

    Returns:
        Tuple of (average_flow_time, l2_norm_flow_time).
    """
    num_queues = initial_num_queues
    queues = [[] for _ in range(num_queues)]
    time = 0
    flow_times = []
    finished_job_sizes = []
    mfjs = 0  # Maximum finished job size

    def add_job_to_appropriate_queue(job):
        nonlocal num_queues, mfjs, queues
        mfjs = max(mfjs, job[1])
        num_queues = max(initial_num_queues, ceil(log2(mfjs)))
        if len(queues) < num_queues:
            queues.extend([[] for _ in range(num_queues - len(queues))])
        queues[0].append(job)

    def mean_finished_job_size():
        """Calculate the mean finished job size."""
        return sum(finished_job_sizes) / len(finished_job_sizes) if finished_job_sizes else 0

    def use_fcfs_mode():
        """Decide whether to use FCFS mode or RMLF mode."""
        mean_size = mean_finished_job_size()
        if not finished_job_sizes:
            return False  # Default to RMLF if no jobs have finished
        log_mean_size = log2(mean_size) if mean_size > 0 else 0
        log_max_size = log2(mfjs) if mfjs > 0 else 0
        return log_mean_size * 2 > log_max_size

    for j, (arrival_time, job_size) in enumerate(jobs, 1):
        while time < arrival_time:
            executed = False
            if use_fcfs_mode():
                # FCFS mode
                for i in range(num_queues):
                    if queues[i]:  # Process the first non-empty queue in FCFS mode
                        job = queues[i][0]
                        exec_time = job[1]  # Execute the entire job in FCFS
                        job[1] -= exec_time
                        time += exec_time
                        finish_time = time
                        flow_time = finish_time - job[0]
                        flow_times.append(flow_time)
                        finished_job_sizes.append(job[1] + exec_time)  # Record the finished job size
                        queues[i].pop(0)
                        executed = True
                        break
            else:
                # RMLF mode
                for i in range(num_queues):
                    if queues[i]:  # Process the first non-empty queue in RMLF mode
                        job = queues[i][0]
                        max_exec_time = 2 ** i * job[2]
                        exec_time = min(max_exec_time, job[1])
                        job[1] -= exec_time
                        time += exec_time
                        if job[1] == 0:
                            finish_time = time
                            flow_time = finish_time - job[0]
                            flow_times.append(flow_time)
                            finished_job_sizes.append(job[1] + exec_time)  # Record the finished job size
                            queues[i].pop(0)
                        else:
                            queues[i].pop(0)
                            if i < num_queues - 1:
                                queues[i + 1].append(job)  # Move to the next queue
                        executed = True
                        break
            if not executed:
                time += 1
                break

        time = max(time, arrival_time)
        bj = calculate_Bj(j)
        add_job_to_appropriate_queue([arrival_time, job_size, bj])

    # Process remaining jobs after arrival
    while any(queues):  # Process remaining jobs
        executed = False
        if use_fcfs_mode():
            # FCFS mode
            for i in range(num_queues):
                if queues[i]:
                    job = queues[i][0]
                    exec_time = job[1]
                    job[1] -= exec_time
                    time += exec_time
                    finish_time = time
                    flow_time = finish_time - job[0]
                    flow_times.append(flow_time)
                    finished_job_sizes.append(job[1] + exec_time)
                    queues[i].pop(0)
                    executed = True
                    break
        else:
            # RMLF mode
            for i in range(num_queues):
                if queues[i]:
                    job = queues[i][0]
                    max_exec_time = 2 ** i * job[2]
                    exec_time = min(max_exec_time, job[1])
                    job[1] -= exec_time
                    time += exec_time
                    if job[1] == 0:
                        finish_time = time
                        flow_time = finish_time - job[0]
                        flow_times.append(flow_time)
                        finished_job_sizes.append(job[1] + exec_time)
                        queues[i].pop(0)
                    else:
                        queues[i].pop(0)
                        if i < num_queues - 1:
                            queues[i + 1].append(job)
                    executed = True
                    break
        if not executed:
            time += 1

    if not flow_times:
        print("No jobs have been completed. Please check the job scheduling logic.")

    average_flow_time = sum(flow_times) / len(flow_times) if flow_times else 0
    l2_norm_flow_time = math.sqrt(sum(x*x for x in flow_times)) if flow_times else 0
    return average_flow_time, l2_norm_flow_time

# Example call with the job list
#jobs = Read_csv("data/(20, 16.772).csv")
jobs = Read_csv("data/(26, 7.918).csv")
average_flow_time, l2_norm_flow_time = Rmlf_bFCFS(jobs)
print(f"Average Flow Time: {average_flow_time}")
print(f"L2 Norm Flow Time: {l2_norm_flow_time}")