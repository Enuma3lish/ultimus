import csv
import random
import math
from typing import Optional, List, Dict, Any, Tuple
from MLF import Job, MLF
from itertools import count

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

def DYNAMIC(jobs: List[Dict[str, Any]], checkpoint: int = 100, prob_greedy: float = 0.9) -> Tuple[float, float]:
    if not jobs:
        return 0.0, 0.0

    def fcfs_selector(mlf: MLF) -> Optional[Job]:
        """Select job based on FCFS policy"""
        earliest_job = None
        earliest_arrival = float('inf')
        
        for job in mlf.active_jobs:
            if job.arrival_time < earliest_arrival:
                earliest_arrival = job.arrival_time
                earliest_job = job
                
        return earliest_job

    def rmlf_selector(mlf: MLF) -> Optional[Job]:
        for queue in mlf.queues:
            if not queue.is_empty:
                # Get the first job in the queue (FIFO principle)
                jobs_in_queue = queue.get_jobs_list()
                if jobs_in_queue:  # Safety check
                    return jobs_in_queue[0]
        return None
    initial_queues = 1
    print(f"Starting with {initial_queues} queues")

    # Initialize variables
    jobs_pointer = 0
    selected_algo = None
    round_score = 0
    round = 1
    discount_factor = 0.5
    fcfs_score = float('inf')
    rmlf_score = float('inf')
    mlf = MLF(initial_queues=initial_queues)
    completed_jobs = []
    sorted_jobs = sorted(jobs, key=lambda x: x['arrival_time'])
    n_jobs = len(sorted_jobs)
    n_completed_jobs = 0
    
    for current_time in count():
        # Check for new job arrivals
        while (jobs_pointer < len(sorted_jobs) and 
               sorted_jobs[jobs_pointer]['arrival_time'] == current_time):
            new_job = Job(
                id=sorted_jobs[jobs_pointer]['job_index'],
                arrival_time=sorted_jobs[jobs_pointer]['arrival_time'],
                processing_time=sorted_jobs[jobs_pointer]['job_size']
            )
            mlf.insert(new_job)
            jobs_pointer += 1
        
        # Start of a round
        if current_time > 0 and current_time % checkpoint == 0:
            if round == 1:
                selected_algo = "FCFS"
            elif round == 2:
                selected_algo = "RMLF"
            else:
                p = random.random()
                if p < prob_greedy:  # greedy mode
                    if fcfs_score < rmlf_score:
                        selected_algo = "FCFS"
                    else:
                        selected_algo = "RMLF"
                else:  # discovery mode
                    selected_algo = "FCFS" if random.random() < 0.5 else "RMLF"
            
            print(f"\nTime {current_time}: Round {round} - {selected_algo}")
            round_score = 0
        
        # Select job based on algorithm
        if selected_algo == "FCFS":
            selected_job = fcfs_selector(mlf)
        else:  # RMLF
            selected_job = rmlf_selector(mlf)
        
        if selected_job:
            mlf.increase(selected_job)
            if selected_job.is_completed():
                mlf.remove(selected_job)
                completed_jobs.append({
                    'arrival_time': selected_job.arrival_time,
                    'job_size': selected_job.processing_time,
                    'job_index': selected_job.id,
                    'completion_time': current_time + 1
                })
                print(f"Time {current_time:.1f}: Job {selected_job.id} completed")
                n_completed_jobs += 1
                if n_completed_jobs == n_jobs:
                    break
        
        # Accumulate round score
        round_score += sum(current_time - job.arrival_time for job in mlf.active_jobs)
        
        # End of round
        if current_time > 0 and (current_time + 1) % checkpoint == 0:
            if selected_algo == "FCFS":
                fcfs_score = round_score if fcfs_score == float('inf') else fcfs_score * discount_factor + round_score
            else:  # RMLF
                rmlf_score = round_score if rmlf_score == float('inf') else rmlf_score * discount_factor + round_score
            
            print(f"\nEnd of Round {round}")
            print(f"FCFS Score: {fcfs_score:.2f}")
            print(f"RMLF Score: {rmlf_score:.2f}")
            print("\nQueue Status:")
            print(mlf.get_queue_status())
            round += 1
    
    # Calculate final metrics
    flow_times = [job['completion_time'] - job['arrival_time'] for job in completed_jobs]
    avg_flow_time = sum(flow_times) / len(flow_times) if flow_times else 0
    l2_norm = math.sqrt(sum(t * t for t in flow_times)) if flow_times else 0
    return avg_flow_time, l2_norm
def main():
    filename = 'data/(30, 4.073).csv'
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