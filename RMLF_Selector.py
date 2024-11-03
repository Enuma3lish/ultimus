import math
import pandas as pd
from typing import Optional, List, Dict
from MLF import Job, MLF

class RMLFSelector:
    def __init__(self):
        self.mlf = MLF(initial_queues=2)  # Start with 2 queues
        self.current_job: Optional[Job] = None
        self.current_time: float = 0
        self.job_ages = {}  # Track job ages
    
    def get_next_job(self) -> Optional[Job]:
        """Get next job from lowest non-empty queue"""
        if self.current_job and not self.current_job.is_completed():
            return self.current_job
            
        # Get job from lowest queue per MLF implementation
        self.current_job = self.mlf.get_job_in_lowest_queue()
        if self.current_job and self.current_job.id not in self.job_ages:
            self.job_ages[self.current_job.id] = 0
        return self.current_job
    
    def process_job(self, job: Job, time_step: float):
        """Process current job and handle promotion if needed"""
        job.executing_time += time_step
        job.time_in_current_queue += time_step
        
        # Update job age using MLF's promotion criteria
        if job.id not in self.job_ages:
            self.job_ages[job.id] = 0
            
        current_age = self.job_ages[job.id]
        new_age = current_age * 0.5 + time_step
        self.job_ages[job.id] = new_age
        
        # Check if job should be promoted using MLF's criteria
        if self.mlf.should_promote_job(job):
            old_queue = job.current_queue
            # Use MLF's promote_job method
            self.mlf.promote_job(job)
            
            # Reset age in new queue
            self.job_ages[job.id] = 0
            print(f"  Age at promotion: {new_age:.1f}")
            return True
        return False
    
    def load_jobs_from_csv(self, filepath: str) -> List[Job]:
        """Load jobs from CSV file"""
        jobs = []
        try:
            df = pd.read_csv(filepath)
            for i, row in df.iterrows():
                job = Job(
                    id=i+1,
                    arrival_time=float(row['arrival_time']),
                    processing_time=float(row['job_size'])
                )
                jobs.append(job)
                self.mlf.total_jobs += 1
                # Use MLF's queue addition logic
                self.mlf.add_queue_if_needed(int(row['job_size']))
            
            return sorted(jobs, key=lambda x: x.arrival_time)
        except Exception as e:
            print(f"Error reading file {filepath}: {str(e)}")
            return []
    
    def print_status(self):
        """Print current status of all queues"""
        print("\nQueue Status:")
        for i, queue in enumerate(self.mlf.queues):
            jobs = queue.get_jobs_list()
            print(f"Queue {i}: {len(jobs)} jobs")
            for job in jobs:
                age = self.job_ages.get(job.id, 0)
                print(f"  Job {job.id}: Age={age:.1f}, Queue Limit={2**i}")
        
        if self.current_job:
            print(f"\nCurrently executing: Job {self.current_job.id}")
            print(f"  Queue Level: {self.current_job.current_queue}")
            print(f"  Progress: {(self.current_job.executing_time/self.current_job.processing_time)*100:.1f}%")
            print(f"  Age: {self.job_ages.get(self.current_job.id, 0):.1f}")
    
    def simulate_jobs(self, jobs: List[Job]) -> Dict:
        """Run simulation with provided jobs"""
        job_index = 0
        time_step = 1.0
        
        while (job_index < len(jobs) or self.current_job or 
               any(not q.is_empty for q in self.mlf.queues)):
            
            # Handle new job arrivals
            while job_index < len(jobs) and jobs[job_index].arrival_time <= self.current_time:
                new_job = jobs[job_index]
                print(f"\nTime {self.current_time:.1f}: Job {new_job.id} arrived")
                self.mlf.active_jobs.add(new_job)
                self.mlf.queues[0].enqueue(new_job)  # Start in first queue
                self.job_ages[new_job.id] = 0
                job_index += 1
            
            # Process current job
            if self.current_job:
                promoted = self.process_job(self.current_job, time_step)
                
                if self.current_job.is_completed():
                    self.current_job.completion_time = self.current_time
                    
                    # Find and remove from active_jobs
                    active_job = None
                    for job in self.mlf.active_jobs:
                        if job.id == self.current_job.id:
                            active_job = job
                            break
                    
                    if active_job:
                        self.mlf.active_jobs.remove(active_job)
                    
                    # Clean up tracking
                    if self.current_job.id in self.job_ages:
                        del self.job_ages[self.current_job.id]
                    
                    # Handle queue removal
                    try:
                        if self.current_job in self.mlf.queues[self.current_job.current_queue].jobs:
                            self.mlf.queues[self.current_job.current_queue].dequeue(self.current_job)
                    except (IndexError, KeyError):
                        pass
                    
                    # Add to finished jobs
                    self.mlf.finished_jobs.append(self.current_job)
                    print(f"\nTime {self.current_time:.1f}: Job {self.current_job.id} completed")
                    print(f"  Flow Time: {self.current_job.completion_time - self.current_job.arrival_time:.1f}")
                    self.current_job = None
                elif promoted:
                    self.current_job = None
            
            # Get next job if needed
            if not self.current_job:
                self.current_job = self.get_next_job()
                if self.current_job:
                    print(f"\nTime {self.current_time:.1f}: Starting Job {self.current_job.id} from Queue {self.current_job.current_queue}")
            
            # Print status periodically
            if self.current_time % 10 == 0:
                self.print_status()
            
            self.current_time += time_step
        
        # Calculate metrics using MLF's calculated_metrics
        return {
            'average_flow_time': sum((job.completion_time - job.arrival_time) 
                                   for job in self.mlf.finished_jobs) / len(self.mlf.finished_jobs),
            'l2_norm_flow_time': math.sqrt(sum((job.completion_time - job.arrival_time) ** 2 
                                             for job in self.mlf.finished_jobs)),
            'total_jobs': len(self.mlf.finished_jobs)
        }

def main():
    job_file = "data/(20, 4.073).csv"
    selector = RMLFSelector()
    
    jobs = selector.load_jobs_from_csv(job_file)
    if not jobs:
        print("No jobs loaded. Exiting.")
        return
    
    print(f"\nInitial number of queues: {len(selector.mlf.queues)}")
    print("\nStarting Simulation...")
    metrics = selector.simulate_jobs(jobs)
    
    print("\nFinal Performance Metrics:")
    print(f"Average Flow Time: {metrics['average_flow_time']:.3f}")
    print(f"L2 Norm Flow Time: {metrics['l2_norm_flow_time']:.3f}")
    print(f"Total Jobs Completed: {metrics['total_jobs']}")

if __name__ == "__main__":
    main()

