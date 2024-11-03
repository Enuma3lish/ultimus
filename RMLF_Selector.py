import pandas as pd
from typing import Optional, List, Dict
from MLF import Job, MLF

class RMLFSelector:
    def __init__(self):
        self.mlf = MLF(initial_queues=2)  # Start with 2 queues
        self.current_job: Optional[Job] = None
        self.current_time: float = 0
    
    def get_next_job(self) -> Optional[Job]:
        """Get next job from lowest non-empty queue"""
        if self.current_job and not self.current_job.is_completed():
            return self.current_job
        return self.mlf.get_job_in_lowest_queue()
    
    def process_job(self, job: Job, time_step: float):
        """Process current job and handle promotion if needed"""
        job.executing_time += time_step
        job.time_in_current_queue += time_step
        
        # Check if job should be promoted
        if self.mlf.should_promote_job(job):
            old_queue = job.current_queue
            self.mlf.promote_job(job)
            print(f"\nTime {self.current_time:.1f}: Job {job.id} promoted from Queue {old_queue} to Queue {job.current_queue}")
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
                # Update queues based on job size
                self.mlf.add_queue_if_needed(int(row['job_size']))
            
            return sorted(jobs, key=lambda x: x.arrival_time)
        except Exception as e:
            print(f"Error reading file {filepath}: {str(e)}")
            return []
    
    def print_status(self):
        """Print current status of all queues"""
        print("\nQueue Status:")
        for i, queue in enumerate(self.mlf.queues):
            jobs = [f"Job {job.id}" for job in queue.get_jobs_list()]
            print(f"  Queue {i}: {len(jobs)} jobs - {', '.join(jobs)}")
        if self.current_job:
            print(f"\nCurrently executing: Job {self.current_job.id}")
            print(f"  Queue Level: {self.current_job.current_queue}")
            print(f"  Progress: {(self.current_job.executing_time/self.current_job.processing_time)*100:.1f}%")
    
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
                self.mlf.queues[0].enqueue(new_job)  # All jobs start in first queue
                job_index += 1
            
            # Process current job
            if self.current_job:
                # Update job times
                promoted = self.process_job(self.current_job, time_step)
                
                # Check if job is complete
                if self.current_job.is_completed():
                    self.current_job.completion_time = self.current_time
                    
                    # Only try to remove if job is in active_jobs
                    if self.current_job in self.mlf.active_jobs:
                        self.mlf.active_jobs.remove(self.current_job)
                    
                    # Remove from current queue if needed
                    current_queue = self.mlf.queues[self.current_job.current_queue]
                    if self.current_job in current_queue.jobs:
                        current_queue.dequeue(self.current_job)
                    
                    self.mlf.finished_jobs.append(self.current_job)
                    print(f"\nTime {self.current_time:.1f}: Job {self.current_job.id} completed")
                    print(f"  Flow Time: {self.current_job.get_flow_time():.1f}")
                    self.current_job = None
                elif promoted:
                    # If job was promoted, it goes back to queue
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
        
        return self.mlf.calculate_metrics()

def main():
    job_file = "data/(20, 16.772).csv"
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