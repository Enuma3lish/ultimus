import math
import csv
import copy
import os
import re
import glob
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

def save_analysis_results(input_file_path, nJobsPerRound, mode, algorithm_history, total_rounds):
    """Save analysis results to CSV file with version handling"""
    if not input_file_path or not algorithm_history:
        return
    
    # Extract folder information
    dir_path = os.path.dirname(input_file_path)
    folder_name = os.path.basename(dir_path)
    filename = os.path.basename(input_file_path)
    
    # Check if it's an avg file (not random/softrandom)
    if not folder_name.startswith('avg_'):
        return
    
    # Extract version number from folder name (e.g., avg_30_1 -> 1)
    version = extract_version_from_path(folder_name)
    
    # Extract avg type (30, 60, or 90)
    avg_type_match = re.search(r'avg_(\d+)', folder_name)
    if not avg_type_match:
        return
    avg_type = avg_type_match.group(1)
    
    # Parse filename to get arrival_rate and other parameters
    arrival_rate, bp_L, bp_H = parse_avg30_filename(filename)
    if arrival_rate is None:
        return
    
    # Create main analysis directory structure
    main_dir = "Dynamic_analysis"
    avg_folder = f"avg_{avg_type}"
    mode_folder = f"mode_{mode}"
    folder_path = os.path.join(main_dir, avg_folder, mode_folder)
    os.makedirs(folder_path, exist_ok=True)
    
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
    
    # Create filename with version number
    if version:
        output_file = f"Dynamic_avg_{avg_type}_nJobsPerRound_{nJobsPerRound}_mode_{mode}_round_{version}.csv"
    else:
        output_file = f"Dynamic_avg_{avg_type}_nJobsPerRound_{nJobsPerRound}_mode_{mode}.csv"
    
    file_path = os.path.join(folder_path, output_file)
    
    # Check if file exists to determine if we need to write header
    write_header = not os.path.exists(file_path)
    
    # Write or append to CSV
    with open(file_path, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if write_header:
            writer.writerow(['arrival_rate', 'bp_L', 'bp_H', 'FCFS_percentage', 'SRPT_percentage', 'total_rounds'])
        writer.writerow([arrival_rate, bp_L, bp_H, f"{fcfs_percentage:.1f}", f"{srpt_percentage:.1f}", total_rounds])
    
    # Save detailed round-by-round algorithm usage
    save_round_details(input_file_path, nJobsPerRound, mode, algorithm_history, version)

def save_round_details(input_file_path, nJobsPerRound, mode, algorithm_history, version):
    """Save detailed round-by-round algorithm selection with version handling"""
    if not algorithm_history:
        return
    
    # Extract folder information
    dir_path = os.path.dirname(input_file_path)
    folder_name = os.path.basename(dir_path)
    filename = os.path.basename(input_file_path)
    
    # Check if it's an avg file (not random/softrandom)
    if not folder_name.startswith('avg_'):
        return
    
    # Extract avg type
    avg_type_match = re.search(r'avg_(\d+)', folder_name)
    if not avg_type_match:
        return
    avg_type = avg_type_match.group(1)
    
    # Parse filename to get parameters
    arrival_rate, bp_L, bp_H = parse_avg30_filename(filename)
    if arrival_rate is None:
        return
    
    # Create folder structure for round details
    main_dir = "Dynamic_analysis"
    avg_folder = f"avg_{avg_type}"
    mode_folder = f"mode_{mode}"
    round_details_folder = "round_details"
    folder_path = os.path.join(main_dir, avg_folder, mode_folder, round_details_folder)
    os.makedirs(folder_path, exist_ok=True)
    
    # Create filename for round details with version
    if version:
        detail_file = f"rounds_arr{arrival_rate}_L{bp_L}_H{bp_H}_njobs{nJobsPerRound}_v{version}.csv"
    else:
        detail_file = f"rounds_arr{arrival_rate}_L{bp_L}_H{bp_H}_njobs{nJobsPerRound}.csv"
    
    file_path = os.path.join(folder_path, detail_file)
    
    # Write round details
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Round', 'Algorithm_Used'])
        for i, algo in enumerate(algorithm_history, 1):
            writer.writerow([i, algo])

def DYNAMIC(jobs, nJobsPerRound = 100, mode=1, input_file_name=None):
    """
    Dynamic scheduling algorithm with 6 modes:
    Mode 1: Use jobs from previous round to decide current round's schedule
    Mode 2: Use jobs from 2 previous rounds (requires current round >= 3)
    Mode 3: Use jobs from 4 previous rounds (requires current round >= 5)
    Mode 4: Use jobs from 8 previous rounds (requires current round >= 9)
    Mode 5: Use jobs from 16 previous rounds (requires current round >= 17)
    Mode 6: Use all jobs from round 1 to current round-1
    
    If current round doesn't meet mode requirements, fallback to mode 1
    """
    total_jobs = len(jobs)

    current_time = 0
    active_jobs = []
    completed_jobs = []
    n_arrival_jobs = 0
    n_completed_jobs = 0
    is_srpt_better = True  # Start with SRPT by default for first round
    jobs_pointer = 0
    jobs_in_current_round = []  # Jobs arriving in current round
    current_job = None
    
    # Store all jobs from each round for future simulations
    round_jobs_history = []  # List of lists, each containing jobs from a round
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
        # Check for new job arrivals - FIXED: use <= instead of ==
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] <= current_time:
            job = jobs[jobs_pointer]
            # Create a clean copy for the active queue (without completion_time)
            job_copy = {
                'arrival_time': job['arrival_time'],
                'job_size': job['job_size'],
                'remaining_time': job['remaining_time'],
                'job_index': job['job_index'],
                'completion_time': None,
                'start_time': None
            }
            active_jobs.append(job_copy)
            
            # Create a clean copy for round tracking (only essential info for simulation)
            round_job = {
                'arrival_time': job['arrival_time'],
                'job_size': job['job_size'],
                'job_index': job['job_index']
            }
            jobs_in_current_round.append(round_job)
            
            n_arrival_jobs += 1
            jobs_pointer += 1

        # Checkpoint logic
        if n_arrival_jobs >= nJobsPerRound:
            if jobs_in_current_round:
                # Store the current round's jobs for future use
                round_jobs_history.append(copy.deepcopy(jobs_in_current_round))
                
                # Decide which algorithm to use for the CURRENT round
                if current_round == 1:
                    # First round defaults to SRPT
                    is_srpt_better = True
                    algorithm_history.append('SRPT')
                else:
                    # Determine effective mode based on current round
                    effective_mode = mode
                    
                    # Check if we need to fallback to mode 1
                    if mode == 2 and current_round < 3:
                        effective_mode = 1
                    elif mode == 3 and current_round < 5:
                        effective_mode = 1
                    elif mode == 4 and current_round < 9:
                        effective_mode = 1
                    elif mode == 5 and current_round < 17:
                        effective_mode = 1
                    
                    # Collect jobs from previous rounds based on effective mode
                    jobs_to_simulate = []
                    
                    if effective_mode == 1:
                        # Mode 1: Use only the previous round's jobs
                        jobs_to_simulate = copy.deepcopy(round_jobs_history[-1])
                    
                    elif effective_mode == 2:
                        # Mode 2: Use jobs from last 2 rounds
                        for round_jobs in round_jobs_history[-2:]:
                            jobs_to_simulate.extend(copy.deepcopy(round_jobs))
                    
                    elif effective_mode == 3:
                        # Mode 3: Use jobs from last 4 rounds
                        for round_jobs in round_jobs_history[-4:]:
                            jobs_to_simulate.extend(copy.deepcopy(round_jobs))
                    
                    elif effective_mode == 4:
                        # Mode 4: Use jobs from last 8 rounds
                        for round_jobs in round_jobs_history[-8:]:
                            jobs_to_simulate.extend(copy.deepcopy(round_jobs))
                    
                    elif effective_mode == 5:
                        # Mode 5: Use jobs from last 16 rounds
                        for round_jobs in round_jobs_history[-16:]:
                            jobs_to_simulate.extend(copy.deepcopy(round_jobs))
                    
                    elif effective_mode == 6:
                        # Mode 6: Use all jobs from round 1 to current round-1
                        for round_jobs in round_jobs_history:
                            jobs_to_simulate.extend(copy.deepcopy(round_jobs))
                    
                    # Simulate SRPT and FCFS on the collected jobs
                    srpt_jobs_copy = copy.deepcopy(jobs_to_simulate)
                    fcfs_jobs_copy = copy.deepcopy(jobs_to_simulate)
                    
                    srpt_avg, srpt_l2 = Srpt(srpt_jobs_copy)
                    fcfs_avg, fcfs_l2 = Fcfs(fcfs_jobs_copy)
                         
                    # Choose algorithm based on L2 norm comparison
                    is_srpt_better = srpt_l2 <= fcfs_l2
                    algorithm_history.append('SRPT' if is_srpt_better else 'FCFS')
                
                current_round += 1
                
            jobs_in_current_round = []
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

