import csv
import random
import math
import os
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from MLF_8 import Job, MLF
from itertools import count

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
        
# def log_algorithm_ratios(checkpoint: int, arrival_rate: float, bp_param: dict, rmlf_ratio: float, fcfs_ratio: float, run_number: Optional[int] = None) -> None:
#     """Save algorithm usage ratios to a CSV file with sequential run numbering"""
#     # Create log directory if it doesn't exist
#     os.makedirs('log', exist_ok=True)
    
#     # Generate filename with run number
#     base_filename = f"log/{run_number}ratio@{checkpoint}.csv" if run_number is not None else f"log/ratio@{checkpoint}.csv"
    
#     file_exists = os.path.isfile(base_filename)
#     fieldnames = ['checkpoint', 'arrival_rate', 'bp_parameter', 'rmlf_ratio', 'fcfs_ratio']
    
#     try:
#         mode = 'a' if file_exists else 'w'
#         with open(base_filename, mode, newline='') as file:
#             writer = csv.DictWriter(file, fieldnames=fieldnames)
            
#             if not file_exists:
#                 writer.writeheader()
                
#             writer.writerow({
#                 'checkpoint': checkpoint,
#                 'arrival_rate': arrival_rate,
#                 'bp_parameter': bp_param,
#                 'rmlf_ratio': rmlf_ratio,
#                 'fcfs_ratio': fcfs_ratio
#             })
#     except IOError as e:
#         print(f"Error writing to ratio results file: {e}")

def calculate_final_ratios(checkpoint: int) -> None:
    """Calculate and save average ratios from multiple sequentially numbered run files"""
    # Find all numbered ratio files for this checkpoint
    run_files = []
    for i in range(1, 11):  # Looks for files 1 through 10
        filename = f"log/{i}ratio@{checkpoint}.csv"
        if os.path.exists(filename):
            run_files.append(filename)
    
    if not run_files:
        print(f"No ratio result files found for checkpoint {checkpoint}")
        return
        
    print(f"Found {len(run_files)} ratio result files for checkpoint {checkpoint}")
    
    # Read and combine all files
    dfs = []
    for file in run_files:
        try:
            df = pd.read_csv(file)
            dfs.append(df)
        except Exception as e:
            print(f"Error reading file {file}: {e}")
            continue
    
    if not dfs:
        print("No valid data files found")
        return
    
    # Calculate averages
    combined_df = pd.concat(dfs, ignore_index=True)
    grouped = combined_df.groupby(['checkpoint', 'arrival_rate', 'bp_parameter']).agg({
        'rmlf_ratio': 'mean',
        'fcfs_ratio': 'mean'
    }).reset_index()
    
    # Round ratios
    grouped['rmlf_ratio'] = grouped['rmlf_ratio'].round(1)
    grouped['fcfs_ratio'] = grouped['fcfs_ratio'].round(1)
    
    # Save final results
    output_file = f"log/final_ratio@{checkpoint}.csv"
    grouped.to_csv(output_file, index=False)
    print(f"Final averaged results saved to {output_file}")
def Rdynamic(jobs: List[Dict[str, Any]], checkpoint: int, prob_greedy: float = 1.0) -> Tuple[float, float]:
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
    mlf = MLF(initial_queues=initial_queues,first_level_quantum=8)
    
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
                p = random.random()
                if p <= prob_greedy:  # greedy mode
                    selected_algo = "FCFS" if fcfs_score < rmlf_score else "RMLF"
                else:  # discovery mode
                    selected_algo = "FCFS" if random.random() <= 0.5 else "RMLF"
            
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
            
            # Print round statistics
            # print(f"\nEnd of Round {current_round}")
            # print(f"Round completed jobs: {round_completed_jobs}")
            # print(f"Raw round score: {round_score:.2f}")
            # print(f"Normalized round score: {normalized_score:.2f}")
            # print(f"FCFS Score: {fcfs_score:.2f}")
            # print(f"RMLF Score: {rmlf_score:.2f}")
            # print(f"Algorithm Usage - RMLF: {rmlf_ratio:.1f}%, FCFS: {fcfs_ratio:.1f}%")
            # print("\nQueue Status:")
            # print(mlf.get_queue_status())
            current_round += 1
    
    # Calculate final ratios
    # total_rounds = fcfs_count + rmlf_count
    # if total_rounds > 0:
    #     final_rmlf_ratio = float((rmlf_count / total_rounds) * 100)
    #     final_fcfs_ratio = float((fcfs_count / total_rounds) * 100)
    # else:
    #     final_rmlf_ratio = 0.0
    #     final_fcfs_ratio = 0.0
    
    # Log final results with run number
    # log_algorithm_ratios(
    #     checkpoint=checkpoint,
    #     arrival_rate=arrival_rate,
    #     bp_param=bp_param,
    #     rmlf_ratio=final_rmlf_ratio,
    #     fcfs_ratio=final_fcfs_ratio,
    #     run_number=run_number
    # )
    # Calculate and return final metrics
    flow_times = [job['completion_time'] - job['arrival_time'] for job in completed_jobs]
    avg_flow_time = sum(flow_times) / len(flow_times) if flow_times else 0
    l2_norm = math.sqrt(sum(t * t for t in flow_times)) if flow_times else 0
    
    return avg_flow_time, l2_norm