from collections import deque
import math
import numpy as np
import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
    data_list = data_frame.values.tolist()
    return data_list

def Prmlfq(job_list):
    class Job:
        def __init__(self, arrival_time, job_size):
            self.arrival_time = arrival_time
            self.job_size = job_size
            self.remaining_time = job_size
            self.first_executed_time = None
            self.completion_time = None
            self.queue_level = 0
            self.beta = None
            self.target = None

        def update_target(self, tau, i, n):
            if self.beta is None:
                self.beta = np.random.exponential(scale=1/(tau * math.log(n)))
            self.target = 2 ** i * max(1, 2 - self.beta)

    class RMLFScheduler:
        def __init__(self, num_queues=100, tau=12):
            self.queues = [deque() for _ in range(num_queues)]
            self.current_time = 0
            self.tau = tau
            self.job_logs = []

        def add_job(self, job):
            job.update_target(self.tau, 0, len(self.queues))  # Initial target for Q0
            self.queues[0].append(job)

        def simulate(self, jobs):
            sorted_jobs = sorted(jobs, key=lambda x: x.arrival_time)
            
            while sorted_jobs or any(self.queues):
                if sorted_jobs and (not any(self.queues) or sorted_jobs[0].arrival_time <= self.current_time):
                    job = sorted_jobs.pop(0)
                    self.current_time = max(self.current_time, job.arrival_time)
                    self.add_job(job)
                
                for i, queue in enumerate(self.queues):
                    if queue:
                        job = queue[0]
                        if job.first_executed_time is None:
                            job.first_executed_time = self.current_time
                        execution_time = min(job.remaining_time, job.target)
                        job.remaining_time -= execution_time
                        self.current_time += execution_time
                        if job.remaining_time <= 0:
                            job.completion_time = self.current_time
                            self.job_logs.append({
                                'arrival_time': job.arrival_time,
                                'first_executed_time': job.first_executed_time,
                                'completion_time': job.completion_time,
                                'ifdone': True
                            })
                            queue.popleft()
                        else:
                            job.queue_level += 1
                            job.update_target(self.tau, job.queue_level, len(self.queues))
                            queue.popleft()
                            if job.queue_level < len(self.queues):
                                self.queues[job.queue_level].append(job)
                        break

        def calculate_metrics(self):
            total_flow_time = sum(log['completion_time'] - log['arrival_time'] for log in self.job_logs)
            average_flow_time = total_flow_time / len(self.job_logs)
            l2_norm_flow_time = math.sqrt(sum((log['completion_time'] - log['arrival_time'])**2 for log in self.job_logs))
            return average_flow_time, l2_norm_flow_time

    # Initialize jobs from the input list
    jobs = [Job(arrival_time, job_size) for arrival_time, job_size in job_list]

    # Initialize the RMLF Scheduler
    scheduler = RMLFScheduler()

    # Simulate the scheduling of jobs
    scheduler.simulate(jobs)

    # Calculate metrics
    average_flow_time, l2_norm_flow_time = scheduler.calculate_metrics()

    return average_flow_time, l2_norm_flow_time, scheduler.job_logs

# Example call with the job list
# jobs = Read_csv("data/(40, 4.073).csv")
# average_flow_time, l2_norm_flow_time, job_logs = Prmlfq(jobs)
# print(average_flow_time)
# print(l2_norm_flow_time)
