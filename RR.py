from typing import List, Tuple
from itertools import count
from RR_Selector import RR_Selector

def RR(initial_jobs: List[List[int]], time_quantum: int = 2) -> Tuple[float, float]:
    """
    Online Round Robin scheduler that processes jobs until completion.
    
    Args:
        initial_jobs: Initial list of [arrival_time, job_size] pairs
        time_quantum: Time quantum for Round Robin scheduling
    
    Returns:
        Tuple of (average_flow_time, l2_norm)
    """
    jobs = initial_jobs.copy()
    total_jobs = len(jobs)
    current_time = 0
    remaining_jobs = [[job[0], job[1]] for job in jobs]  # Create mutable copy
    completion_times = [0] * total_jobs
    total_flow_time = 0
    l2_norm_sum = 0
    completed_jobs = 0
    
    # Process jobs until all are completed
    for _ in count():
        # Break condition: all jobs are completed
        if completed_jobs == total_jobs:
            break
            
        # Get next job from selector if there are remaining jobs
        if remaining_jobs:
            job_index, execution_time = RR_Selector(remaining_jobs, current_time, time_quantum)
            
            if job_index is not None:
                # Execute the selected job
                arrival_time = remaining_jobs[job_index][0]
                current_time = max(current_time, arrival_time) + execution_time
                remaining_jobs[job_index][1] -= execution_time
                
                # Process job completion
                if remaining_jobs[job_index][1] == 0:
                    completion_times[job_index] = current_time
                    flow_time = completion_times[job_index] - jobs[job_index][0]
                    total_flow_time += flow_time
                    l2_norm_sum += flow_time ** 2
                    completed_jobs += 1
                    remaining_jobs.pop(job_index)
                    
                    print(f"Job {job_index} completed at time {current_time}")
                    print(f"Flow time: {flow_time}")
                    print(f"Completed jobs: {completed_jobs}/{total_jobs}")
                    print("---")
            else:
                # No job available, advance time
                current_time = execution_time
    
    # Calculate final metrics
    avg_flow_time = total_flow_time / total_jobs
    l2_norm = l2_norm_sum ** 0.5
    
    print("\nFinal Results:")
    print(f"Average Flow Time: {avg_flow_time}")
    print(f"L2 Norm: {l2_norm}")
    
    return avg_flow_time, l2_norm

# if __name__ == "__main__":
#     # Example jobs: [arrival_time, job_size]
#     initial_jobs = [
#         [0, 5],  # Job 1: arrives at time 0, needs 5 time units
#         [1, 3],  # Job 2: arrives at time 1, needs 3 time units
#         [2, 4]   # Job 3: arrives at time 2, needs 4 time units
#     ]
    
#     # Start the Round Robin scheduler
#     avg_flow_time, l2_norm = RR(initial_jobs, time_quantum=2)