import csv
import random
import math
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from MLF import Job, MLF

def read_jobs_from_csv(filename):
    jobs = []
    try:
        with open(filename, 'r') as file:
            reader = csv.DictReader(file)
            for i, row in enumerate(reader):
                arrival_time = float(row['arrival_time'])
                job_size = float(row['job_size'])
                jobs.append({
                    'arrival_time': arrival_time,
                    'job_size': job_size,
                    'job_index': i
                })
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except csv.Error as e:
        print(f"Error reading CSV file: {e}")
    return jobs

def DYNAMIC(jobs: List[Dict[str, Any]], checkpoint: int = 1000, prob_greedy: float = 0.9, rmlf_prob: float = 0.9) -> Tuple[float, float]:
    """
    Dynamic scheduling function that combines FCFS and RMLF strategies.
    """
    if not jobs:
        return 0.0, 0.0

    # Calculate number of queues based on ceiling of log2(max_job_size)
    max_job_size = max(job['job_size'] for job in jobs)
    num_queues = math.ceil(math.log2(max_job_size))
    print(f"Max job size: {max_job_size}")
    print(f"Number of queues based on ceiling(log2(max_job_size)): {num_queues}")

    for i, job in enumerate(jobs):
        if 'job_index' not in job:
            job['job_index'] = i

    class DynamicScheduler:
        def __init__(self):
            self.checkpoint = checkpoint
            self.prob_greedy = prob_greedy
            self.rmlf_prob = rmlf_prob
            self.fcfs_score = float('inf')
            self.rmlf_score = float('inf')
            self.round = 1
            self.current_time = 0
            self.completed_jobs = []
            self.mlf = MLF(initial_queues=num_queues)  # Use calculated number of queues
            self.selected_algo = "FCFS"
            self.fcfs_job_scores = {}
            self.rmlf_job_scores = {}

        def select_next_job_fcfs(self) -> Optional[Job]:
            earliest_job = None
            earliest_arrival = float('inf')
            earliest_queue = None

            for queue in self.mlf.queues:
                jobs = queue.get_jobs_list()
                for job in jobs:
                    if job.arrival_time < earliest_arrival:
                        earliest_arrival = job.arrival_time
                        earliest_job = job
                        earliest_queue = queue

            if earliest_job and earliest_queue:
                earliest_queue.dequeue(earliest_job)
                return earliest_job
            return None

        def select_next_job_rmlf(self) -> Optional[Job]:
            return self.mlf.get_job_in_lowest_queue()

        def process_job(self, job: Job, time_step: float) -> bool:
            job.executing_time += time_step
            job.time_in_current_queue += time_step
            
            if self.mlf.should_promote_job(job):
                old_queue = job.current_queue
                self.mlf.promote_job(job)
                return True
            return False

        def select_algorithm(self) -> str:
            if self.round == 1:
                return "FCFS"
            elif self.round == 2:
                return "RMLF"
            else:
                if random.random() < self.prob_greedy:
                    fcfs_total = sum(self.fcfs_job_scores.values()) if self.fcfs_job_scores else float('inf')
                    rmlf_total = sum(self.rmlf_job_scores.values()) if self.rmlf_job_scores else float('inf')
                    
                    if fcfs_total < rmlf_total:
                        return "FCFS"
                    else:
                        return "RMLF" if random.random() < self.rmlf_prob else "FCFS"
                else:
                    return "RMLF" if random.random() < 0.5 else "FCFS"

        def update_scores(self):
            current_jobs = set()
            for queue in self.mlf.queues:
                for job in queue.get_jobs_list():
                    current_jobs.add(job.id)
                    age = self.current_time - job.arrival_time
                    
                    if self.selected_algo == "FCFS":
                        if job.id in self.fcfs_job_scores:
                            self.fcfs_job_scores[job.id] = self.fcfs_job_scores[job.id] * 0.5 + age
                        else:
                            self.fcfs_job_scores[job.id] = age
                    else:
                        if job.id in self.rmlf_job_scores:
                            self.rmlf_job_scores[job.id] = self.rmlf_job_scores[job.id] * 0.5 + age
                        else:
                            self.rmlf_job_scores[job.id] = age
            
            for job_id in list(self.fcfs_job_scores.keys()):
                if job_id not in current_jobs:
                    del self.fcfs_job_scores[job_id]
            
            for job_id in list(self.rmlf_job_scores.keys()):
                if job_id not in current_jobs:
                    del self.rmlf_job_scores[job_id]

        def simulate(self, jobs: List[Dict[str, Any]]) -> Tuple[float, float]:
            total_jobs = len(jobs)
            jobs_pointer = 0
            current_job = None
            
            sorted_jobs = sorted(jobs, key=lambda x: x['arrival_time'])
            next_arrival_time = sorted_jobs[0]['arrival_time'] if sorted_jobs else float('inf')
            
            while jobs_pointer < total_jobs or len(self.mlf.active_jobs) > 0:
                while jobs_pointer < total_jobs and sorted_jobs[jobs_pointer]['arrival_time'] <= self.current_time:
                    new_job = Job(
                        id=sorted_jobs[jobs_pointer]['job_index'],
                        arrival_time=sorted_jobs[jobs_pointer]['arrival_time'],
                        processing_time=sorted_jobs[jobs_pointer]['job_size']
                    )
                    self.mlf.active_jobs.add(new_job)
                    self.mlf.queues[0].enqueue(new_job)
                    jobs_pointer += 1
                    if jobs_pointer < total_jobs:
                        next_arrival_time = sorted_jobs[jobs_pointer]['arrival_time']
                    else:
                        next_arrival_time = float('inf')
                
                if self.current_time % self.checkpoint == 0:
                    prev_algo = self.selected_algo
                    self.selected_algo = self.select_algorithm()
                    if prev_algo != self.selected_algo:
                        current_job = None
                
                if not current_job:
                    current_job = self.select_next_job_fcfs() if self.selected_algo == "FCFS" else self.select_next_job_rmlf()
                
                if current_job:
                    promoted = self.process_job(current_job, 1.0)
                    
                    if current_job.is_completed():
                        current_job.completion_time = self.current_time + 1
                        self.mlf.active_jobs.remove(current_job)
                        self.completed_jobs.append({
                            'arrival_time': current_job.arrival_time,
                            'job_size': current_job.processing_time,
                            'job_index': current_job.id,
                            'completion_time': current_job.completion_time
                        })
                        current_job = None
                    elif promoted:
                        current_job = None
                    else:
                        self.mlf.queues[current_job.current_queue].enqueue(current_job)
                        current_job = None
                
                self.update_scores()
                
                if (self.current_time + 1) % self.checkpoint == 0:
                    self.round += 1
                
                self.current_time += 1
                
                if self.current_time > 1000000:
                    break
            
            flow_times = [job['completion_time'] - job['arrival_time'] for job in self.completed_jobs]
            avg_flow_time = sum(flow_times) / len(flow_times) if flow_times else 0
            l2_norm = math.sqrt(sum(t * t for t in flow_times)) if flow_times else 0
            
            return avg_flow_time, l2_norm

    scheduler = DynamicScheduler()
    return scheduler.simulate(jobs)

def main():
    filename = 'data/(20, 4.073).csv'
    jobs = read_jobs_from_csv(filename)

    if jobs:
        print(f"Loaded {len(jobs)} jobs")
        avg_flow_time, l2_norm = DYNAMIC(jobs)
        print("\nFinal Results:")
        print(f"Average Flow Time: {avg_flow_time:.3f}")
        print(f"L2 Norm of Flow Time: {l2_norm:.3f}")
    else:
        print("No jobs were loaded. Please check the input file.")

if __name__ == "__main__":
    main()