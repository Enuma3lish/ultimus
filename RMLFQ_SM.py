import pandas as pd
import math
import random
def Read_csv(filename):
    # Read the CSV file into a DataFrame
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list
import math
import random

def Rmlfq_sm(jobs,p):
    """Schedules jobs using MLFQ with exponential arrival and probability-based queue selection.
    If p = 0, strictly follows the original MLFQ queue order.

    Args:
        jobs: List of [arrival_time, job_size] pairs.
        num_queues: Number of queues in the MLFQ system.
        p: Probability for the next lower-priority queue to be selected if it has jobs.

    Returns:
        Tuple of (average_flow_time, l2_norm_flow_time). If no jobs are processed, returns (0, 0).
    """
    num_queues=100
    queues = [[] for _ in range(num_queues)]
    time = 0
    flow_times = []

    for j, (arrival_time, job_size) in enumerate(jobs, 1):
        queues[0].append([arrival_time, job_size, 1 if j < 3 else 1 - random.expovariate(12 * math.log(j))])  
  
    while any(queues):
        # Find the highest priority queue with jobs ready
        selected_queue = None
        for i, q in enumerate(queues):
            if q and time >= q[0][0]:
                selected_queue = i
                break
        if selected_queue is None:
            # No jobs are ready at this time, move to the next time
            time += 1
            continue  # Continue to the next iteration of the outer while loop
            
        # Queue Selection (MLFQ with Probability or Strict Order)
        if p != 0: # if p ==0 , we will follow the mlfq sequence
            eligible_queues = [(i, q) for i, q in enumerate(queues) if q and time >= q[0][0]]
            queue_probs = [p**i for i, _ in eligible_queues]
            total_prob = sum(queue_probs)
            queue_probs = [prob/total_prob for prob in queue_probs]
            selected_queue = random.choices([i for i, _ in eligible_queues], weights=queue_probs)[0]

        # Process the job in the selected queue
        q = queues[selected_queue]
        job = q[0]
        target_time = 2**selected_queue * max(1, 2 - job[2])  
            
        execution_time = min(target_time, job[1])
        time += execution_time # Update time based on how much the job can run
        job[1] -= execution_time

        if job[1] == 0:  
            flow_times.append(time - job[0]) 
            q.pop(0)
        elif time - job[0] >= target_time:  
            q.pop(0)
            if selected_queue < num_queues - 1:  
                queues[selected_queue + 1].append(job)  
            else:
                q.append(job)


    average_flow_time = sum(flow_times) / len(flow_times) if flow_times else 0
    l2_norm_flow_time = math.sqrt(sum(x*x for x in flow_times)) if flow_times else 0
    return average_flow_time, l2_norm_flow_time


jobs = Read_csv("data/(28, 4.073).csv")
avg,l2=Rmlfq_sm(jobs,0.05)
print(avg)
print(l2)
#print(logs)