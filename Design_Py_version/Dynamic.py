import math
import csv
import copy
import os
import re
import glob
from SRPT_Selector import select_next_job_optimized as srpt_select_next_job
from FCFS_Selector import select_next_job_optimized as fcfs_select_next_job
import logging
from typing import List, Dict, Tuple, Optional
from multiprocessing import Pool, cpu_count,freeze_support
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# -----------------------------
# Optimized, API-compatible SRPT
# -----------------------------
def Srpt(jobs: List[Dict]) -> Tuple[float, float,float]:
    """
    Optimized SRPT simulator (same I/O, same results).
    - Event-driven time advance: run until next arrival or completion (min step).
    - Avoid per-tick loops; drastically fewer iterations.
    - Keeps selectors and outputs identical to the old version.
    """
    if not jobs:
        return 0.0, 0.0,0.0

    # Assign job indices (stable and explicit)
    for idx, job in enumerate(jobs):
        job['job_index'] = idx

    # Sort by arrival once
    jobs_sorted = sorted(jobs, key=lambda x: x['arrival_time'])
    total_jobs = len(jobs_sorted)

    current_time = 0
    jobs_pointer = 0  # next job to admit
    completed_jobs: List[Dict] = []
    job_queue: List[Dict] = []  # waiting jobs

    # Helper to admit all arrivals up to current_time
    def admit_until_now(t: int):
        nonlocal jobs_pointer
        while jobs_pointer < total_jobs and jobs_sorted[jobs_pointer]['arrival_time'] <= t:
            j = jobs_sorted[jobs_pointer]
            job_queue.append({
                'arrival_time': j['arrival_time'],
                'job_size': j['job_size'],
                'remaining_time': j['job_size'],
                'job_index': j['job_index'],
                'completion_time': None,
                'start_time': None,
            })
            jobs_pointer += 1

    while len(completed_jobs) < total_jobs:
        # Admit any arrived jobs for current_time
        admit_until_now(current_time)

        # Pick next job (SRPT) using optimized selector
        selected_job = srpt_select_next_job(job_queue) if job_queue else None

        if selected_job:
            # Determine delta until next arrival (if any) to keep preemption points correct
            next_arrival_t = jobs_sorted[jobs_pointer]['arrival_time'] if jobs_pointer < total_jobs else None
            if next_arrival_t is None:
                # No more arrivals: run to completion
                delta = selected_job['remaining_time']
            else:
                # Run only until either next arrival or completion
                gap = max(1, next_arrival_t - current_time)  # at least 1 time unit
                delta = min(selected_job['remaining_time'], gap)

            # Remove selected from queue (find by identity keys, stable)
            for idx, j in enumerate(job_queue):
                if (j['job_index'] == selected_job['job_index'] and
                    j['arrival_time'] == selected_job['arrival_time'] and
                    j['job_size'] == selected_job['job_size'] and
                    j['remaining_time'] == selected_job['remaining_time']):
                    job = job_queue.pop(idx)
                    break
            else:
                # Fallback (shouldn't happen): just pop first
                job = job_queue.pop(0)

            # Start time - ensure it's at or after arrival time
            if job['start_time'] is None:
                job['start_time'] = max(current_time, job['arrival_time'])

            # Execute
            job['remaining_time'] -= delta
            current_time += delta

            if job['remaining_time'] == 0:
                job['completion_time'] = current_time
                completed_jobs.append(job)
            else:
                # Re-queue for potential preemption
                job_queue.append(job)
        else:
            # Idle: jump to next arrival
            if jobs_pointer < total_jobs:
                current_time = max(current_time, jobs_sorted[jobs_pointer]['arrival_time'])
            else:
                break  # nothing left

    # Metrics (identical to old version)
    total_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    max_flow = max(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    if total_jobs > 0:
        avg_flow_time = total_flow_time / total_jobs
        l2_norm_flow_time = math.sqrt(sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs))
    else:
        avg_flow_time = 0
        l2_norm_flow_time = 0

    return avg_flow_time, l2_norm_flow_time,max_flow


