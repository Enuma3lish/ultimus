from dataclasses import dataclass
from typing import Optional, List, Set
import math
import random
from queue import Queue

@dataclass
class Job:
    id: int
    arrival_time: float
    processing_time: float
    beta: float = 0.0
    
    # Dynamic properties
    executing_time: float = 0
    current_queue: int = 0
    current_target: float = 0
    time_in_current_queue: float = 0
    last_execution_start: float = 0
    completion_time: float = 0
    
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
        self.queue = Queue()
        self.jobs = []
        self.time_quantum = 2 ** level
    
    def enqueue(self, job: Job):
        self.queue.put(job)
        self.jobs.append(job)
        job.current_queue = self.level
        
    def dequeue(self, job=None) -> Optional[Job]:
        if job:
            if job in self.jobs:
                self.jobs.remove(job)
                temp_queue = Queue()
                while not self.queue.empty():
                    current_job = self.queue.get()
                    if current_job != job:
                        temp_queue.put(current_job)
                self.queue = temp_queue
                return job
        elif not self.queue.empty():
            job = self.queue.get()
            self.jobs.remove(job)
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
    # Constants
    TAU = 12
    
    def __init__(self, initial_queues: int = 2):
        self.queues = [MLFQueue(level) for level in range(initial_queues)]
        self.active_jobs: Set[Job] = set()
        self.finished_jobs: List[Job] = []
        self.total_jobs = 0
    
    def generate_beta(self, j: int) -> float:
        """Generate beta value for job j with proper rules"""
        if j <= 3:
            return 1  # β_j = 0 for j ≤ 3
        # For j > 3, use exponential distribution
        return -math.log(1 - random.random()) / (self.TAU * math.log(j))
    
    def calculate_target(self, job_index: int, queue_level: int) -> float:
        """Calculate target based on queue level and beta value"""
        beta = self.generate_beta(job_index)
        base_target = max(1, 2 - beta)  # T₀,ₕ = max(1, 2-βₕ)
        return (2 ** queue_level) * base_target  # Ti,j = 2^i * T₀,j
    
    def should_promote_job(self, job: Job) -> bool:
        target = self.calculate_target(job.id, job.current_queue)
        return job.time_in_current_queue >= target
    
    def promote_job(self, job: Job):
        old_queue = job.current_queue
        new_queue = min(old_queue + 1, len(self.queues) - 1)
        
        self.queues[old_queue].dequeue(job)
        self.queues[new_queue].enqueue(job)
        job.current_target = self.calculate_target(job.id, new_queue)
        
        print(f"Job {job.id} promoted: Queue {old_queue} -> {new_queue}")
        print(f"  New target: {job.current_target:.1f}")
    
    def get_job_in_lowest_queue(self) -> Optional[Job]:
        for queue in self.queues:
            if not queue.is_empty:
                return queue.dequeue()
        return None
    
    def add_queue_if_needed(self, job_size: int):
        needed_queues = math.ceil(math.log2(max(2, job_size)))
        while len(self.queues) < needed_queues:
            self.queues.append(MLFQueue(len(self.queues)))