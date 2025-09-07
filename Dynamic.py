import math
import csv
import copy
import os
import re
from SRPT_Selector import select_next_job as srpt_select_next_job
from FCFS_Selector import select_next_job as fcfs_select_next_job
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def Srpt(jobs):
    current_time = 0
    completed_jobs = []
    job_queue = []
    total_jobs = len(jobs)
    jobs_pointer = 0

    # Assign job indices
    for idx, job in enumerate(jobs):
        job['job_index'] = idx

    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x['arrival_time'])

    while len(completed_jobs) < total_jobs:
        # Add jobs that arrive at the current time
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] <= current_time:
            job = jobs[jobs_pointer]
            job_copy = {
                'arrival_time': job['arrival_time'],
                'job_size': job['job_size'],
                'remaining_time': job['job_size'],
                'job_index': job['job_index'],
                'completion_time': None,
                'start_time': None
            }
            job_queue.append(job_copy)
            jobs_pointer += 1

        # Select the next job
        selected_job = srpt_select_next_job(job_queue) if job_queue else None

        # Process selected job
        if selected_job:
            job_queue.remove(selected_job)

            # Record start_time if not already set
            if selected_job['start_time'] is None:
                selected_job['start_time'] = current_time

            selected_job['remaining_time'] -= 1

            # Check if job is completed
            if selected_job['remaining_time'] == 0:
                selected_job['completion_time'] = current_time + 1  # Adjusted here
                completed_jobs.append(selected_job)
            else:
                # Re-add the job to the queue
                job_queue.append(selected_job)

        # Increment time
        current_time += 1

    # Calculate metrics
    total_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    if total_jobs > 0:
        avg_flow_time = total_flow_time / total_jobs
        l2_norm_flow_time = (sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs)) ** 0.5
    else:
        avg_flow_time = 0
        l2_norm_flow_time = 0

    return avg_flow_time, l2_norm_flow_time

def Fcfs(jobs):
    current_time = 0
    completed_jobs = []
    waiting_queue = []
    total_jobs = len(jobs)
    jobs_pointer = 0
    current_job = None

    # Assign job indices
    for idx, job in enumerate(jobs):
        job['job_index'] = idx

    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x['arrival_time'])

    while len(completed_jobs) < total_jobs:
        # Add jobs that arrive at the current time
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] <= current_time:
            job = jobs[jobs_pointer]
            # Copy job to avoid modifying the original
            job_copy = {
                'arrival_time': job['arrival_time'],
                'job_size': job['job_size'],
                'remaining_time': job['job_size'],
                'job_index': job['job_index'],
                'completion_time': None,
                'start_time': None
            }
            waiting_queue.append(job_copy)
            jobs_pointer += 1

        # Select the next job using the FCFS selector
        if current_job is None and waiting_queue:
            current_job = fcfs_select_next_job(waiting_queue)
            if current_job:
                waiting_queue.remove(current_job)
                # Record start_time if not already set
                if current_job['start_time'] is None:
                    current_job['start_time'] = current_time

        # Process current job
        if current_job:
            current_job['remaining_time'] -= 1

            # Check if job is completed
            if current_job['remaining_time'] == 0:
                current_job['completion_time'] = current_time + 1
                completed_jobs.append(current_job)
                current_job = None

        # Increment time
        current_time += 1

    # Calculate metrics
    total_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    if total_jobs > 0:
        avg_flow_time = total_flow_time / total_jobs
        l2_norm_flow_time = (sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs))**0.5
    else:
        avg_flow_time = 0
        l2_norm_flow_time = 0

    return avg_flow_time, l2_norm_flow_time

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

