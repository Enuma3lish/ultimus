import csv
import random
import math
import os
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
    main_dir = "RFdynamic_C_analysis"
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
        
        # Create filename: RFdynamic_C_avg_30_checkpoint_100_mode_1.csv
        avg_num = file_type.replace('avg', '')
        output_file = f"RFdynamic_C_avg_{avg_num}_checkpoint_{checkpoint}_mode_{mode}.csv"
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
        # Create subfolder: freq1_mode_1
        sub_folder = f"freq{freq}_mode_{mode}"
        folder_path = os.path.join(main_dir, sub_folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Create filename: random_freq_1_mode1.csv
        output_file = f"{file_base_name}_mode{mode}.csv"
        file_path = os.path.join(folder_path, output_file)
        
        # Check if file exists to determine if we need to write header
        write_header = not os.path.exists(file_path)
        
        # Write or append to CSV
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if write_header:
                writer.writerow(['freq', 'FCFS_percentage', 'RMLF_percentage'])
            writer.writerow([freq, f"{fcfs_percentage:.1f}", f"{rmlf_percentage:.1f}"])
    
    # Handle softrandom type files
    elif file_type == 'softrandom':
        # Create nested folder structure: softrandom/freq1_mode_1
        softrandom_folder = os.path.join(main_dir, 'softrandom')
        if not os.path.exists(softrandom_folder):
            os.makedirs(softrandom_folder)
        
        sub_folder = f"freq{freq}_mode_{mode}"
        folder_path = os.path.join(softrandom_folder, sub_folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Create filename: softrandom_freq_1_mode1.csv
        output_file = f"{file_base_name}_mode{mode}.csv"
        file_path = os.path.join(folder_path, output_file)
        
        # Check if file exists to determine if we need to write header
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
    main_dir = "RFdynamic_C_analysis"
    
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

def RFdynamic_C(jobs: List[Dict[str, Any]], checkpoint = 100, mode: int = 1, input_filename=None) -> Tuple[float, float]:
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
    
    jobs_pointer = 0
    selected_algo = "FCFS"
    round_score = 0
    current_round = 1
    round_start_time = 0
    discount_factor = 0.9
    fcfs_score = float('inf')
    rmlf_score = float('inf')
    mlf = MLF(initial_queues=initial_queues, first_level_quantum=2)
    
    # Track jobs
    completed_jobs = []
    sorted_jobs = sorted(jobs, key=lambda x: x['arrival_time'])
    n_jobs = len(sorted_jobs)
    n_completed_jobs = 0
    round_completed_jobs = 0
    
    # Algorithm tracking for modes
    algorithm_history = []
    fcfs_scores_history = []
    rmlf_scores_history = []
    
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
            
            # Decide algorithm based on mode
            if current_round == 1:
                selected_algo = "FCFS"
            elif current_round == 2:
                selected_algo = "RMLF"
            else:
                # Apply mode-based selection for round 3 onwards
                if mode == 1:
                    # Mode 1: Check from round 2 to current round-1
                    if len(fcfs_scores_history) >= 2 and len(rmlf_scores_history) >= 2:
                        # Calculate average from round 2 onwards (index 1 onwards)
                        fcfs_avg = sum(fcfs_scores_history[1:]) / len(fcfs_scores_history[1:])
                        rmlf_avg = sum(rmlf_scores_history[1:]) / len(rmlf_scores_history[1:])
                        selected_algo = "FCFS" if fcfs_avg < rmlf_avg else "RMLF"
                    else:
                        # Default comparison
                        selected_algo = "FCFS" if fcfs_score < rmlf_score else "RMLF"
                
                elif mode == 2:
                    # Mode 2: Check the last ceil(sqrt(current_round)) rounds if round > 2
                    if current_round > 2:
                        check_rounds = math.ceil(math.sqrt(current_round))
                        
                        # Get recent scores
                        if len(fcfs_scores_history) >= check_rounds and len(rmlf_scores_history) >= check_rounds:
                            fcfs_recent = fcfs_scores_history[-check_rounds:]
                            rmlf_recent = rmlf_scores_history[-check_rounds:]
                            fcfs_avg = sum(fcfs_recent) / len(fcfs_recent)
                            rmlf_avg = sum(rmlf_recent) / len(rmlf_recent)
                            selected_algo = "FCFS" if fcfs_avg < rmlf_avg else "RMLF"
                        else:
                            # Use all available scores
                            if fcfs_scores_history and rmlf_scores_history:
                                fcfs_avg = sum(fcfs_scores_history) / len(fcfs_scores_history)
                                rmlf_avg = sum(rmlf_scores_history) / len(rmlf_scores_history)
                                selected_algo = "FCFS" if fcfs_avg < rmlf_avg else "RMLF"
                            else:
                                selected_algo = "FCFS" if fcfs_score < rmlf_score else "RMLF"
                    else:
                        # For round 2, use default comparison
                        selected_algo = "FCFS" if fcfs_score < rmlf_score else "RMLF"
                
                elif mode == 3:
                    # Mode 3: Check the last ceil(current_round/2) rounds if current_round >= 4
                    if current_round >= 4:
                        check_rounds = math.ceil(current_round / 2)
                        
                        if len(fcfs_scores_history) >= check_rounds and len(rmlf_scores_history) >= check_rounds:
                            fcfs_recent = fcfs_scores_history[-check_rounds:]
                            rmlf_recent = rmlf_scores_history[-check_rounds:]
                            fcfs_avg = sum(fcfs_recent) / len(fcfs_recent)
                            rmlf_avg = sum(rmlf_recent) / len(rmlf_recent)
                            selected_algo = "FCFS" if fcfs_avg < rmlf_avg else "RMLF"
                        else:
                            # Use all available scores
                            if fcfs_scores_history and rmlf_scores_history:
                                fcfs_avg = sum(fcfs_scores_history) / len(fcfs_scores_history)
                                rmlf_avg = sum(rmlf_scores_history) / len(rmlf_scores_history)
                                selected_algo = "FCFS" if fcfs_avg < rmlf_avg else "RMLF"
                            else:
                                selected_algo = "FCFS" if fcfs_score < rmlf_score else "RMLF"
                    else:
                        # For rounds 2 and 3, use default comparison
                        selected_algo = "FCFS" if fcfs_score < rmlf_score else "RMLF"
                else:
                    # Default to original behavior
                    selected_algo = "FCFS" if fcfs_score < rmlf_score else "RMLF"
            
            # Record algorithm choice
            algorithm_history.append(selected_algo)
            
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
                n_completed_jobs += 1
                round_completed_jobs += 1
                
                if n_completed_jobs == n_jobs:
                    break
        
        # Update round score
        round_score += sum(current_time - job.arrival_time for job in mlf.active_jobs)
        
        # End of round processing
        if current_time > 0 and (current_time + 1) % checkpoint == 0:
            normalized_score = round_score / max((round_completed_jobs+1), 1)
            
            # Update algorithm scores
            if selected_algo == "FCFS":
                if fcfs_score == float('inf'):
                    fcfs_score = normalized_score
                else:
                    fcfs_score = fcfs_score * discount_factor + normalized_score
                fcfs_scores_history.append(fcfs_score)
            else:  # RMLF
                if rmlf_score == float('inf'):
                    rmlf_score = normalized_score
                else:
                    rmlf_score = rmlf_score * discount_factor + normalized_score
                rmlf_scores_history.append(rmlf_score)
            
            # Also append a placeholder for the algorithm that wasn't used
            if selected_algo == "FCFS" and len(rmlf_scores_history) == 0:
                rmlf_scores_history.append(float('inf'))
            elif selected_algo == "RMLF" and len(fcfs_scores_history) == 0:
                fcfs_scores_history.append(float('inf'))

            current_round += 1
    
    flow_times = [job['completion_time'] - job['arrival_time'] for job in completed_jobs]
    avg_flow_time = sum(flow_times) / len(flow_times) if flow_times else 0
    l2_norm = math.sqrt(sum(t * t for t in flow_times)) if flow_times else 0
    
    # Save analysis results if input filename is provided
    if input_filename:
        save_analysis_results(input_filename, checkpoint, mode, algorithm_history, current_round - 1)
    
    return avg_flow_time, l2_norm