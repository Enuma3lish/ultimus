import csv
import random
import math
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from MLF import Job, MLF

def read_jobs_from_csv(filename: str) -> List[Dict[str, Any]]:
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
    """Dynamic scheduling function that combines FCFS and RMLF strategies."""
    if not jobs:
        return 0.0, 0.0

    # Calculate number of queues based on max job size
    max_job_size = max(job['job_size'] for job in jobs)
    num_queues = math.ceil(math.log2(max_job_size))
    print(f"Max job size: {max_job_size}")
    print(f"Number of queues based on ceiling(log2(max_job_size)): {num_queues}")

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
            self.mlf = MLF(initial_queues=num_queues)
            self.selected_algo = "FCFS"
            self.fcfs_job_scores = {}
            self.rmlf_job_scores = {}
            self.job_ages = {}

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
                if earliest_job.id not in self.job_ages:
                    self.job_ages[earliest_job.id] = 0
                return earliest_job
            return None

        def select_next_job_rmlf(self) -> Optional[Job]:
            return self.mlf.get_job_in_lowest_queue()

        def update_job_age(self, job: Job, time_step: float):
            if job.id not in self.job_ages:
                self.job_ages[job.id] = 0
            
            current_age = self.job_ages[job.id]
            new_age = current_age * 0.5 + time_step
            self.job_ages[job.id] = new_age
            
            queue_limit = 2 ** job.current_queue
            if new_age >= queue_limit:
                old_queue = job.current_queue
                new_queue = min(old_queue + 1, len(self.mlf.queues) - 1)
                
                try:
                    if job in self.mlf.queues[old_queue].jobs:
                        self.mlf.queues[old_queue].dequeue(job)
                    self.mlf.queues[new_queue].enqueue(job)
                    
                    job.current_queue = new_queue
                    self.job_ages[job.id] = 0
                    
                    print(f"\nTime {self.current_time:.1f}: Job {job.id} promoted from Queue {old_queue} to Queue {new_queue}")
                    print(f"  Age at promotion: {new_age:.1f}")
                    return True
                except IndexError:
                    self.mlf.queues[-1].enqueue(job)
                    return False
            return False

        def process_job(self, job: Job, time_step: float) -> bool:
            job.executing_time += time_step
            
            if self.selected_algo == "FCFS":
                return self.update_job_age(job, time_step)
            else:
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
            
            while jobs_pointer < total_jobs or len(self.mlf.active_jobs) > 0:
                # Handle new job arrivals
                while jobs_pointer < total_jobs and sorted_jobs[jobs_pointer]['arrival_time'] <= self.current_time:
                    new_job = Job(
                        id=sorted_jobs[jobs_pointer]['job_index'],
                        arrival_time=sorted_jobs[jobs_pointer]['arrival_time'],
                        processing_time=sorted_jobs[jobs_pointer]['job_size']
                    )
                    self.mlf.active_jobs.add(new_job)
                    self.mlf.queues[0].enqueue(new_job)
                    self.job_ages[new_job.id] = 0
                    jobs_pointer += 1
                
                # Start of round
                if self.current_time % self.checkpoint == 0:
                    prev_algo = self.selected_algo
                    self.selected_algo = self.select_algorithm()
                    print(f"\nTime {self.current_time}: Round {self.round} - {self.selected_algo}")
                    if prev_algo != self.selected_algo:
                        current_job = None
                
                # Process jobs
                if not current_job:
                    if self.selected_algo == "FCFS":
                        current_job = self.select_next_job_fcfs()
                    else:
                        current_job = self.select_next_job_rmlf()
                
                if current_job:
                    promoted = self.process_job(current_job, 1.0)
                    
                    if current_job.is_completed():
                        current_job.completion_time = self.current_time + 1
                        
                        # Get the actual job object from active_jobs
                        active_job = None
                        for job in self.mlf.active_jobs:
                            if job.id == current_job.id:
                                active_job = job
                                break
                        
                        # Remove from active_jobs if found
                        if active_job:
                            self.mlf.active_jobs.remove(active_job)
                        
                        # Clean up job tracking
                        if current_job.id in self.job_ages:
                            del self.job_ages[current_job.id]
                        
                        # Remove from current queue
                        try:
                            current_queue = self.mlf.queues[current_job.current_queue]
                            if current_job in current_queue.jobs:
                                current_queue.dequeue(current_job)
                        except (IndexError, KeyError):
                            pass
                        
                        self.completed_jobs.append({
                            'arrival_time': current_job.arrival_time,
                            'job_size': current_job.processing_time,
                            'job_index': current_job.id,
                            'completion_time': current_job.completion_time
                        })
                        print(f"\nTime {self.current_time:.1f}: Job {current_job.id} completed")
                        current_job = None
                    elif promoted:
                        current_job = None
                    else:
                        try:
                            self.mlf.queues[current_job.current_queue].enqueue(current_job)
                        except IndexError:
                            self.mlf.queues[-1].enqueue(current_job)
                        current_job = None
                
                self.update_scores()
                
                if (self.current_time + 1) % self.checkpoint == 0:
                    print("\nQueue Status:")
                    for i, queue in enumerate(self.mlf.queues):
                        jobs = queue.get_jobs_list()
                        print(f"Queue {i}: {len(jobs)} jobs")
                        for job in jobs:
                            age = self.job_ages.get(job.id, 0)
                            print(f"  Job {job.id}: Age={age:.1f}, Queue Limit={2**i}")
                    self.round += 1
                
                self.current_time += 1
                
                if self.current_time > 1000000:
                    print("Warning: Maximum simulation time reached")
                    break
            
            flow_times = [job['completion_time'] - job['arrival_time'] 
                         for job in self.completed_jobs]
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