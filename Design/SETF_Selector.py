import heapq
from typing import List, Tuple, Dict

class SETFSelector:
    """
    Shortest Elapsed Time First (SETF) job selector that maintains and manages active jobs.
    Handles job selection, addition, and progress tracking for SETF scheduling.
    """
    
    def __init__(self):
        self.active_jobs = []  # min-heap: (elapsed_time, job_id, arrival_time, job_size)
        self.job_elapsed = {}  # tracks elapsed time for each job_id
        
    def add_job(self, job_id: int, arrival_time: float, job_size: float) -> None:
        """
        Add a new job to the active jobs pool.
        
        Args:
            job_id: Unique identifier for the job
            arrival_time: Time when the job arrives
            job_size: Total processing time required for the job
        """
        heapq.heappush(self.active_jobs, (0, job_id, arrival_time, job_size))
        self.job_elapsed[job_id] = 0
        
    def get_next_job(self) -> Tuple[float, int, float, float]:
        """
        Get the job with the shortest elapsed time.
        
        Returns:
            Tuple of (elapsed_time, job_id, arrival_time, job_size)
        """
        if not self.active_jobs:
            return None
        return heapq.heappop(self.active_jobs)
        
    def update_job_progress(self, job_id: int, run_time: float) -> None:
        """
        Update the progress of a job after it has run for some time.
        
        Args:
            job_id: ID of the job to update
            run_time: Amount of time the job has run
        """
        self.job_elapsed[job_id] += run_time
        
    def requeue_job(self, job_id: int, arrival_time: float, job_size: float) -> None:
        """
        Put a job back into the queue if it's not completed.
        
        Args:
            job_id: ID of the job to requeue
            arrival_time: Original arrival time of the job
            job_size: Total size of the job
        """
        heapq.heappush(self.active_jobs, 
                      (self.job_elapsed[job_id], job_id, arrival_time, job_size))
        
    def is_job_completed(self, job_id: int, job_size: float) -> bool:
        """
        Check if a job has completed its required processing time.
        
        Args:
            job_id: ID of the job to check
            job_size: Total size of the job
            
        Returns:
            bool: True if job is completed, False otherwise
        """
        return self.job_elapsed[job_id] >= job_size
        
    def has_active_jobs(self) -> bool:
        """
        Check if there are any active jobs in the queue.
        
        Returns:
            bool: True if there are active jobs, False otherwise
        """
        return len(self.active_jobs) > 0