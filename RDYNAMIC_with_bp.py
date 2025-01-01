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

def log_algorithm_usage(filename: str, checkpoint_data: List[Dict[str, Any]]) -> None:
    fieldnames = ['checkpoint_time', 'algorithm', 'fcfs_score', 'rmlf_score', 'rmlf_ratio', 'fcfs_ratio']
    
    try:
        with open(filename, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(checkpoint_data)
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

def log_time_slots(filename: str, time_slots: List[Dict[str, Any]]) -> None:
    fieldnames = ['time_slot', 'executed_job_id']
    try:
        with open(filename, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(time_slots)
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

def log_fcfs_job_sizes(filename: str, fcfs_jobs: List[Dict[str, Any]]) -> None:
    """
    Log information about jobs executed by FCFS algorithm.
    
    Args:
        filename: Name of the output CSV file
        fcfs_jobs: List of dictionaries containing FCFS job execution data
    """
    fieldnames = ['time', 'job_id', 'job_size', 'completion_percentage']
    try:
        with open(filename, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(fcfs_jobs)
    except IOError as e:
        print(f"Error writing FCFS job sizes to CSV file: {e}")

def RDYNAMIC_bp(jobs: List[Dict[str, Any]],H:int, checkpoint: int) -> Tuple[float, float]:
    if not jobs:
        return 0.0, 0.0

    def fcfs_selector(mlf: MLF) -> Optional[Job]:
        earliest_job = None
        earliest_arrival = float('inf')
        
        for job in mlf.active_jobs:
            if job.arrival_time < earliest_arrival and not job.is_completed():
                earliest_arrival = job.arrival_time
                earliest_job = job
                
        return earliest_job

    def rmlf_selector(mlf: MLF) -> Optional[Job]:
        for queue in mlf.queues:
            if not queue.is_empty:
                jobs_in_queue = queue.get_jobs_list()
                for job in jobs_in_queue:
                    if not job.is_completed():
                        return job
        return None
    
    initial_queues = 1
    print(f"Starting with {initial_queues} queues")

    # Initialize variables
    jobs_pointer = 0
    selected_algo = "FCFS"
    round_score = 0
    current_round = 1
    round_start_time = 0
    discount_factor = 0.5
    fcfs_score = float('inf')
    rmlf_score = float('inf')
    mlf = MLF(initial_queues=initial_queues)
    completed_jobs = []
    sorted_jobs = sorted(jobs, key=lambda x: x['arrival_time'])
    n_jobs = len(sorted_jobs)
    n_completed_jobs = 0
    
    # Track completed jobs per round
    round_completed_jobs = 0
    
    checkpoint_data = []
    fcfs_count = 0
    rmlf_count = 0
    
    # Initialize time slot logging
    time_slot_log = []
    current_job_id = None
    
    # Track job progress
    job_progress = {job['job_index']: 0 for job in sorted_jobs}
    job_sizes = {job['job_index']: int(job['job_size']) for job in sorted_jobs}
    
    # Initialize FCFS job size tracking
    fcfs_job_log = []
    
    for current_time in count():
        # Check for new job arrivals
        while (jobs_pointer < len(sorted_jobs) and 
               sorted_jobs[jobs_pointer]['arrival_time'] <= current_time):
            new_job = Job(
                id=sorted_jobs[jobs_pointer]['job_index'],
                arrival_time=sorted_jobs[jobs_pointer]['arrival_time'],
                processing_time=sorted_jobs[jobs_pointer]['job_size']
            )
            mlf.insert(new_job)
            jobs_pointer += 1
        
        # Start of a round
        if current_time > 0 and current_time % checkpoint == 0:
            round_start_time = current_time
            if current_round == 1:
                selected_algo = "FCFS"
            elif current_round == 2:
                selected_algo = "RMLF"
            else:
                p = random.random()
                print(p)
                if H<= pow(2,9):  # greedy mode
                    if p <1.0:
                       selected_algo = "FCFS"
                    else:
                        selected_algo = "RMLF"
                else: # max_size> pow(2,9)
                    if p <0.9:
                       selected_algo = "RMLF"
                    else:
                        selected_algo = "FCFS"
            if selected_algo == "FCFS":
                fcfs_count += 1
            else:
                rmlf_count += 1        
            print(f"\nTime {current_time}: Round {current_round} - {selected_algo}")
            round_score = 0
            round_completed_jobs = 0
        
        # Select job based on algorithm
        if selected_algo == "FCFS":
            selected_job = fcfs_selector(mlf)
        else:  # RMLF
            selected_job = rmlf_selector(mlf)

        # Update current_job_id based on selection and progress
        if (selected_job and 
            selected_job.arrival_time <= current_time and 
            job_progress[selected_job.id] < job_sizes[selected_job.id]):
            current_job_id = selected_job.id
        else:
            current_job_id = None
            selected_job = None

        # Log time slot
        time_slot_log.append({
            'time_slot': float(current_time),
            'executed_job_id': str(current_job_id) if current_job_id is not None else ''
        })
        
        # Process selected job and log FCFS job information
        if selected_job and current_job_id is not None:
            job_progress[current_job_id] += 1
            mlf.increase(selected_job)
            
            # Log FCFS job size information
            if selected_algo == "FCFS":
                completion_percentage = (job_progress[current_job_id] / job_sizes[current_job_id]) * 100
                fcfs_job_log.append({
                    'time': float(current_time),
                    'job_id': str(current_job_id),
                    'job_size': float(job_sizes[current_job_id]),
                    'completion_percentage': float(f"{completion_percentage:.1f}")
                })
            
            # Check if job is completed
            if job_progress[current_job_id] >= job_sizes[current_job_id]:
                mlf.remove(selected_job)
                completed_jobs.append({
                    'arrival_time': selected_job.arrival_time,
                    'job_size': selected_job.processing_time,
                    'job_index': selected_job.id,
                    'completion_time': current_time + 1
                })
                print(f"Time {current_time:.1f}: Job {selected_job.id} completed")
                n_completed_jobs += 1
                round_completed_jobs += 1
                if n_completed_jobs == n_jobs:
                    # Add final empty time slot
                    time_slot_log.append({
                        'time_slot': float(current_time + 1),
                        'executed_job_id': ''
                    })
                    break
        
        # Calculate round score based on waiting times
        round_score += sum(current_time - max(job.arrival_time, round_start_time) for job in mlf.active_jobs)
                    
        # End of round
        if current_time > 0 and (current_time + 1) % checkpoint == 0:
            normalized_score = round_score / max(round_completed_jobs, 1)
            
            if selected_algo == "FCFS":
                fcfs_score = normalized_score if fcfs_score == float('inf') else fcfs_score * discount_factor + normalized_score
            else:  # RMLF
                rmlf_score = normalized_score if rmlf_score == float('inf') else rmlf_score * discount_factor + normalized_score
            
            total_rounds = fcfs_count + rmlf_count
            if total_rounds > 0:
                rmlf_ratio = float((rmlf_count / total_rounds) * 100)
                fcfs_ratio = float((fcfs_count / total_rounds) * 100)
            else:
                rmlf_ratio = 0.0
                fcfs_ratio = 0.0
            
            checkpoint_data.append({
                'checkpoint_time': current_time + 1,
                'algorithm': selected_algo,
                'fcfs_score': fcfs_score if fcfs_score != float('inf') else 0,
                'rmlf_score': rmlf_score if rmlf_score != float('inf') else 0,
                'rmlf_ratio': float(f"{rmlf_ratio:.1f}"),
                'fcfs_ratio': float(f"{fcfs_ratio:.1f}")
            })
            
            print(f"\nEnd of Round {current_round}")
            print(f"Round completed jobs: {round_completed_jobs}")
            print(f"Raw round score: {round_score:.2f}")
            print(f"Normalized round score: {normalized_score:.2f}")
            print(f"FCFS Score: {fcfs_score:.2f}")
            print(f"RMLF Score: {rmlf_score:.2f}")
            print(f"Algorithm Usage - RMLF: {rmlf_ratio:.1f}%, FCFS: {fcfs_ratio:.1f}%")
            print("\nQueue Status:")
            print(mlf.get_queue_status())
            current_round += 1
    
    # Write logs
    log_algorithm_usage(f'BP_algorithm_usage_log_{len(jobs)}jobs.csv', checkpoint_data)
    log_time_slots('Rdy_time_slot_log.csv', time_slot_log)
    log_fcfs_job_sizes('fcfs_job_sizes_log.csv', fcfs_job_log)
    
    flow_times = [job['completion_time'] - job['arrival_time'] for job in completed_jobs]
    avg_flow_time = sum(flow_times) / len(flow_times) if flow_times else 0
    l2_norm = math.sqrt(sum(t * t for t in flow_times)) if flow_times else 0
    return avg_flow_time, l2_norm
def main():
     filename = 'data/(20, 7.918).csv'  # Replace with your input file name
     jobs = read_jobs_from_csv(filename)
     if jobs:
         avg_flow_time, l2_norm = RDYNAMIC_bp(jobs,pow(2,9),128)
         print(f"Average Flow Time: {avg_flow_time}")
         print(f"L2 Norm of Flow Time: {l2_norm}")
     else:
         print("No jobs were loaded. Please check the input file.")
if __name__ == "__main__":
     main()