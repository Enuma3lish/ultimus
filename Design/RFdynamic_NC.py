import csv
import random
import math
import os
import copy
import re
import pandas as pd
from typing import Optional, List, Dict, Any, Tuple
from MLF_2 import Job, MLF
from itertools import count

def extract_file_info(input_file_name):
    """Extract information from the input file path"""
    if not input_file_name:
        return None, None, None, None, None
    
    # Get base filename without path
    base_name = os.path.basename(input_file_name)
    file_name_without_ext = os.path.splitext(base_name)[0]
    
    # Extract directory structure
    dir_path = os.path.dirname(input_file_name)
    
    # Check for avg pattern: (arrival_rate, L).csv
    avg_pattern = r'\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\)'
    avg_match = re.search(avg_pattern, base_name)
    
    if avg_match:
        arrival_rate = float(avg_match.group(1))
        L = float(avg_match.group(2))
        
        # Check if it's avg_30 or similar
        if 'avg_30' in dir_path or 'avg30' in dir_path.lower():
            return 'avg30', None, arrival_rate, L, None
        elif 'avg' in dir_path.lower():
            # Extract the avg number
            avg_num_match = re.search(r'avg_?(\d+)', dir_path.lower())
            if avg_num_match:
                avg_type = f"avg{avg_num_match.group(1)}"
                return avg_type, None, arrival_rate, L, None
    
    # Check for freq pattern
    freq_pattern = r'freq_?(\d+)'
    freq_match = re.search(freq_pattern, input_file_name.lower())
    
    if freq_match:
        freq = int(freq_match.group(1))
        
        # Check if it's softrandom
        if 'softrandom' in input_file_name.lower():
            return 'softrandom', file_name_without_ext, None, None, freq
        # Check if it's random
        elif 'random' in input_file_name.lower():
            return 'random', file_name_without_ext, None, None, freq
    
    return None, file_name_without_ext, None, None, None

