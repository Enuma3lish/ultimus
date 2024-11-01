#re-designed
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
    return max(1,2 - random.expovariate(12 * math.log(j)))

def Rmlfq(jobs, initial_num_queues=2):
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

    for j, (arrival_time, job_size) in enumerate(jobs, 1):
        while time < arrival_time:
            executed = False
            for i in range(num_queues):
                if queues[i]:  # Process the first non-empty queue
                    job = queues[i][0]
                    max_exec_time = 2 ** i * job[2]
                    if i == num_queues - 1:
                        exec_time = min(max_exec_time, job[1])
                        job[1] -= exec_time
                        time += exec_time
                        if job[1] == 0:
                            finish_time = time
                            flow_time = finish_time - job[0]
                            flow_times.append(flow_time)
                            finished_job_sizes.append(job[1] + exec_time)  # Record the finished job size
                            #print(f"Time {time}: Job {job} completed. Flow time: {flow_time}")
                            queues[i].pop(0)
                        else:
                            queues[i].append(queues[i].pop(0))  # Round-robin rotation
                    else:
                        exec_time = min(max_exec_time, job[1])
                        job[1] -= exec_time
                        time += exec_time
                        if job[1] == 0:
                            finish_time = time
                            flow_time = finish_time - job[0]
                            flow_times.append(flow_time)
                            finished_job_sizes.append(job[1] + exec_time)  # Record the finished job size
                            #print(f"Time {time}: Job {job} completed. Flow time: {flow_time}")
                            queues[i].pop(0)
                        else:
                            queues[i].pop(0)
                            queues[i + 1].append(job)  # Move to the next queue
                            #print(f"Time {time}: Job {job} moved to queue {i+1}")
                    executed = True
                    break
            if not executed:
                time += 1
                break

        time = max(time, arrival_time)
        bj = calculate_Bj(j)
        add_job_to_appropriate_queue([arrival_time, job_size, bj])
        #print(f"Time {time}: Job {[arrival_time, job_size, bj]} added to queue 0")

    while any(queues):  # Process remaining jobs
        executed = False
        for i in range(num_queues):
            if queues[i]:
                job = queues[i][0]
                max_exec_time = 2 ** i * job[2]
                if i == num_queues - 1:
                    exec_time = min(max_exec_time, job[1])
                    job[1] -= exec_time
                    time += exec_time
                    if job[1] == 0:
                        finish_time = time
                        flow_time = finish_time - job[0]
                        flow_times.append(flow_time)
                        finished_job_sizes.append(job[1] + exec_time)  # Record the finished job size
                        #print(f"Time {time}: Job {job} completed. Flow time: {flow_time}")
                        queues[i].pop(0)
                    else:
                        queues[i].append(queues[i].pop(0))  # Round-robin rotation
                else:
                    exec_time = min(max_exec_time, job[1])
                    job[1] -= exec_time
                    time += exec_time
                    if job[1] == 0:
                        finish_time = time
                        flow_time = finish_time - job[0]
                        flow_times.append(flow_time)
                        finished_job_sizes.append(job[1] + exec_time)  # Record the finished job size
                        #print(f"Time {time}: Job {job} completed. Flow time: {flow_time}")
                        queues[i].pop(0)
                    else:
                        queues[i].pop(0)
                        queues[i + 1].append(job)  # Move to the next queue
                        #print(f"Time {time}: Job {job} moved to queue {i+1}")
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
jobs = Read_csv("data/(26, 7.918).csv")
print(jobs)
#jobs = Read_csv("data/(20, 4.073).csv")
average_flow_time, l2_norm_flow_time = Rmlfq(jobs)
print(f"Average Flow Time: {average_flow_time}")
print(f"L2 Norm Flow Time: {l2_norm_flow_time}")