def extract_version_from_path(folder_path):
    """Extract version number (1-10) from folder path like 'avg_30_2' or 'freq_16_2'"""
    # Match patterns like avg_30_1, freq_16_2, softrandom_3, etc.
    pattern = r'_(\d+)$'
    match = re.search(pattern, folder_path)
    if match:
        return int(match.group(1))
    return None

def read_jobs_from_csv(filepath):
    """Read jobs from CSV file"""
    jobs = []
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                job = {
                    'arrival_time': int(row['arrival_time']),
                    'job_size': int(row['job_size'])
                }
                jobs.append(job)
        logger.info(f"Successfully read {len(jobs)} jobs from {filepath}")
        return jobs
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return None

def parse_avg30_filename(filename):
    """Parse avg30 filename to extract arrival_rate, bp_L, and bp_H"""
    # Pattern: (arrival_rate, bp_L_bp_H).csv
    # Example: (20, 4.073_262144).csv or (28, 7.918_512).csv
    pattern = r'\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)_(\d+)\)'
    match = re.search(pattern, filename)
    if match:
        arrival_rate = float(match.group(1))
        bp_L = float(match.group(2))
        bp_H = int(match.group(3))
        return arrival_rate, bp_L, bp_H
    return None, None, None

def parse_freq_from_folder(folder_name):
    """Extract frequency value from folder name like freq_2_1"""
    # Pattern now handles freq_2_1, freq_16_2, etc.
    pattern = r'freq_(\d+)(?:_\d+)?'
    match = re.search(pattern, folder_name)
    if match:
        return int(match.group(1))
    return None