def save_analysis_results(input_file_name, nJobsPerRound, mode, algorithm_history, total_rounds):
    """Save analysis results to CSV file"""
    if not input_file_name:
        return
    
    file_type, file_base_name, arrival_rate, L, freq = extract_file_info(input_file_name)
    
    if not file_type:
        return
    
    # Create main analysis directory
    main_dir = "Dynamic_analysis"
    if not os.path.exists(main_dir):
        os.makedirs(main_dir)
    
    # Calculate algorithm percentages
    srpt_count = sum(1 for algo in algorithm_history if algo == 'SRPT')
    fcfs_count = sum(1 for algo in algorithm_history if algo == 'FCFS')
    total = len(algorithm_history)
    
    if total > 0:
        srpt_percentage = (srpt_count / total) * 100
        fcfs_percentage = (fcfs_count / total) * 100
    else:
        srpt_percentage = 0
        fcfs_percentage = 0
    
    # Handle avg type files
    if file_type.startswith('avg'):
        # Create subfolder: avg30_mode_1
        sub_folder = f"{file_type}_mode_{mode}"
        folder_path = os.path.join(main_dir, sub_folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        # Create filename: Dynamic_avg_30_nJobsPerRound_100_mode_1.csv
        avg_num = file_type.replace('avg', '')
        output_file = f"Dynamic_avg_{avg_num}_nJobsPerRound_{nJobsPerRound}_mode_{mode}.csv"
        file_path = os.path.join(folder_path, output_file)
        
        # Check if file exists to determine if we need to write header
        write_header = not os.path.exists(file_path)
        
        # Write or append to CSV
        with open(file_path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if write_header:
                writer.writerow(['arrival_rate', 'L', 'FCFS_percentage', 'SRPT_percentage'])
            writer.writerow([arrival_rate, L, f"{fcfs_percentage:.1f}", f"{srpt_percentage:.1f}"])
    
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
                writer.writerow(['freq', 'FCFS_percentage', 'SRPT_percentage'])
            writer.writerow([freq, f"{fcfs_percentage:.1f}", f"{srpt_percentage:.1f}"])
    
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
                writer.writerow(['freq', 'FCFS_percentage', 'SRPT_percentage'])
            writer.writerow([freq, f"{fcfs_percentage:.1f}", f"{srpt_percentage:.1f}"])
    
    # Save detailed round-by-round algorithm usage
    save_round_details(input_file_name, nJobsPerRound, mode, algorithm_history)

def save_round_details(input_file_name, nJobsPerRound, mode, algorithm_history):
    """Save detailed round-by-round algorithm selection"""
    if not input_file_name or not algorithm_history:
        return
    
    file_type, file_base_name, arrival_rate, L, freq = extract_file_info(input_file_name)
    
    if not file_type:
        return
    
    # Create main analysis directory
    main_dir = "Dynamic_analysis"
    
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
        detail_file = f"rounds_arr{arrival_rate}_L{L}_njobs{nJobsPerRound}.csv"
    else:
        detail_file = f"rounds_{file_base_name}_njobs{nJobsPerRound}.csv"
    
    file_path = os.path.join(folder_path, detail_file)
    
    # Write round details
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Round', 'Algorithm_Used'])
        for i, algo in enumerate(algorithm_history, 1):
            writer.writerow([i, algo])

def DYNAMIC(jobs, nJobsPerRound = 100, mode=1, input_file_name=None):
    total_jobs = len(jobs)

    current_time = 0
    active_jobs = []
    completed_jobs = []
    n_arrival_jobs = 0
    n_completed_jobs = 0
    is_srpt_better = True  # Start with SRPT by default for first round
    jobs_pointer = 0
    jobs_in_round = []
    current_job = None
    
    # Lists to log L2 norms for each round
    fcfs_l2_history = []
    srpt_l2_history = []
    current_round = 1
    
    # Track which algorithm was used in each round
    algorithm_history = []

    # Assign job indices and initialize jobs
    for idx, job in enumerate(jobs):
        job['job_index'] = idx
        job['remaining_time'] = job['job_size']
        job['completion_time'] = None

    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x['arrival_time'])

    while n_completed_jobs < total_jobs:
        # Check for new job arrivals
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] == current_time:
            job = jobs[jobs_pointer]
            job_copy = job.copy()
            active_jobs.append(job_copy)
            jobs_in_round.append(job_copy)
            n_arrival_jobs += 1
            jobs_pointer += 1

        # Checkpoint logic
        if n_arrival_jobs >= nJobsPerRound:
            if jobs_in_round:
                # Simulate SRPT and FCFS on the new jobs only
                srpt_jobs_copy = copy.deepcopy(jobs_in_round)
                fcfs_jobs_copy = copy.deepcopy(jobs_in_round)
                
                srpt_avg, srpt_l2 = Srpt(srpt_jobs_copy)
                fcfs_avg, fcfs_l2 = Fcfs(fcfs_jobs_copy)
                
                # Log the L2 norms
                srpt_l2_history.append(srpt_l2)
                fcfs_l2_history.append(fcfs_l2)
                
                # Decide which algorithm to use for the NEXT round
                if current_round == 1:
                    # First round is fixed on SRPT
                    is_srpt_better = True
                    algorithm_history.append('SRPT')
                else:
                    # Apply the selected mode to decide for the current round
                    if mode == 1:
                        # Mode 1: Check from round 2 to current round-1
                        if len(srpt_l2_history) >= 2:
                            # Calculate average from round 2 to current round-1
                            # (indices 1 to len(history)-1, which is current_round-1)
                            srpt_avg_l2 = sum(srpt_l2_history[1:]) / len(srpt_l2_history[1:])
                            fcfs_avg_l2 = sum(fcfs_l2_history[1:]) / len(fcfs_l2_history[1:])
                            is_srpt_better = srpt_avg_l2 <= fcfs_avg_l2
                        else:
                            # For round 2, use the comparison of round 1
                            is_srpt_better = srpt_l2_history[0] <= fcfs_l2_history[0]
                    
                    elif mode == 2:
                        # Mode 2: Check the last ceil(sqrt(current_round)) rounds
                        check_rounds = math.ceil(math.sqrt(current_round))
                        # We have current_round-1 completed rounds in history
                        available_rounds = len(srpt_l2_history)
                        
                        if available_rounds >= check_rounds:
                            # Get the last check_rounds rounds
                            srpt_recent = srpt_l2_history[-check_rounds:]
                            fcfs_recent = fcfs_l2_history[-check_rounds:]
                            srpt_avg_l2 = sum(srpt_recent) / len(srpt_recent)
                            fcfs_avg_l2 = sum(fcfs_recent) / len(fcfs_recent)
                            is_srpt_better = srpt_avg_l2 <= fcfs_avg_l2
                        else:
                            # Use all available previous rounds
                            srpt_avg_l2 = sum(srpt_l2_history) / len(srpt_l2_history)
                            fcfs_avg_l2 = sum(fcfs_l2_history) / len(fcfs_l2_history)
                            is_srpt_better = srpt_avg_l2 <= fcfs_avg_l2
                    
                    elif mode == 3:
                        # Mode 3: Check the last ceil(current_round/2) rounds if current_round >= 4
                        if current_round >= 4:
                            check_rounds = math.ceil(current_round / 2)
                            available_rounds = len(srpt_l2_history)
                            
                            if available_rounds >= check_rounds:
                                # Get the last check_rounds rounds
                                srpt_recent = srpt_l2_history[-check_rounds:]
                                fcfs_recent = fcfs_l2_history[-check_rounds:]
                                srpt_avg_l2 = sum(srpt_recent) / len(srpt_recent)
                                fcfs_avg_l2 = sum(fcfs_recent) / len(fcfs_recent)
                                is_srpt_better = srpt_avg_l2 <= fcfs_avg_l2
                            else:
                                # Use all available previous rounds
                                srpt_avg_l2 = sum(srpt_l2_history) / len(srpt_l2_history)
                                fcfs_avg_l2 = sum(fcfs_l2_history) / len(fcfs_l2_history)
                                is_srpt_better = srpt_avg_l2 <= fcfs_avg_l2
                        else:
                            # For rounds 2 and 3, use all previous rounds
                            if len(srpt_l2_history) > 0:
                                srpt_avg_l2 = sum(srpt_l2_history) / len(srpt_l2_history)
                                fcfs_avg_l2 = sum(fcfs_l2_history) / len(fcfs_l2_history)
                                is_srpt_better = srpt_avg_l2 <= fcfs_avg_l2
                            else:
                                is_srpt_better = True  # Default to SRPT
                    
                    # Record which algorithm was chosen
                    algorithm_history.append('SRPT' if is_srpt_better else 'FCFS')
                
                current_round += 1
                
            jobs_in_round = []
            n_arrival_jobs = 0  # Reset the arrival counter

        # Select next job based on the current scheduling policy
        if is_srpt_better:
            # SRPT mode: preemptive scheduling
            selected_job = srpt_select_next_job(active_jobs) 
        else:
            # FCFS mode: non-preemptive scheduling
            selected_job = fcfs_select_next_job(active_jobs)

        # Process current job
        if selected_job:
            active_jobs.remove(selected_job)
            selected_job['remaining_time'] -= 1
            if selected_job['remaining_time'] == 0:
                selected_job['completion_time'] = current_time + 1
                completed_jobs.append(selected_job)
                n_completed_jobs += 1
            else:
                active_jobs.append(selected_job)            

        # Increment time
        current_time += 1

    # Calculate metrics
    total_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    if total_jobs > 0:
        avg_flow_time = total_flow_time / total_jobs
        l2_norm_flow_time = math.sqrt(sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs))
    else:
        avg_flow_time = 0
        l2_norm_flow_time = 0

    # Save analysis results if input file name is provided
    if input_file_name:
        save_analysis_results(input_file_name, nJobsPerRound, mode, algorithm_history, current_round - 1)

    return avg_flow_time, l2_norm_flow_time