# -----------------------------
# Optimized, API-compatible FCFS
# -----------------------------
def Fcfs(jobs: List[Dict]) -> Tuple[float, float,float]:
    """
    Optimized FCFS simulator (same I/O, same results):
    - Event-driven; non-preemptive job runs to completion.
    - Avoid per-tick loops; admit arrivals in batches.
    """
    if not jobs:
        return 0.0, 0.0,0.0

    # Assign job indices
    for idx, job in enumerate(jobs):
        job['job_index'] = idx

    jobs_sorted = sorted(jobs, key=lambda x: x['arrival_time'])
    total_jobs = len(jobs_sorted)

    current_time = 0
    jobs_pointer = 0
    completed_jobs: List[Dict] = []
    waiting_queue: List[Dict] = []
    current_job: Optional[Dict] = None

    def admit_until_now(t: int):
        nonlocal jobs_pointer
        while jobs_pointer < total_jobs and jobs_sorted[jobs_pointer]['arrival_time'] <= t:
            j = jobs_sorted[jobs_pointer]
            waiting_queue.append({
                'arrival_time': j['arrival_time'],
                'job_size': j['job_size'],
                'remaining_time': j['job_size'],
                'job_index': j['job_index'],
                'completion_time': None,
                'start_time': None,
            })
            jobs_pointer += 1

    while len(completed_jobs) < total_jobs:
        admit_until_now(current_time)

        if current_job is None and waiting_queue:
            # FCFS selector picks earliest arrival using optimized selector
            selected = fcfs_select_next_job(waiting_queue)
            # Remove the selected item
            for idx, j in enumerate(waiting_queue):
                if (j['job_index'] == selected['job_index'] and
                    j['arrival_time'] == selected['arrival_time'] and
                    j['job_size'] == selected['job_size']):
                    current_job = waiting_queue.pop(idx)
                    break
            else:
                current_job = waiting_queue.pop(0)

            if current_job['start_time'] is None:
                # Ensure start time is at or after arrival
                current_time = max(current_time, current_job['arrival_time'])
                current_job['start_time'] = current_time

        if current_job is not None:
            # Non-preemptive: run to completion in one step
            current_time += current_job['remaining_time']
            current_job['remaining_time'] = 0
            current_job['completion_time'] = current_time
            completed_jobs.append(current_job)
            current_job = None
            continue

        # If nothing to run, jump to next arrival
        if jobs_pointer < total_jobs:
            current_time = max(current_time, jobs_sorted[jobs_pointer]['arrival_time'])
        else:
            break

    total_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    max_flow = max(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    if total_jobs > 0:
        avg_flow_time = total_flow_time / total_jobs
        l2_norm_flow_time = (sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs))**0.5
    else:
        avg_flow_time = 0
        l2_norm_flow_time = 0

    return avg_flow_time, l2_norm_flow_time, max_flow