def run_all_modes_for_file(jobs, nJobsPerRound, input_file_path=None):
    """Run all 6 modes for a given job set and return results"""
    mode_results = {}
    
    for mode in range(1, 7):
        try:
            # Create a deep copy to ensure each mode gets fresh job data
            jobs_copy = copy.deepcopy(jobs)
            avg_flow_time, l2_norm_flow_time = DYNAMIC(
                jobs_copy,
                nJobsPerRound=nJobsPerRound,
                mode=mode,
                input_file_name=input_file_path  # Pass the file path for analysis
            )
            mode_results[mode] = l2_norm_flow_time
            logger.info(f"    Mode {mode}: L2 norm = {l2_norm_flow_time:.4f}")
        except Exception as e:
            logger.error(f"    Error in mode {mode}: {e}")
            mode_results[mode] = None
    
    return mode_results

def process_avg_folders(data_dir, output_dir, nJobsPerRound):
    """Process all avg_30_*, avg_60_*, avg_90_* folders"""
    
    # Find all avg folders with version numbers
    avg_patterns = ['avg_30_*']
    
    for pattern in avg_patterns:
        avg_folders = glob.glob(os.path.join(data_dir, pattern))
        
        for avg_folder in sorted(avg_folders):
            if not os.path.isdir(avg_folder):
                continue
                
            folder_name = os.path.basename(avg_folder)
            version = extract_version_from_path(folder_name)
            
            # Extract avg type (30, 60, or 90)
            avg_type_match = re.search(r'avg_(\d+)', folder_name)
            if not avg_type_match:
                continue
            avg_type = avg_type_match.group(1)
            
            logger.info(f"Processing folder: {folder_name} (version={version})")
            
            # Create output directory
            avg_result_dir = os.path.join(output_dir, f'avg{avg_type}_result')
            os.makedirs(avg_result_dir, exist_ok=True)
            
            # Group results by arrival_rate
            results_by_arrival_rate = {}
            
            # Process all CSV files in this folder
            csv_files = glob.glob(os.path.join(avg_folder, '*.csv'))
            
            for csv_file in csv_files:
                filename = os.path.basename(csv_file)
                arrival_rate, bp_L, bp_H = parse_avg30_filename(filename)
                
                if arrival_rate is None:
                    logger.warning(f"Could not parse filename: {filename}")
                    continue
                
                logger.info(f"  Processing {filename}: arrival_rate={arrival_rate}, bp_L={bp_L}, bp_H={bp_H}")
                
                # Read jobs
                jobs = read_jobs_from_csv(csv_file)
                if jobs is None:
                    continue
                
                # Run all 6 modes
                mode_results = run_all_modes_for_file(jobs, nJobsPerRound, csv_file)
                
                # Store results
                if arrival_rate not in results_by_arrival_rate:
                    results_by_arrival_rate[arrival_rate] = []
                
                results_by_arrival_rate[arrival_rate].append({
                    'bp_parameter_L': bp_L,
                    'bp_parameter_H': bp_H,
                    'mode_results': mode_results
                })
            
            # Write results grouped by arrival_rate with version number
            for arrival_rate, results in results_by_arrival_rate.items():
                if version:
                    output_file = os.path.join(avg_result_dir, f"{int(arrival_rate)}_Dynamic_result_{version}.csv")
                else:
                    output_file = os.path.join(avg_result_dir, f"{int(arrival_rate)}_Dynamic_result.csv")
                
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Create header with all mode columns - FIXED format
                    header = ['arrival_rate', 'bp_parameter_L', 'bp_parameter_H']
                    for mode in range(1, 7):
                        header.append(f'Dynamic_njobs{nJobsPerRound}_mode{mode}_L2_norm_flow_time')
                    writer.writerow(header)
                    
                    # Sort results by bp_L and bp_H for consistency
                    results.sort(key=lambda x: (x['bp_parameter_L'], x['bp_parameter_H']))
                    
                    # Write data rows
                    for result in results:
                        row = [arrival_rate, result['bp_parameter_L'], result['bp_parameter_H']]
                        for mode in range(1, 7):
                            value = result['mode_results'].get(mode, '')
                            row.append(value if value is not None else '')
                        writer.writerow(row)
                
                logger.info(f"  Saved results for arrival_rate={arrival_rate} to {output_file}")

