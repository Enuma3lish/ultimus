import math
import pandas as pd
import csv
from typing import Optional, List, Dict, Any, Tuple
from MLF import Job, MLF
from itertools import count

def read_jobs_from_csv(filename: str) -> List[Dict[str, Any]]:
    jobs = []
    try:
        with open(filename, 'r') as file:
            df = pd.read_csv(filename)
            for i, row in df.iterrows():
                arrival_time = float(row['arrival_time'])
                job_size = float(row['job_size'])
                jobs.append({
                    'arrival_time': arrival_time,
                    'job_size': job_size,
                    'job_index': i
                })
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return jobs

def RMLF(jobs: List[Dict[str, Any]]) -> Tuple[float, float]:
    if not jobs:
        return 0.0, 0.0

    # Create log file and write header
    # with open('RMLF_time_slot_log.csv', 'w', newline='') as log_file:
    #     log_writer = csv.writer(log_file)
    #     log_writer.writerow(['time_slot', 'executed_job_id'])

    def rmlf_selector(mlf: MLF) -> Optional[Job]:
        for queue in mlf.queues:
            if not queue.is_empty:
                jobs_in_queue = queue.get_jobs_list()
                for job in jobs_in_queue:
                    if job.processing_time > 0:
                        return job
        return None

    # def log_execution(time_slot: int, job_id: Optional[int]):
    #     with open('RMLF_time_slot_log.csv', 'a', newline='') as log_file:
    #         log_writer = csv.writer(log_file)
    #         log_writer.writerow([time_slot, '' if job_id is None else job_id])

    mlf = MLF(initial_queues=1)
    completed_jobs = []
    sorted_jobs = sorted(jobs, key=lambda x: x['arrival_time'])
    jobs_pointer = 0
    n_jobs = len(sorted_jobs)
    n_completed_jobs = 0
    
    # Main simulation loop
    for current_time in count():
        # Insert new jobs that have arrived
        while (jobs_pointer < len(sorted_jobs) and 
               sorted_jobs[jobs_pointer]['arrival_time'] == current_time):
            new_job = Job(
                id=sorted_jobs[jobs_pointer]['job_index'],
                arrival_time=sorted_jobs[jobs_pointer]['arrival_time'],
                processing_time=sorted_jobs[jobs_pointer]['job_size']
            )
            mlf.insert(new_job)
            jobs_pointer += 1
        
        # Select and process job
        selected_job = rmlf_selector(mlf)
        if selected_job:
            # Log the execution
            #log_execution(current_time, selected_job.id)
            
            # Process the job
            mlf.increase(selected_job)   
            if selected_job.is_completed():
                mlf.remove(selected_job)
                completed_jobs.append({
                    'arrival_time': selected_job.arrival_time,
                    'job_size': selected_job.processing_time,
                    'job_index': selected_job.id,
                    'completion_time': current_time + 1
                })
                n_completed_jobs += 1
                if n_completed_jobs == n_jobs:
                    # Log the final time slot
                    #log_execution(current_time + 1, None)
                    break
    
    # Calculate metrics
    flow_times = [job['completion_time'] - job['arrival_time'] for job in completed_jobs]
    avg_flow_time = sum(flow_times) / len(flow_times) if flow_times else 0
    l2_norm = math.sqrt(sum(t * t for t in flow_times)) if flow_times else 0
    
    return avg_flow_time, l2_norm