def save_analysis_results(input_file_name, checkpoint, mode, algorithm_history, total_rounds):
    """Save analysis results to CSV file"""
    if not input_file_name:
        return
    
    file_type, file_base_name, arrival_rate, L, freq = extract_file_info(input_file_name)
    
    if not file_type:
        return
    
    # Create main analysis directory
    main_dir = "RFdynamic_NC_analysis"
    if not os.path.exists(main_dir):
        os.makedirs(main_dir)
    
    # Calculate algorithm percentages
    rmlf_count = sum(1 for algo in algorithm_history if algo == 'RMLF')
    fcfs_count = sum(1 for algo in algorithm_history if algo == 'FCFS')
    total = len(algorithm_history)
    
    if total > 0:
        rmlf_percentage = (rmlf_count / total) * 100
        fcfs_percentage = (fcfs_count / total) * 100
    else:
        rmlf_percentage = 0
        fcfs_percentage = 0
    
    # Handle avg type files
    if file_type.startswith('avg'):
        # Create subfolder: avg30_mode_1
        sub_folder = f"{file_type}_mode_{mode}"
        folder_path = os.path.join(main_dir, sub_folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Create filename
        avg_num = file_type.replace('avg', '')
        output_file = f"RFdynamic_NC_avg_{avg_num}_checkpoint_{checkpoint}_mode_{mode}.csv"
        file_path = os.path.join(folder_path, output_file)
        
        # Check if file exists to determine if we need to write header
        write_header = not os.path.exists(file_path)
        
        # Write or append to CSV
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if write_header:
                writer.writerow(['arrival_rate', 'L', 'FCFS_percentage', 'RMLF_percentage'])
            writer.writerow([arrival_rate, L, f"{fcfs_percentage:.1f}", f"{rmlf_percentage:.1f}"])
    
    # Handle random type files
    elif file_type == 'random':
        # Create subfolder
        sub_folder = f"freq{freq}_mode_{mode}"
        folder_path = os.path.join(main_dir, sub_folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Create filename
        output_file = f"{file_base_name}_mode{mode}.csv"
        file_path = os.path.join(folder_path, output_file)
        
        # Check if file exists
        write_header = not os.path.exists(file_path)
        
        # Write or append to CSV
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if write_header:
                writer.writerow(['freq', 'FCFS_percentage', 'RMLF_percentage'])
            writer.writerow([freq, f"{fcfs_percentage:.1f}", f"{rmlf_percentage:.1f}"])
    
    # Handle softrandom type files
    elif file_type == 'softrandom':
        # Create nested folder structure
        softrandom_folder = os.path.join(main_dir, 'softrandom')
        if not os.path.exists(softrandom_folder):
            os.makedirs(softrandom_folder)
        
        sub_folder = f"freq{freq}_mode_{mode}"
        folder_path = os.path.join(softrandom_folder, sub_folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Create filename
        output_file = f"{file_base_name}_mode{mode}.csv"
        file_path = os.path.join(folder_path, output_file)
        
        # Check if file exists
        write_header = not os.path.exists(file_path)
        
        # Write or append to CSV
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if write_header:
                writer.writerow(['freq', 'FCFS_percentage', 'RMLF_percentage'])
            writer.writerow([freq, f"{fcfs_percentage:.1f}", f"{rmlf_percentage:.1f}"])
    
    # Save detailed round-by-round algorithm usage
    save_round_details(input_file_name, checkpoint, mode, algorithm_history)

def save_round_details(input_file_name, checkpoint, mode, algorithm_history):
    """Save detailed round-by-round algorithm selection"""
    if not input_file_name or not algorithm_history:
        return
    
    file_type, file_base_name, arrival_rate, L, freq = extract_file_info(input_file_name)
    
    if not file_type:
        return
    
    # Create main analysis directory
    main_dir = "RFdynamic_NC_analysis"
    
    # Determine folder structure based on file type
    if file_type.startswith('avg'):
        sub_folder = f"{file_type}_mode_{mode}"
        folder_path = os.path.join(main_dir, sub_folder, "round_details")
    elif file_type == 'random':
        sub_folder = f"freq{freq}_mode_{mode}"
        folder_path = os.path.join(main_dir, sub_folder, "round_details")
    elif file_type == 'softrandom':
        sub_folder = f"freq{freq}_mode_{mode}"
        folder_path = os.path.join(main_dir, 'softrandom', sub_folder, "round_details")
    else:
        return
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    # Create filename for round details
    if file_type.startswith('avg'):
        detail_file = f"rounds_arr{arrival_rate}_L{L}_checkpoint{checkpoint}.csv"
    else:
        detail_file = f"rounds_{file_base_name}_checkpoint{checkpoint}.csv"
    
    file_path = os.path.join(folder_path, detail_file)
    
    # Write round details
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Round', 'Algorithm_Used'])
        for i, algo in enumerate(algorithm_history, 1):
            writer.writerow([i, algo])

def simulate_fcfs_on_jobs(job_pool):
    """Simulate FCFS on a pool of jobs to get L2 norm"""
    if not job_pool:
        return 0.0
    
    jobs = sorted(job_pool, key=lambda x: x['arrival_time'])
    current_time = 0
    completed_jobs = []
    waiting_queue = []
    jobs_pointer = 0
    current_job = None
    
    while len(completed_jobs) < len(jobs):
        # Add jobs that arrive at current time
        while jobs_pointer < len(jobs) and jobs[jobs_pointer]['arrival_time'] <= current_time:
            waiting_queue.append(jobs[jobs_pointer].copy())
            jobs_pointer += 1
        
        # Select next job if no current job
        if current_job is None and waiting_queue:
            current_job = waiting_queue.pop(0)
        
        # Process current job
        if current_job:
            current_job['remaining_time'] -= 1
            if current_job['remaining_time'] == 0:
                completion_time = current_time + 1
                flow_time = completion_time - current_job['arrival_time']
                completed_jobs.append(flow_time)
                current_job = None
        
        current_time += 1
    
    # Calculate L2 norm
    l2_norm = math.sqrt(sum(t * t for t in completed_jobs)) if completed_jobs else 0
    return l2_norm

def simulate_rmlf_on_jobs(job_pool):
    """Simulate RMLF on a pool of jobs to get L2 norm"""
    if not job_pool:
        return 0.0
    
    mlf = MLF(initial_queues=1, first_level_quantum=2)
    jobs = sorted(job_pool, key=lambda x: x['arrival_time'])
    current_time = 0
    completed_flow_times = []
    jobs_pointer = 0
    job_progress = {}
    
    # Create MLF jobs
    mlf_jobs = {}
    for job in jobs:
        mlf_job = Job(
            id=job['job_index'],
            arrival_time=job['arrival_time'],
            processing_time=job['job_size']
        )
        mlf_jobs[job['job_index']] = mlf_job
        job_progress[job['job_index']] = 0
    
    while len(completed_flow_times) < len(jobs):
        # Add jobs that arrive at current time
        while jobs_pointer < len(jobs) and jobs[jobs_pointer]['arrival_time'] <= current_time:
            mlf.insert(mlf_jobs[jobs[jobs_pointer]['job_index']])
            jobs_pointer += 1
        
        # Select next job using RMLF
        selected_job = None
        for queue in mlf.queues:
            if not queue.is_empty:
                jobs_in_queue = queue.get_jobs_list()
                for job in jobs_in_queue:
                    if job_progress[job.id] < job.processing_time:
                        selected_job = job
                        break
                if selected_job:
                    break
        
        # Process selected job
        if selected_job:
            job_progress[selected_job.id] += 1
            mlf.increase(selected_job)
            
            if job_progress[selected_job.id] >= selected_job.processing_time:
                mlf.remove(selected_job)
                completion_time = current_time + 1
                flow_time = completion_time - selected_job.arrival_time
                completed_flow_times.append(flow_time)
        
        current_time += 1
    
    # Calculate L2 norm
    l2_norm = math.sqrt(sum(t * t for t in completed_flow_times)) if completed_flow_times else 0
    return l2_norm

def RFdynamic_NC(jobs: List[Dict[str, Any]], checkpoint = 100, mode: int = 1, input_filename=None) -> Tuple[float, float]:
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
    mlf = MLF(initial_queues=initial_queues, first_level_quantum=2)
    
    jobs_pointer = 0
    selected_algo = "FCFS"  # First round fixed to FCFS
    current_round = 1
    
    # Track jobs
    completed_jobs = []
    sorted_jobs = sorted(jobs, key=lambda x: x['arrival_time'])
    n_jobs = len(sorted_jobs)
    n_completed_jobs = 0
    
    # Job tracking
    job_progress = {job['job_index']: 0 for job in sorted_jobs}
    job_sizes = {job['job_index']: int(job['job_size']) for job in sorted_jobs}
    
    # Job pool for simulation
    job_size_pool = []
    job_finished_counter = 0
    n_arrival_jobs = 0
    
    # History tracking for mode selection
    fcfs_l2_history = []
    rmlf_l2_history = []
    algorithm_history = []
    
    # Algorithm selection flag
    is_fcfs_better = True  # Start with FCFS for first round
    
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
            n_arrival_jobs += 1
            jobs_pointer += 1
        
        # Checkpoint logic - check when to switch rounds
        checkpoint_triggered = False
        if current_round == 1:
            # First round: checkpoint based on jobs finished
            if job_finished_counter >= checkpoint:
                checkpoint_triggered = True
        else:
            # Subsequent rounds: checkpoint based on jobs arrived
            if n_arrival_jobs >= checkpoint * current_round:
                checkpoint_triggered = True
        
        if checkpoint_triggered:
            # Prepare job pool for simulation
            simulation_pool = job_size_pool[-checkpoint:].copy() if len(job_size_pool) >= checkpoint else job_size_pool.copy()
            
            # If not enough jobs, randomly sample from pool with preference for recent arrivals
            if len(simulation_pool) < checkpoint and len(job_size_pool) > 0:
                needed = checkpoint - len(simulation_pool)
                # Create weighted sampling - more recent arrivals have higher weight
                weights = [i + 1 for i in range(len(job_size_pool))]  # Later indices have higher weights
                sampled_indices = random.choices(range(len(job_size_pool)), weights=weights, k=min(needed, len(job_size_pool)))
                
                for idx in sampled_indices:
                    if len(simulation_pool) < checkpoint:
                        simulation_pool.append(job_size_pool[idx].copy())
            
            # Simulate both algorithms on the job pool
            if simulation_pool:
                fcfs_l2 = simulate_fcfs_on_jobs(simulation_pool)
                rmlf_l2 = simulate_rmlf_on_jobs(simulation_pool)
                
                fcfs_l2_history.append(fcfs_l2)
                rmlf_l2_history.append(rmlf_l2)
                
                # Decide which algorithm to use for next round
                if current_round == 1:
                    # First round fixed to FCFS, record it
                    algorithm_history.append('FCFS')
                    # Decide for round 2 based on simulation
                    is_fcfs_better = fcfs_l2 <= rmlf_l2
                else:
                    # Apply the selected mode to decide for current round
                    if mode == 1:
                        # Mode 1: Check from round 2 to current round-1
                        if len(fcfs_l2_history) >= 2:
                            fcfs_avg_l2 = sum(fcfs_l2_history[1:]) / len(fcfs_l2_history[1:])
                            rmlf_avg_l2 = sum(rmlf_l2_history[1:]) / len(rmlf_l2_history[1:])
                            is_fcfs_better = fcfs_avg_l2 <= rmlf_avg_l2
                        else:
                            is_fcfs_better = fcfs_l2_history[0] <= rmlf_l2_history[0]
                    
                    elif mode == 2:
                        # Mode 2: Check the last ceil(sqrt(current_round)) rounds if round > 2
                        if current_round > 2:
                            check_rounds = math.ceil(math.sqrt(current_round))
                            available_rounds = len(fcfs_l2_history)
                            
                            if available_rounds >= check_rounds:
                                fcfs_recent = fcfs_l2_history[-check_rounds:]
                                rmlf_recent = rmlf_l2_history[-check_rounds:]
                                fcfs_avg_l2 = sum(fcfs_recent) / len(fcfs_recent)
                                rmlf_avg_l2 = sum(rmlf_recent) / len(rmlf_recent)
                                is_fcfs_better = fcfs_avg_l2 <= rmlf_avg_l2
                            else:
                                fcfs_avg_l2 = sum(fcfs_l2_history) / len(fcfs_l2_history)
                                rmlf_avg_l2 = sum(rmlf_l2_history) / len(rmlf_l2_history)
                                is_fcfs_better = fcfs_avg_l2 <= rmlf_avg_l2
                        else:
                            # For round 2, use all available history
                            if fcfs_l2_history:
                                fcfs_avg_l2 = sum(fcfs_l2_history) / len(fcfs_l2_history)
                                rmlf_avg_l2 = sum(rmlf_l2_history) / len(rmlf_l2_history)
                                is_fcfs_better = fcfs_avg_l2 <= rmlf_avg_l2
                            else:
                                is_fcfs_better = True
                    
                    elif mode == 3:
                        # Mode 3: Check the last ceil(current_round/2) rounds if current_round >= 4
                        if current_round >= 4:
                            check_rounds = math.ceil(current_round / 2)
                            available_rounds = len(fcfs_l2_history)
                            
                            if available_rounds >= check_rounds:
                                fcfs_recent = fcfs_l2_history[-check_rounds:]
                                rmlf_recent = rmlf_l2_history[-check_rounds:]
                                fcfs_avg_l2 = sum(fcfs_recent) / len(fcfs_recent)
                                rmlf_avg_l2 = sum(rmlf_recent) / len(rmlf_recent)
                                is_fcfs_better = fcfs_avg_l2 <= rmlf_avg_l2
                            else:
                                fcfs_avg_l2 = sum(fcfs_l2_history) / len(fcfs_l2_history)
                                rmlf_avg_l2 = sum(rmlf_l2_history) / len(rmlf_l2_history)
                                is_fcfs_better = fcfs_avg_l2 <= rmlf_avg_l2
                        else:
                            # For rounds 2 and 3, use all previous rounds
                            if len(fcfs_l2_history) > 0:
                                fcfs_avg_l2 = sum(fcfs_l2_history) / len(fcfs_l2_history)
                                rmlf_avg_l2 = sum(rmlf_l2_history) / len(rmlf_l2_history)
                                is_fcfs_better = fcfs_avg_l2 <= rmlf_avg_l2
                            else:
                                is_fcfs_better = True
                    
                    # Record which algorithm was chosen
                    algorithm_history.append('FCFS' if is_fcfs_better else 'RMLF')
                
                # Update selected algorithm for next round
                selected_algo = 'FCFS' if is_fcfs_better else 'RMLF'
                current_round += 1
                
                # Reset counter for next round
                if current_round == 2:
                    n_arrival_jobs = 0  # Reset arrival counter after first round
        
        # Select and process job based on current algorithm
        selected_job = fcfs_selector(mlf) if selected_algo == "FCFS" else rmlf_selector(mlf)
        
        # Process selected job
        if selected_job and job_progress[selected_job.id] < job_sizes[selected_job.id]:
            job_progress[selected_job.id] += 1
            mlf.increase(selected_job)
            
            # Check for job completion
            if job_progress[selected_job.id] >= job_sizes[selected_job.id]:
                mlf.remove(selected_job)
                completed_jobs.append({
                    'arrival_time': selected_job.arrival_time,
                    'job_size': selected_job.processing_time,
                    'job_index': selected_job.id,
                    'completion_time': current_time + 1
                })
                n_completed_jobs += 1
                job_finished_counter += 1
                
                # Add to job pool
                job_size_pool.append({
                    'job_index': selected_job.id,
                    'arrival_time': selected_job.arrival_time,
                    'job_size': selected_job.processing_time,
                    'remaining_time': selected_job.processing_time
                })
                
                if n_completed_jobs == n_jobs:
                    break
    
    # Calculate final metrics
    flow_times = [job['completion_time'] - job['arrival_time'] for job in completed_jobs]
    avg_flow_time = sum(flow_times) / len(flow_times) if flow_times else 0
    l2_norm = math.sqrt(sum(t * t for t in flow_times)) if flow_times else 0
    
    # Save analysis results if input filename is provided
    if input_filename:
        save_analysis_results(input_filename, checkpoint, mode, algorithm_history, current_round - 1)
    
    return avg_flow_time, l2_norm