def process_random_folders(data_dir, output_dir, nJobsPerRound):
    """Process all freq_* folders for random files"""
    
    # Create output directory
    random_result_dir = os.path.join(output_dir, 'random_result')
    os.makedirs(random_result_dir, exist_ok=True)
    
    # Group results by version number
    results_by_version = {}
    
    # Find all freq folders
    freq_folders = glob.glob(os.path.join(data_dir, 'freq_*'))
    
    for freq_folder in sorted(freq_folders):
        if not os.path.isdir(freq_folder):
            continue
            
        folder_name = os.path.basename(freq_folder)
        frequency = parse_freq_from_folder(folder_name)
        version = extract_version_from_path(folder_name)
        
        if frequency is None:
            logger.warning(f"Could not parse frequency from folder: {folder_name}")
            continue
        
        logger.info(f"Processing folder: {folder_name} (freq={frequency}, version={version})")
        
        # Look for random_freq_*.csv files
        random_files = glob.glob(os.path.join(freq_folder, 'random_freq_*.csv'))
        
        for random_file in random_files:
            filename = os.path.basename(random_file)
            logger.info(f"  Processing {filename}")
            
            # Read jobs
            jobs = read_jobs_from_csv(random_file)
            if jobs is None:
                continue
            
            # Run all 6 modes (no analysis needed for random files)
            mode_results = run_all_modes_for_file(jobs, nJobsPerRound, None)
            
            # Group results by version
            if version not in results_by_version:
                results_by_version[version] = []
            
            results_by_version[version].append({
                'frequency': frequency,
                'mode_results': mode_results
            })
    
    # Write results grouped by version
    for version, results in results_by_version.items():
        if results:
            if version:
                output_file = os.path.join(random_result_dir, f"random_result_Dynamic_njobs{nJobsPerRound}_{version}.csv")
            else:
                output_file = os.path.join(random_result_dir, f"random_result_Dynamic_njobs{nJobsPerRound}.csv")
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Create header - FIXED format
                header = ['frequency']
                for mode in range(1, 7):
                    header.append(f'Dynamic_njobs{nJobsPerRound}_mode{mode}_L2_norm_flow_time')
                writer.writerow(header)
                
                # Sort by frequency
                results.sort(key=lambda x: x['frequency'])
                
                # Write data rows
                for result in results:
                    row = [result['frequency']]
                    for mode in range(1, 7):
                        value = result['mode_results'].get(mode, '')
                        row.append(value if value is not None else '')
                    writer.writerow(row)
            
            logger.info(f"  Saved random results (version {version}) to {output_file}")

