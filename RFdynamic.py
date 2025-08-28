import csv
import random
import math
import os
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from MLF_2 import Job, MLF
from itertools import count

def Rdynamic(jobs: List[Dict[str, Any]], checkpoint = 100) -> Tuple[float, float]:
    if not jobs:
        return 0.0, 0.0

    def fcfs_selector(mlf: MLF) -> Optional[Job]:
        """Select next job using FCFS policy"""
        earliest_job = None
        earliest_arrival = float('inf')
        
        for job in mlf.active_jobs:
            if job.arrival_time < earliest_arrival and not job.is_completed():
                earliest_arrival = job.arrival_time
                earliest_job = job
                
        return earliest_job

    def rmlf_selector(mlf: MLF) -> Optional[Job]:
        """Select next job using RMLF policy"""
        for queue in mlf.queues:
            if not queue.is_empty:
                jobs_in_queue = queue.get_jobs_list()
                for job in jobs_in_queue:
                    if not job.is_completed():
                        return job
        return None
    
    # Initialize MLF and variables
    initial_queues = 1
    #print(f"Starting with {initial_queues} queues")
    
    jobs_pointer = 0
    selected_algo = "FCFS"
    round_score = 0
    current_round = 1
    round_start_time = 0
    discount_factor = 0.9
    fcfs_score = float('inf')
    rmlf_score = float('inf')
    mlf = MLF(initial_queues=initial_queues,first_level_quantum=2)
    
    # Track jobs
    completed_jobs = []
    sorted_jobs = sorted(jobs, key=lambda x: x['arrival_time'])
    n_jobs = len(sorted_jobs)
    n_completed_jobs = 0
    round_completed_jobs = 0
    
    # Logging data
    checkpoint_data = []
    fcfs_count = 0
    rmlf_count = 0
    time_slot_log = []
    current_job_id = None
    
    # Job tracking
    job_progress = {job['job_index']: 0 for job in sorted_jobs}
    job_sizes = {job['job_index']: int(job['job_size']) for job in sorted_jobs}
    
    # Main scheduling loop
    for current_time in count():
        # Process new job arrivals
        while (jobs_pointer < len(sorted_jobs) and 
               sorted_jobs[jobs_pointer]['arrival_time'] <= current_time):
            new_job = Job(
                id=sorted_jobs[jobs_pointer]['job_index'],
                arrival_time=sorted_jobs[jobs_pointer]['arrival_time'],
                processing_time=sorted_jobs[jobs_pointer]['job_size']
            )
            mlf.insert(new_job)
            jobs_pointer += 1
        
        # Start of new round
        if current_time > 0 and current_time % checkpoint == 0:
            round_start_time = current_time
            
            # Algorithm selection
            if current_round == 1:
                selected_algo = "FCFS"
            elif current_round == 2:
                selected_algo = "RMLF"
            else:
                selected_algo = "FCFS" if fcfs_score < rmlf_score else "RMLF"
            
            # Update algorithm counts
            if selected_algo == "FCFS":
                fcfs_count += 1
            else:
                rmlf_count += 1
                
            #print(f"\nTime {current_time}: Round {current_round} - {selected_algo}")
            round_score = 0
            round_completed_jobs = 0
        
        # Select and process job
        selected_job = fcfs_selector(mlf) if selected_algo == "FCFS" else rmlf_selector(mlf)
        
        # Update current job status
        if (selected_job and 
            selected_job.arrival_time <= current_time and 
            job_progress[selected_job.id] < job_sizes[selected_job.id]):
            current_job_id = selected_job.id
        else:
            current_job_id = None
            selected_job = None
        
        # Process selected job
        if selected_job and current_job_id is not None:
            job_progress[current_job_id] += 1
            mlf.increase(selected_job)
            
            # Check for job completion
            if job_progress[current_job_id] >= job_sizes[current_job_id]:
                mlf.remove(selected_job)
                completed_jobs.append({
                    'arrival_time': selected_job.arrival_time,
                    'job_size': selected_job.processing_time,
                    'job_index': selected_job.id,
                    'completion_time': current_time + 1
                })
                #print(f"Time {current_time:.1f}: Job {selected_job.id} completed")
                n_completed_jobs += 1
                round_completed_jobs += 1
                
                if n_completed_jobs == n_jobs:
                    time_slot_log.append({
                        'time_slot': float(current_time + 1),
                        'executed_job_id': ''
                    })
                    break
        
        # Update round score
        round_score += sum(current_time - job.arrival_time for job in mlf.active_jobs)
        
        # End of round processing
        if current_time > 0 and (current_time + 1) % checkpoint == 0:
            normalized_score = round_score / max((round_completed_jobs+1), 1)
            
            # Update algorithm scores
            if selected_algo == "FCFS":
                fcfs_score = normalized_score if fcfs_score == float('inf') else fcfs_score * discount_factor + normalized_score
            else:  # RMLF
                rmlf_score = normalized_score if rmlf_score == float('inf') else rmlf_score * discount_factor + normalized_score
            
            # Calculate usage ratios
            total_rounds = fcfs_count + rmlf_count
            if total_rounds > 0:
                rmlf_ratio = float((rmlf_count / total_rounds) * 100)
                fcfs_ratio = float((fcfs_count / total_rounds) * 100)
            else:
                rmlf_ratio = 0.0
                fcfs_ratio = 0.0
            
            # Log checkpoint data
            checkpoint_data.append({
                'checkpoint_time': current_time + 1,
                'algorithm': selected_algo,
                'fcfs_score': fcfs_score if fcfs_score != float('inf') else 0,
                'rmlf_score': rmlf_score if rmlf_score != float('inf') else 0,
                'rmlf_ratio': float(f"{rmlf_ratio:.1f}"),
                'fcfs_ratio': float(f"{fcfs_ratio:.1f}")
            })

            current_round += 1
    
    flow_times = [job['completion_time'] - job['arrival_time'] for job in completed_jobs]
    avg_flow_time = sum(flow_times) / len(flow_times) if flow_times else 0
    l2_norm = math.sqrt(sum(t * t for t in flow_times)) if flow_times else 0
    
    return avg_flow_time, l2_norm