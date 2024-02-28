import numpy as np

def Prmlfq(jobs):
    # Constants
    tau = 12
    n = len(jobs)  # Total number of jobs

    # Function to generate beta_j values based on the given probability distribution
    def generate_beta_j(job_size, j):
        u = np.random.rand()  # Generate a uniform random number between 0 and 1
        beta_j = -np.log(1 - u) / (tau * np.log(j))
        return beta_j

    # Function to calculate time quantum for a job at level i
    def calculate_time_quantum(i, beta_j):
        return 2**i * max(1, 2 - beta_j)

    # Generate beta_j for each job
    beta_js = [generate_beta_j(job[1], j+3) for j, job in enumerate(jobs)]  # Starting j from 3

    # Calculate time quantum for each job at initial level (i=0)
    time_quantums = [calculate_time_quantum(0, beta_j) for beta_j in beta_js]

    # Simulate job completion and calculate flow times
    completion_times = []
    current_time = 0
    for job, tq in zip(jobs, time_quantums):
        arrival_time, job_size = job
        current_time = max(current_time, arrival_time) + job_size * tq  # Simplified execution time
        completion_times.append(current_time - arrival_time)  # Flow time

    # Calculate average flow time and L2-norm flow time
    average_flow_time = np.mean(completion_times)
    l2_norm_flow_time = np.linalg.norm(completion_times, 2)

    return average_flow_time, l2_norm_flow_time