def process_softrandom_folders(data_dir, output_dir, nJobsPerRound):
    """Process all softrandom_* folders"""
    
    # Create output directory
    softrandom_result_dir = os.path.join(output_dir, 'softrandom_result')
    os.makedirs(softrandom_result_dir, exist_ok=True)
    
    # Group results by version number
    results_by_version = {}
    
    # Find all softrandom base folders with version numbers
    softrandom_folders = glob.glob(os.path.join(data_dir, 'softrandom_*'))
    
    for softrandom_base in sorted(softrandom_folders):
        if not os.path.isdir(softrandom_base):
            continue
            
        base_folder_name = os.path.basename(softrandom_base)
        base_version = extract_version_from_path(base_folder_name)
        
        logger.info(f"Processing softrandom base: {base_folder_name} (version={base_version})")
        
        # Look for freq_* folders inside softrandom
        freq_folders = glob.glob(os.path.join(softrandom_base, 'freq_*'))
        
        for freq_folder in sorted(freq_folders):
            if not os.path.isdir(freq_folder):
                continue
                
            folder_name = os.path.basename(freq_folder)
            frequency = parse_freq_from_folder(folder_name)
            
            if frequency is None:
                logger.warning(f"Could not parse frequency from folder: {folder_name}")
                continue
            
            logger.info(f"  Processing subfolder: {folder_name} (freq={frequency})")
            
            # Look for softrandom_freq_*.csv files
            softrandom_files = glob.glob(os.path.join(freq_folder, 'softrandom_freq_*.csv'))
            
            for softrandom_file in softrandom_files:
                filename = os.path.basename(softrandom_file)
                logger.info(f"    Processing {filename}")
                
                # Read jobs
                jobs = read_jobs_from_csv(softrandom_file)
                if jobs is None:
                    continue
                
                # Run all 6 modes (no analysis needed for softrandom files)
                mode_results = run_all_modes_for_file(jobs, nJobsPerRound, None)
                
                # Group results by version
                if base_version not in results_by_version:
                    results_by_version[base_version] = []
                
                results_by_version[base_version].append({
                    'frequency': frequency,
                    'mode_results': mode_results
                })
    
    # Write results grouped by version
    for version, results in results_by_version.items():
        if results:
            if version:
                output_file = os.path.join(softrandom_result_dir, f"softrandom_result_Dynamic_njobs{nJobsPerRound}_{version}.csv")
            else:
                output_file = os.path.join(softrandom_result_dir, f"softrandom_result_Dynamic_njobs{nJobsPerRound}.csv")
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Create header - FIXED format
                header = ['frequency']
                for mode in range(1, 7):
                    header.append(f'Dynamic_njobs{nJobsPerRound}_mode{mode}_L2_norm_flow_time')
                writer.writerow(header)
                
                # Sort by frequency
                results.sort(key=lambda x: x['frequency'])
                
                # Write data rows
                for result in results:
                    row = [result['frequency']]
                    for mode in range(1, 7):
                        value = result['mode_results'].get(mode, '')
                        row.append(value if value is not None else '')
                    writer.writerow(row)
            
            logger.info(f"  Saved softrandom results (version {version}) to {output_file}")

def main():
    """Main function to process all data"""
    
    # Configuration
    data_dir = 'data'  # Base directory containing all folders
    output_dir = 'Dynamic_result'  # Output directory for results
    nJobsPerRound = 100  # Adjust as needed
    
    logger.info("="*60)
    logger.info(f"Starting batch processing with settings:")
    logger.info(f"  Data directory: {data_dir}")
    logger.info(f"  Output directory: {output_dir}")
    logger.info(f"  nJobsPerRound: {nJobsPerRound}")
    logger.info(f"  Running all modes (1-6) for each file")
    logger.info("="*60)
    
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # # Process avg folders
    # logger.info("\n" + "="*40)
    # logger.info("Processing avg folders...")
    # logger.info("="*40)
    # process_avg_folders(data_dir, output_dir, nJobsPerRound)
    
    # Process random files
    logger.info("\n" + "="*40)
    logger.info("Processing random files...")
    logger.info("="*40)
    process_random_folders(data_dir, output_dir, nJobsPerRound)
    
    # Process softrandom files
    logger.info("\n" + "="*40)
    logger.info("Processing softrandom files...")
    logger.info("="*40)
    process_softrandom_folders(data_dir, output_dir, nJobsPerRound)
    
    logger.info("\n" + "="*60)
    logger.info("Batch processing completed successfully!")
    logger.info("="*60)

if __name__ == "__main__":
    main()