# ----------------------------------
# FIXED AND OPTIMIZED DYNAMIC
# ----------------------------------
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
    arrival_rate, bp_L, bp_H = parse_avg_filename(filename)
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
    arrival_rate, bp_L, bp_H = parse_avg_filename(filename)
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
    Mode 7: At round n: Re-execute the most recent ceil(0.5 * total_jobs) jobs
    
    If current round doesn't meet mode requirements, fallback to mode 1
    
    BUG FIX: Properly carry over excess jobs to next round count
    OPTIMIZATION: Use optimized selectors
    """
    total_jobs = len(jobs)

    current_time = 0
    active_jobs = []
    completed_jobs = []
    n_arrival_jobs = 0  # Jobs counted for current round
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
        job['start_time'] = None

    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x['arrival_time'])

    while n_completed_jobs < total_jobs:
        # Admit all jobs up to current_time (batch, not tick-by-tick)
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] <= current_time:
            job = jobs[jobs_pointer]
            job_copy = {
                'arrival_time': job['arrival_time'],
                'job_size': job['job_size'],
                'remaining_time': job['remaining_time'],
                'job_index': job['job_index'],
                'completion_time': None,
                'start_time': None
            }
            active_jobs.append(job_copy)
            
            # Track only essential fields for history
            jobs_in_current_round.append({
                'arrival_time': job['arrival_time'],
                'job_size': job['job_size'],
                'job_index': job['job_index']
            })
            
            n_arrival_jobs += 1
            jobs_pointer += 1

        # Checkpoint logic when we have nJobsPerRound arrivals
        # BUG FIX: Properly handle excess jobs
        while n_arrival_jobs >= nJobsPerRound:
            # Process exactly nJobsPerRound jobs for this round
            jobs_for_this_round = jobs_in_current_round[:nJobsPerRound]
            
            if jobs_for_this_round:
                # Store the current round's jobs
                round_jobs_history.append(list(jobs_for_this_round))
                
                # Decide which algorithm to use for the CURRENT round
                if current_round == 1:
                    is_srpt_better = True
                    algorithm_history.append('SRPT')
                else:
                    # Fallback rules to mode 1 when not enough history yet
                    effective_mode = mode
                    if mode == 2 and current_round < 3:
                        effective_mode = 1
                    elif mode == 3 and current_round < 5:
                        effective_mode = 1
                    elif mode == 4 and current_round < 9:
                        effective_mode = 1
                    elif mode == 5 and current_round < 17:
                        effective_mode = 1
                    
                    # Collect jobs from previous rounds per effective mode
                    jobs_to_simulate = []
                    if effective_mode == 1:
                        jobs_to_simulate = list(round_jobs_history[-1])
                    elif effective_mode == 2:
                        for r in round_jobs_history[-2:]:
                            jobs_to_simulate.extend(r)
                    elif effective_mode == 3:
                        for r in round_jobs_history[-4:]:
                            jobs_to_simulate.extend(r)
                    elif effective_mode == 4:
                        for r in round_jobs_history[-8:]:
                            jobs_to_simulate.extend(r)
                    elif effective_mode == 5:
                        for r in round_jobs_history[-16:]:
                            jobs_to_simulate.extend(r)
                    elif effective_mode == 6:
                        for r in round_jobs_history:
                            jobs_to_simulate.extend(r)
                    elif effective_mode == 7:
                        for r in round_jobs_history[-math.ceil(current_round*0.5):]:
                            jobs_to_simulate.extend(r)
                    
                    # Run SRPT and FCFS on the collected jobs
                    srpt_avg, srpt_l2,max_flow_srpt = Srpt([{'arrival_time': j['arrival_time'], 'job_size': j['job_size']} for j in jobs_to_simulate])
                    fcfs_avg, fcfs_l2,max_flow_fcfs = Fcfs([{'arrival_time': j['arrival_time'], 'job_size': j['job_size']} for j in jobs_to_simulate])
                         
                    # Choose algorithm based on L2 norm comparison
                    is_srpt_better = srpt_l2 <= fcfs_l2
                    algorithm_history.append('SRPT' if is_srpt_better else 'FCFS')
                
                current_round += 1
            
            # Move excess jobs to next round
            jobs_in_current_round = jobs_in_current_round[nJobsPerRound:]
            n_arrival_jobs -= nJobsPerRound

        # Select next job based on the current scheduling policy
        if active_jobs:
            if is_srpt_better:
                selected_job = srpt_select_next_job(active_jobs)
            else:
                selected_job = fcfs_select_next_job(active_jobs)
        else:
            selected_job = None

        if selected_job:
            # Decide event-driven step:
            next_arrival_t = jobs[jobs_pointer]['arrival_time'] if jobs_pointer < total_jobs else None
            if is_srpt_better:
                # SRPT: allow preemption at arrivals, run until min(next arrival, completion)
                if next_arrival_t is None:
                    delta = selected_job['remaining_time']
                else:
                    delta = min(selected_job['remaining_time'], max(1, next_arrival_t - current_time))
            else:
                # FCFS mode inside DYNAMIC is non-preemptive: run to completion
                delta = selected_job['remaining_time']

            # Remove selected
            for idx, j in enumerate(active_jobs):
                if (j['job_index'] == selected_job['job_index'] and
                    j['arrival_time'] == selected_job['arrival_time'] and
                    j['job_size'] == selected_job['job_size'] and
                    j['remaining_time'] == selected_job['remaining_time']):
                    job = active_jobs.pop(idx)
                    break
            else:
                job = active_jobs.pop(0)

            # Set start time if not set (ensure >= arrival_time)
            if job['start_time'] is None:
                job['start_time'] = max(current_time, job['arrival_time'])

            job['remaining_time'] -= delta
            current_time += delta

            if job['remaining_time'] == 0:
                job['completion_time'] = current_time
                completed_jobs.append(job)
                n_completed_jobs += 1
            else:
                # Only SRPT can be preempted here
                active_jobs.append(job)
        else:
            # No job to run; jump to next arrival
            if jobs_pointer < total_jobs:
                current_time = max(current_time, jobs[jobs_pointer]['arrival_time'])
            else:
                break

    # Process any remaining jobs in the last incomplete round
    if jobs_in_current_round and n_arrival_jobs > 0:
        round_jobs_history.append(list(jobs_in_current_round))
        # The last round uses the same algorithm as determined for current state
        algorithm_history.append('SRPT' if is_srpt_better else 'FCFS')
        current_round += 1

    # Metrics
    total_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    max_flow = max(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    if total_jobs > 0:
        avg_flow_time = total_flow_time / total_jobs
        l2_norm_flow_time = math.sqrt(sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs))
    else:
        avg_flow_time = 0
        l2_norm_flow_time = 0
        max_flow = 0
    
    # Save analysis for avg_* files only
    if input_file_name:
        save_analysis_results(input_file_name, nJobsPerRound, mode, algorithm_history, current_round - 1)

    return avg_flow_time, l2_norm_flow_time, max_flow


# -----------------------------
# Helpers and batch processors (unchanged)
# -----------------------------
def extract_version_from_path(folder_path):
    """Extract version number (1-10) from folder path like 'avg_30_2' or 'freq_16_2'"""
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

def parse_avg_filename(filename):
    """Parse avg filename to extract arrival_rate, bp_L, and bp_H"""
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
    pattern = r'freq_(\d+)(?:_\d+)?'
    match = re.search(pattern, folder_name)
    if match:
        return int(match.group(1))
    return None
def run_all_modes_for_file_normal(jobs, nJobsPerRound, input_file_path=None):
    """Run all 7 modes for NORMAL cases - ONLY return L2 norm results"""
    mode_results = {}
    
    for mode in range(1, 8):
        try:
            jobs_copy = [{'arrival_time': j['arrival_time'], 'job_size': j['job_size']} for j in jobs]
            result = DYNAMIC(
                jobs_copy,
                nJobsPerRound=nJobsPerRound,
                mode=mode,
                input_file_name=input_file_path
            )
            
            # Handle both old and new return formats
            if len(result) == 3:
                _, l2_norm_flow_time, _ = result  # Ignore max flow time
            else:
                _, l2_norm_flow_time = result
                
            mode_results[mode] = l2_norm_flow_time
            logger.info(f"    Mode {mode}: L2 norm = {l2_norm_flow_time:.4f}")
        except Exception as e:
            logger.error(f"    Error in mode {mode}: {e}")
            mode_results[mode] = None
    
    return mode_results  # Returns dictionary, not tuple
def run_all_modes_for_file_frequency(jobs, nJobsPerRound, input_file_path=None):
    """Run all 6 modes for a given job set and return results with max flow time"""
    mode_results = {}
    max_flow_results = {}  # NEW: Track max flow time results
    
    for mode in range(1, 8):
        try:
            jobs_copy = [{'arrival_time': j['arrival_time'], 'job_size': j['job_size']} for j in jobs]
            avg_flow_time, l2_norm_flow_time, max_flow_time = DYNAMIC(  # CHANGED: Capture third value
                jobs_copy,
                nJobsPerRound=nJobsPerRound,
                mode=mode,
                input_file_name=input_file_path
            )
            mode_results[mode] = l2_norm_flow_time
            max_flow_results[mode] = max_flow_time  # NEW: Store max flow time
            logger.info(f"    Mode {mode}: L2 norm = {l2_norm_flow_time:.4f}, Max flow = {max_flow_time:.4f}")
        except Exception as e:
            logger.error(f"    Error in mode {mode}: {e}")
            mode_results[mode] = None
            max_flow_results[mode] = None
    
    return mode_results, max_flow_results
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
                arrival_rate, bp_L, bp_H = parse_avg_filename(filename)
                
                if arrival_rate is None:
                    logger.warning(f"Could not parse filename: {filename}")
                    continue
                
                logger.info(f"  Processing {filename}: arrival_rate={arrival_rate}, bp_L={bp_L}, bp_H={bp_H}")
                
                # Read jobs
                jobs = read_jobs_from_csv(csv_file)
                if jobs is None:
                    continue
                
                # Run all 6 modes
                mode_results = run_all_modes_for_file_normal(jobs, nJobsPerRound, csv_file)
                
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
                    
                    # Create header with all mode columns
                    header = ['arrival_rate', 'bp_parameter_L', 'bp_parameter_H']
                    for mode in range(1, 8):
                        header.append(f'Dynamic_njobs{nJobsPerRound}_mode{mode}_L2_norm_flow_time')
                    writer.writerow(header)
                    
                    # Sort results by bp_L and bp_H for consistency
                    results.sort(key=lambda x: (x['bp_parameter_L'], x['bp_parameter_H']))
                    
                    # Write data rows
                    for result in results:
                        row = [arrival_rate, result['bp_parameter_L'], result['bp_parameter_H']]
                        for mode in range(1, 8):
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
            
            # FIXED: Properly unpack the tuple returned by frequency function
            mode_results, max_flow_results = run_all_modes_for_file_frequency(jobs, nJobsPerRound, None)
            
            # Group results by version
            if version not in results_by_version:
                results_by_version[version] = []
            
            results_by_version[version].append({
                'frequency': frequency,
                'mode_results': mode_results,        # This is now properly unpacked as a dictionary
                'max_flow_results': max_flow_results # This is now properly unpacked as a dictionary
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
                
                # Create header with both L2 norm and max flow time
                header = ['frequency']
                for mode in range(1, 8):
                    header.append(f'Dynamic_njobs{nJobsPerRound}_mode{mode}_L2_norm_flow_time')
                for mode in range(1, 8):
                    header.append(f'Dynamic_njobs{nJobsPerRound}_mode{mode}_max_flow_time')
                writer.writerow(header)
                
                # Sort by frequency
                results.sort(key=lambda x: x['frequency'])
                
                # Write data rows
                for result in results:
                    row = [result['frequency']]
                    # Add L2 norm values
                    for mode in range(1, 8):
                        value = result['mode_results'].get(mode, '')  # This now works because mode_results is a dict
                        row.append(value if value is not None else '')
                    # Add max flow time values
                    for mode in range(1, 8):
                        value = result['max_flow_results'].get(mode, '')  # This now works because max_flow_results is a dict
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
                
                # FIXED: Properly unpack the tuple returned by frequency function
                mode_results, max_flow_results = run_all_modes_for_file_frequency(jobs, nJobsPerRound, None)
                
                # Group results by version
                if base_version not in results_by_version:
                    results_by_version[base_version] = []
                
                results_by_version[base_version].append({
                    'frequency': frequency,
                    'mode_results': mode_results,        # This is now properly unpacked as a dictionary
                    'max_flow_results': max_flow_results # This is now properly unpacked as a dictionary
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
                
                # Create header with both L2 norm and max flow time
                header = ['frequency']
                for mode in range(1, 8):
                    header.append(f'Dynamic_njobs{nJobsPerRound}_mode{mode}_L2_norm_flow_time')
                for mode in range(1, 8):
                    header.append(f'Dynamic_njobs{nJobsPerRound}_mode{mode}_max_flow_time')
                writer.writerow(header)
                
                # Sort by frequency
                results.sort(key=lambda x: x['frequency'])
                
                # Write data rows
                for result in results:
                    row = [result['frequency']]
                    # Add L2 norm values
                    for mode in range(1, 8):
                        value = result['mode_results'].get(mode, '')  # This now works because mode_results is a dict
                        row.append(value if value is not None else '')
                    # Add max flow time values
                    for mode in range(1, 8):
                        value = result['max_flow_results'].get(mode, '')  # This now works because max_flow_results is a dict
                        row.append(value if value is not None else '')
                    writer.writerow(row)
            
            logger.info(f"  Saved softrandom results (version {version}) to {output_file}")

def main():
    # Configuration
    data_dir = 'data'
    output_dir = 'Dynamic_result'
    nJobsPerRound = 100
    
    # Configure logging for multiprocessing
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(processName)s - %(levelname)s - %(message)s'
    )
    
    logger.info("="*60)
    logger.info(f"Starting batch processing with multiprocessing")
    logger.info(f"  Data directory: {data_dir}")
    logger.info(f"  Output directory: {output_dir}")
    logger.info(f"  nJobsPerRound: {nJobsPerRound}")
    logger.info(f"  Available CPU cores: {cpu_count()}")
    logger.info("="*60)
    
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a pool with 3 workers (one for each task)
    with Pool(processes=min(3, cpu_count())) as pool:
        # Submit all three tasks asynchronously
        avg_result = pool.apply_async(
            process_avg_folders, 
            args=(data_dir, output_dir, nJobsPerRound)
        )
        random_result = pool.apply_async(
            process_random_folders, 
            args=(data_dir, output_dir, nJobsPerRound)
        )
        softrandom_result = pool.apply_async(
            process_softrandom_folders, 
            args=(data_dir, output_dir, nJobsPerRound)
        )
        
        # Wait for all tasks to complete
        avg_result.get()
        logger.info("Avg folders processing completed")
        
        random_result.get()
        logger.info("Random files processing completed")
        
        softrandom_result.get()
        logger.info("Softrandom files processing completed")
    
    logger.info("\n" + "="*60)
    logger.info("All parallel processing completed successfully!")
    logger.info("="*60)

if __name__ == "__main__":
    freeze_support()
    main()