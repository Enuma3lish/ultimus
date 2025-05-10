import csv
import random
import math
import os
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from MLF_6 import Job, MLF
from itertools import count
#this is test for RDD
def log_algorithm_usage(filename: str, checkpoint_data: List[Dict[str, Any]]) -> None:
    """Log algorithm usage statistics to a CSV file"""
    fieldnames = ['checkpoint_time', 'algorithm', 'fcfs_score', 'rmlf_score', 'rmlf_ratio', 'fcfs_ratio']
    try:
        with open(filename, 'w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(checkpoint_data)
    except IOError as e:
        print(f"Error writing to CSV file: {e}")

def calculate_final_ratios(checkpoint: int) -> None:
    """Calculate and save average ratios from multiple sequentially numbered run files"""
    run_files = []
    for i in range(1, 11):
        filename = f"log/{i}ratio@{checkpoint}.csv"
        if os.path.exists(filename):
            run_files.append(filename)
    if not run_files:
        print(f"No ratio result files found for checkpoint {checkpoint}")
        return

    dfs = []
    for file in run_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            print(f"Error reading file {file}: {e}")
    if not dfs:
        print("No valid data files found")
        return

    combined = pd.concat(dfs, ignore_index=True)
    grouped = combined.groupby(['checkpoint', 'arrival_rate', 'bp_parameter']).agg({
        'rmlf_ratio': 'mean',
        'fcfs_ratio': 'mean'
    }).reset_index()
    grouped['rmlf_ratio'] = grouped['rmlf_ratio'].round(1)
    grouped['fcfs_ratio'] = grouped['fcfs_ratio'].round(1)

    output_file = f"log/final_ratio@{checkpoint}.csv"
    grouped.to_csv(output_file, index=False)
    print(f"Final averaged results saved to {output_file}")

def Rdynamic(jobs: List[Dict[str, Any]], checkpoint: int, prob_greedy: float = 1.0) -> Tuple[float, float]:
    if not jobs:
        return 0.0, 0.0

    # Initialize scheduler and job lists
    mlf = MLF(initial_queues=1, first_level_quantum=6)
    sorted_jobs = sorted(jobs, key=lambda x: x['arrival_time'])
    n_jobs = len(sorted_jobs)
    jobs_pointer = 0

    # Track progress and sizes
    job_progress = {j['job_index']: 0 for j in sorted_jobs}
    job_sizes    = {j['job_index']: int(j['job_size']) for j in sorted_jobs}

    # Completed job info
    completed_jobs: List[Dict[str, Any]] = []
    n_completed_jobs = 0

    # Algorithm scoring
    fcfs_count = 0
    rmlf_count = 0
    discount_factor = 0.9
    fcfs_score = float('inf')
    rmlf_score = float('inf')
    checkpoint_data: List[Dict[str, Any]] = []

    # Initial algorithm selection state
    sel = "FCFS"
    current_round = 1
    round_score = 0.0
    round_completed_jobs = 0
    
    # Flag to track if a job was processed in the current time step
    job_processed_this_step = False

    # FCFS selector
    def fcfs_selector(_mlf: MLF) -> Optional[Job]:
        best = None
        best_time = float('inf')
        for job in _mlf.active_jobs:
            if job_progress[job.id] < job_sizes[job.id] and job.arrival_time < best_time:
                best_time = job.arrival_time
                best = job
        return best

    # Corrected RMLF selector - prioritize higher priority queues first
    def rmlf_selector(_mlf: MLF) -> Optional[Job]:
        # Start from higher priority (lower index) queues
        for queue_idx in range(len(_mlf.queues)):
            queue = _mlf.queues[queue_idx]
            if not queue.is_empty:
                # Get the first job that's not complete
                for job in queue.get_jobs_list():
                    if job_progress[job.id] < job_sizes[job.id]:
                        return job
        return None

    # Improved overload detection
    def is_queue_overloaded(_mlf: MLF) -> Tuple[bool, int]:
        if len(_mlf.queues) <= 1:
            return False, -1
            
        first_queue_length = len(_mlf.queues[0].get_jobs_list()) if not _mlf.queues[0].is_empty else 0
        if first_queue_length == 0:
            return False, -1
            
        # Check each higher-level queue separately
        for i in range(1, len(_mlf.queues)):
            queue_length = len(_mlf.queues[i].get_jobs_list()) if not _mlf.queues[i].is_empty else 0
            
            # Only consider non-empty queues
            if queue_length > 0:
                # Overload condition: either length >= 50% of first queue or length > first queue
                if queue_length >= 0.5 * first_queue_length or queue_length > first_queue_length:
                    return True, i
        
        return False, -1

    # Process one job in overloaded queue - FIXED to only process one job
    def process_job_from_overloaded_queue(_mlf: MLF, idx: int, current_time: int) -> bool:
        nonlocal n_completed_jobs, round_completed_jobs, job_processed_this_step
        
        # If we already processed a job in this time step, don't process another
        if job_processed_this_step:
            return False
            
        if idx < 0 or idx >= len(_mlf.queues):
            return False
        queue = _mlf.queues[idx]
        if queue.is_empty:
            return False
        job = queue.get_jobs_list()[0]

        # If already done, remove and count (but don't adjust progress)
        if job_progress[job.id] >= job_sizes[job.id]:
            _mlf.remove(job)
            # Only add to completed_jobs if not already there
            if not any(j['job_index'] == job.id for j in completed_jobs):
                completed_jobs.append({
                    'arrival_time': job.arrival_time,
                    'job_size': job_sizes[job.id],
                    'job_index': job.id,
                    'completion_time': current_time
                })
                n_completed_jobs += 1
            return True

        # Process 1 time unit
        job_progress[job.id] += 1
        job_processed_this_step = True
        
        # Apply MLF rules for queue promotion
        prev_lvl = job.current_queue
        _mlf.increase(job)
        
        # If job is now complete after this processing
        if job_progress[job.id] >= job_sizes[job.id]:
            _mlf.remove(job)
            completed_jobs.append({
                'arrival_time': job.arrival_time,
                'job_size': job_sizes[job.id],
                'job_index': job.id,
                'completion_time': current_time + 1
            })
            n_completed_jobs += 1
            round_completed_jobs += 1
            return True
            
        # Let MLF rules apply naturally for queue placement
        return True

    # Mitigate overload - FIXED to process only one job at a time
    def mitigate_overload(_mlf: MLF, idx: int, current_time: int) -> None:
        # Process only 1 job at a time to be fair to SRPT
        process_job_from_overloaded_queue(_mlf, idx, current_time)

    # Main loop
    for current_time in count():
        # Reset job processing flag at the start of each time step
        job_processed_this_step = False
        
        # Exit if all jobs arrived and processed
        if jobs_pointer == n_jobs and not mlf.active_jobs:
            break

        # Insert arrivals at this time
        while jobs_pointer < n_jobs and sorted_jobs[jobs_pointer]['arrival_time'] <= current_time:
            info = sorted_jobs[jobs_pointer]
            mlf.insert(Job(
                id=info['job_index'],
                arrival_time=info['arrival_time'],
                processing_time=info['job_size']
            ))
            jobs_pointer += 1

        # On checkpoint boundary
        if current_time > 0 and current_time % checkpoint == 0:
            if current_round == 1:
                sel = "FCFS"
            elif current_round == 2:
                sel = "RMLF"
            else:
                if random.random() <= prob_greedy:
                    sel = "FCFS" if fcfs_score < rmlf_score else "RMLF"
                else:
                    sel = "FCFS" if random.random() <= 0.5 else "RMLF"

            if sel == "FCFS":
                fcfs_count += 1
            else:
                rmlf_count += 1

            round_score = 0.0
            round_completed_jobs = 0
            current_round += 1

        # Verify no jobs are stuck
        for job in list(mlf.active_jobs):
            if job_progress[job.id] >= job_sizes[job.id]:
                mlf.remove(job)
                if not any(j['job_index'] == job.id for j in completed_jobs):
                    completed_jobs.append({
                        'arrival_time': job.arrival_time,
                        'job_size': job_sizes[job.id],
                        'job_index': job.id,
                        'completion_time': current_time
                    })
                    n_completed_jobs += 1

        # Check for overload in RMLF mode - but only if we haven't processed a job yet
        if sel == "RMLF" and len(mlf.queues) > 1 and not job_processed_this_step:
            overloaded, idx = is_queue_overloaded(mlf)
            if overloaded:
                mitigate_overload(mlf, idx, current_time)

        # Only select and execute a job if we haven't processed one already this time step
        if not job_processed_this_step:
            job = fcfs_selector(mlf) if sel == "FCFS" else rmlf_selector(mlf)
            if job and job.arrival_time <= current_time and job_progress[job.id] < job_sizes[job.id]:
                job_progress[job.id] += 1
                job_processed_this_step = True
                mlf.increase(job)

                # On completion
                if job_progress[job.id] >= job_sizes[job.id]:
                    mlf.remove(job)
                    completed_jobs.append({
                        'arrival_time': job.arrival_time,
                        'job_size': job_sizes[job.id],
                        'job_index': job.id,
                        'completion_time': current_time + 1
                    })
                    n_completed_jobs += 1
                    round_completed_jobs += 1

        # Accumulate waiting cost for active jobs
        round_score += sum(current_time - j.arrival_time for j in mlf.active_jobs)

        # End-of-round scoring
        if current_time > 0 and (current_time + 1) % checkpoint == 0:
            # Prevent division by zero
            norm_score = round_score / max(round_completed_jobs, 1)
            if sel == "FCFS":
                fcfs_score = norm_score if fcfs_score == float('inf') else fcfs_score * discount_factor + norm_score
            else:
                rmlf_score = norm_score if rmlf_score == float('inf') else rmlf_score * discount_factor + norm_score

            total_rounds = fcfs_count + rmlf_count
            r_ratio = (rmlf_count / total_rounds * 100) if total_rounds else 0.0
            f_ratio = (fcfs_count / total_rounds * 100) if total_rounds else 0.0

            checkpoint_data.append({
                'checkpoint_time': current_time + 1,
                'algorithm': sel,
                'fcfs_score': fcfs_score,
                'rmlf_score': rmlf_score,
                'rmlf_ratio': round(r_ratio, 1),
                'fcfs_ratio': round(f_ratio, 1)
            })

    # Verify all jobs are accounted for
    if n_completed_jobs != n_jobs:
        print(f"Warning: Expected {n_jobs} completed jobs, but found {n_completed_jobs}")
    
    # Compute final metrics
    if not completed_jobs:
        return 0.0, 0.0
        
    flow_times = [c['completion_time'] - c['arrival_time'] for c in completed_jobs]
    avg_flow_time = sum(flow_times) / len(flow_times) if flow_times else 0.0
    l2_norm = math.sqrt(sum(t*t for t in flow_times)) if flow_times else 0.0

    return avg_flow_time, l2_norm