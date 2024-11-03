from dataclasses import dataclass
from typing import Optional, List, Set
import math
import random
from queue import Queue

@dataclass
class Job:
    id: int
    release_time: float      # rj - known only at arrival
    processing_time: float   # xj - may or may not be known at arrival
    arrival_time: float      # When job entered system
    waiting_time: float = 0  # Time spent waiting in queues
    
    # Dynamic properties - updated as job runs
    executing_time: float = 0    # Time spent actually executing
    current_queue: int = 0       # Current Qi
    current_target: float = 0    # Current Ti,j
    beta: float = 0             # βj - determined on arrival
    last_execution_start: float = 0
    
    def get_remaining_time(self) -> float:
        # yj(t) = xj - wj(t)
        # where wj(t) is the amount of time that RMLF has run Jj before time t
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
    def length(self) -> int:
        return len(self.jobs)
    
    def get_jobs_list(self) -> List[Job]:
        return self.jobs.copy()

class MLF:
    # Constants
    TAU = 12
    
    def __init__(self, initial_queues: int = 2):
        # Dynamic system state
        self.queues = []  # Start with just Q0, expand as needed
        self.queues.append(MLFQueue(level=0))
        self.current_job: Optional[Job] = None
        self.current_time: float = 0
        self.active_jobs: Set[Job] = set()
    
    def generate_beta(self, j: int) -> float:
        # Modified beta generation
        if j <= 3:
            return 0  # Return 0 for jobs with index ≤ 3
        # For j > 3, use exponential distribution
        return -math.log(1 - random.random()) / (self.TAU * math.log(j))
    
    def on_job_progress(self, running_job: Job, time_delta: float):
        # Update executing time (not waiting time)
        running_job.executing_time += time_delta
        
        if running_job.executing_time >= running_job.current_target:
            old_queue = running_job.current_queue
            new_queue = old_queue + 1
            
            # Update waiting time when moving to new queue
            running_job.waiting_time += self.current_time - (
                running_job.arrival_time + running_job.executing_time)
            
            # Add new queue if needed
            while len(self.queues) <= new_queue:
                self.queues.append(MLFQueue(level=len(self.queues)))
            
            self.queues[old_queue].dequeue(running_job)
            self.queues[new_queue].enqueue(running_job)
            
            running_job.current_target *= 2
            running_job.current_queue = new_queue
            
            self.schedule_next()
    
    def on_job_arrival(self, new_job: Job):
        self.current_time = new_job.arrival_time
        
        # Initialize time tracking
        new_job.executing_time = 0
        new_job.waiting_time = 0
        
        # Generate beta with modified rule
        new_job.beta = self.generate_beta(new_job.id)
        
        # Set initial target
        new_job.current_target = max(1, 2 - new_job.beta)
        new_job.current_queue = 0
        
        self.queues[0].enqueue(new_job)
        self.active_jobs.add(new_job)
        
        if self.queues[0].length == 1 and self.current_job is not None:
            self.preempt_current_job()
            self.start_job(new_job)
    
    def preempt_current_job(self):
        if self.current_job is not None:
            # Update waiting time for preempted job
            self.current_job.waiting_time += self.current_time - (
                self.current_job.arrival_time + self.current_job.executing_time)
            self.current_job = None
    
    def start_job(self, job: Job):
        self.current_job = job
        # Record start of execution period
        job.last_execution_start = self.current_time
    
    def on_job_completion(self, completed_job: Job):
        # Final time updates
        completed_job.executing_time += self.current_time - completed_job.last_execution_start
        
        self.queues[completed_job.current_queue].dequeue(completed_job)
        self.active_jobs.remove(completed_job)
        
        if completed_job == self.current_job:
            self.current_job = None
            self.schedule_next()
    
    def schedule_next(self):
        """Schedule next job from lowest non-empty queue"""
        for queue in self.queues:
            if not queue.is_empty:
                next_job = queue.dequeue()
                if next_job:
                    self.start_job(next_job)
                    return

    def add_queue_if_needed(self, job_size: int):
        needed_queues = math.ceil(math.log2(max(2, job_size)))
        while len(self.queues) < needed_queues:
            self.queues.append(MLFQueue(len(self.queues)))