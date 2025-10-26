from dataclasses import dataclass
from typing import Optional, List, Set
import math
import random

@dataclass
class Job:
    id: int
    arrival_time: float
    processing_time: float
    beta: float = 0.0
    
    # Dynamic properties
    executing_time: float = 0.0
    current_queue: int = 0
    time_in_current_queue: float = 0.0
    completion_time: float = 0.0
    
    def get_remaining_time(self) -> float:
        return self.processing_time - self.executing_time
    
    def is_completed(self) -> bool:
        return self.executing_time >= self.processing_time
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Job):
            return False
        return self.id == other.id

class MLFQueue:
    def __init__(self, level: int):
        self.level = level
        self.jobs: List[Job] = []
    
    def enqueue(self, job: Job):
        self.jobs.append(job)
        job.current_queue = self.level
        
    def dequeue(self, job: Optional[Job] = None) -> Optional[Job]:
        if job:
            if job in self.jobs:
                self.jobs.remove(job)
                return job
        elif self.jobs:
            job = self.jobs.pop(0)
            return job
        return None
    
    @property
    def is_empty(self) -> bool:
        return len(self.jobs) == 0
    
    @property
    def length(self) -> int:
        return len(self.jobs)
    
    def get_jobs_list(self) -> List[Job]:
        return self.jobs.copy()

class MLF:
    TAU = 12
    
    def __init__(self, initial_queues: int = 1, first_level_quantum: float = 2.0):
        self.queues = [MLFQueue(level) for level in range(initial_queues)]
        self.active_jobs: Set[Job] = set()
        self.finished_jobs: List[Job] = []
        self.total_jobs = 0
        self.first_level_quantum = first_level_quantum
    
    def insert(self, job: Job):
        """Insert job into lowest queue"""
        self.total_jobs += 1
        job.beta = self.generate_beta(self.total_jobs)
        job.current_queue = 0
        job.time_in_current_queue = 0
        
        self.queues[0].enqueue(job)
        self.active_jobs.add(job)
        
    def remove(self, job: Job):
        """Remove completed job"""
        if job in self.active_jobs:
            self.active_jobs.remove(job)
            self.finished_jobs.append(job)
            current_queue = self.queues[job.current_queue]
            current_queue.dequeue(job)
    
    def increase(self, job: Job):
        """Process job and handle MLFQ queue transitions"""
        if job not in self.active_jobs:
            return
            
        job.executing_time += 1
        job.time_in_current_queue += 1
        
        # Check if job has used its time quantum
        target = self.calculate_target(job)
        if job.time_in_current_queue >= target:
            current_queue = job.current_queue
            next_queue = current_queue + 1
            
            # Add new queue if needed
            if next_queue >= len(self.queues):
                self.queues.append(MLFQueue(next_queue))
            
            # Move to next lower priority queue (higher number)
            self.queues[current_queue].dequeue(job)
            self.queues[next_queue].enqueue(job)
            job.current_queue = next_queue
            job.time_in_current_queue = 0
    
    def generate_beta(self, job_index: int) -> float:
        if job_index <= 3:
            return 2.0
        return -math.log(1 - random.random()) / (self.TAU * math.log(job_index))
    
    def calculate_target(self, job: Job) -> float:
        if job.current_queue == 0:
            base_target = max(1, self.first_level_quantum - job.beta)
        else:
            base_target = max(1, 2 - job.beta)
        
        # Apply exponential growth for lower priority queues
        if job.current_queue == 0:
            return base_target
        else:
            return 2 ** (job.current_queue - 1) * base_target * 2
    
    def get_queue_status(self) -> str:
        status = []
        for i, queue in enumerate(self.queues):
            jobs_info = [f"{job.id}({job.get_remaining_time():.1f})" for job in queue.get_jobs_list()]
            status.append(f"Queue {i}: {len(jobs_info)} jobs - [{', '.join(jobs_info)}]")
        return "\n".join(status)