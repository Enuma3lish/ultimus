import math
from SRPT_Selector import select_next_job_optimized as srpt_select_next_job
from BAL_Selector import select_starving_job, select_starving_job_optimized
import os
import csv
import re
import glob
import copy
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def Bal(jobs):
    """
    Optimized BAL scheduler:
    - Starvation rule: waiting_time_ratio = (t - arrival_time) / max(1, remaining_time);
      a job becomes starving when this ratio > N^(2/3) (N = total jobs). We store its first
      starving_time and prefer the earliest starving_time, then larger ratio, then smaller index.
    - Event-driven time advance: run selected job until min(next_arrival, completion).
    - Selection:
        * If starving jobs exist: use select_starving_job_optimized (heap-backed).
        * Else: use SRPT selector (heap-backed) on (remaining_time, arrival_time, job_index).
    Returns (avg_flow_time, l2_norm_flow_time).
    """
    # Normalize jobs & index
    norm = [{"arrival_time": int(j["arrival_time"]), "job_size": int(j["job_size"]), "job_index": i}
            for i, j in enumerate(jobs)]
    norm.sort(key=lambda x: x["arrival_time"])

    total_jobs = len(norm)
    if total_jobs == 0:
        return 0.0, 0.0

    starvation_threshold = total_jobs ** (2/3)

    t = 0
    i = 0  # next arrival pointer
    q = []  # waiting queue of dicts with runtime fields
    completed = []

    while len(completed) < total_jobs:
        # Admit arrivals up to time t
        while i < total_jobs and norm[i]["arrival_time"] <= t:
            q.append({
                "arrival_time": norm[i]["arrival_time"],
                "job_index": norm[i]["job_index"],
                "remaining_time": norm[i]["job_size"],
                "start_time": None,
                "completion_time": None,
                "starving_time": None,
                "waiting_time_ratio": 0.0,
            })
            i += 1

        # Update ratios and starving_time stamps
        if q:
            for job in q:
                if job["remaining_time"] > 0:
                    job["waiting_time_ratio"] = (t - job["arrival_time"]) / max(1, job["remaining_time"])
                    if job["waiting_time_ratio"] > starvation_threshold and job["starving_time"] is None:
                        job["starving_time"] = t

        # Separate starving / non-starving
        starving = [job for job in q if job["waiting_time_ratio"] > starvation_threshold]

        # Choose job
        selected = None
        if starving:
            picked = select_starving_job_optimized(starving)
            # locate the exact dict in q
            sel_idx = None
            for idx, job in enumerate(q):
                if job is picked or (job.get("starving_time") == picked.get("starving_time") and
                                     job.get("waiting_time_ratio") == picked.get("waiting_time_ratio") and
                                     job.get("job_index") == picked.get("job_index")):
                    sel_idx = idx; break
            if sel_idx is None:
                # fallback: compute by key
                sel_idx = min(range(len(q)),
                              key=lambda k: (
                                  0 if q[k] in starving else 1,
                                  q[k].get("starving_time", float("inf")),
                                  -float(q[k].get("waiting_time_ratio", 0.0)),
                                  q[k].get("job_index", 0)))
            selected = q.pop(sel_idx)
        elif q:
            # SRPT selection among waiting jobs
            picked = srpt_select_next_job([
                {"remaining_time": j["remaining_time"], "arrival_time": j["arrival_time"], "job_index": j["job_index"]}
                for j in q
            ])
            sel_idx = min(range(len(q)),
                          key=lambda k: (q[k]["remaining_time"], q[k]["arrival_time"], q[k]["job_index"]))
            for k, j in enumerate(q):
                if (j["remaining_time"], j["arrival_time"], j["job_index"]) == \
                   (picked["remaining_time"], picked["arrival_time"], picked["job_index"]):
                    sel_idx = k; break
            selected = q.pop(sel_idx)

        # If nothing to run, jump to next arrival
        if selected is None:
            if i < total_jobs:
                t = max(t, norm[i]["arrival_time"])
                continue
            else:
                break

        # Start time record
        if selected["start_time"] is None:
            selected["start_time"] = t

        # Compute next arrival time
        next_arrival_t = norm[i]["arrival_time"] if i < total_jobs else None

        if next_arrival_t is None:
            # No more arrivals: run to completion
            t += selected["remaining_time"]
            selected["completion_time"] = t
            selected["remaining_time"] = 0
            completed.append(selected)
        else:
            # Run until either next arrival or completion
            delta = min(selected["remaining_time"], max(1, next_arrival_t - t))
            t += delta
            selected["remaining_time"] -= delta
            if selected["remaining_time"] == 0:
                selected["completion_time"] = t
                completed.append(selected)
            else:
                # Put back to queue for reconsideration at new time
                q.append(selected)

    # Metrics
    flows = [c["completion_time"] - c["arrival_time"] for c in completed]
    n = len(flows)
    if n == 0:
        return 0.0, 0.0
    avg_flow = sum(flows) / n
    l2 = (sum(f * f for f in flows)) ** 0.5
    return avg_flow, l2
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
    """Extract frequency value from folder name like freq_2"""
    pattern = r'freq_(\d+)(?:_\d+)?'
    match = re.search(pattern, folder_name)
    if match:
        return int(match.group(1))
    return None
def run(jobs):
    #Create a deep copy to ensure each mode gets fresh job data
    jobs_copy = copy.deepcopy(jobs)
    _, l2_norm_flow_time = Bal(jobs_copy)
    logger.info(f"BAL: L2 norm = {l2_norm_flow_time:.4f}")
    
    return l2_norm_flow_time

def process_avg_folders(data_dir, output_dir):
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
                
                # Run BAL
                _results = run(jobs)
                
                # Store results
                if arrival_rate not in results_by_arrival_rate:
                    results_by_arrival_rate[arrival_rate] = []
                
                results_by_arrival_rate[arrival_rate].append({
                    'bp_parameter_L': bp_L,
                    'bp_parameter_H': bp_H,
                    'results': _results
                })
            
            # Write results grouped by arrival_rate with version number
            for arrival_rate, results in results_by_arrival_rate.items():
                if version:
                    output_file = os.path.join(avg_result_dir, f"{int(arrival_rate)}_BAL_result_{version}.csv")
                else:
                    output_file = os.path.join(avg_result_dir, f"{int(arrival_rate)}_BAL_result.csv")
                
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    header = ['arrival_rate', 'bp_parameter_L', 'bp_parameter_H']
                    writer.writerow(header)
                    
                    # Sort results by bp_L and bp_H for consistency
                    results.sort(key=lambda x: (x['bp_parameter_L'], x['bp_parameter_H']))
                    
                    # Write data rows
                    for result in results:
                        row = [arrival_rate, result['bp_parameter_L'], result['bp_parameter_H']]
                        value = result['results']
                        row.append(value if value is not None else '')
                        writer.writerow(row)
                
                logger.info(f"  Saved results for arrival_rate={arrival_rate} to {output_file}")

def process_random_folders(data_dir, output_dir):
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
            
            # Run BAL
            _results = run(jobs)
            
            # Group results by version
            if version not in results_by_version:
                results_by_version[version] = []
            
            results_by_version[version].append({
                'frequency': frequency,
                'results': _results
            })
    
    # Write results grouped by version
    for version, results in results_by_version.items():
        if results:
            if version:
                output_file = os.path.join(random_result_dir, f"random_result_BAL_{version}.csv")
            else:
                output_file = os.path.join(random_result_dir, f"random_result_BAL.csv")
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Create header - FIXED format
                header = ['frequency']
                writer.writerow(header)
                
                # Sort by frequency
                results.sort(key=lambda x: x['frequency'])
                
                # Write data rows
                for result in results:
                    row = [result['frequency']]
                    value = result['results']
                    row.append(value if value is not None else '')
                    writer.writerow(row)
            
            logger.info(f"  Saved random results (version {version}) to {output_file}")

def process_softrandom_folders(data_dir, output_dir):
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
                
                # Run BAL
                _results = run(jobs)
                
                # Group results by version
                if base_version not in results_by_version:
                    results_by_version[base_version] = []
                
                results_by_version[base_version].append({
                    'frequency': frequency,
                    'results':_results
                })
    
    # Write results grouped by version
    for version, results in results_by_version.items():
        if results:
            if version:
                output_file = os.path.join(softrandom_result_dir, f"softrandom_result_BAL_{version}.csv")
            else:
                output_file = os.path.join(softrandom_result_dir, f"softrandom_result_BAL.csv")
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Create header - FIXED format
                header = ['frequency']
                writer.writerow(header)
                
                # Sort by frequency
                results.sort(key=lambda x: x['frequency'])
                
                # Write data rows
                for result in results:
                    row = [result['frequency']]
                    value = result['results']
                    row.append(value if value is not None else '')
                    writer.writerow(row)
            
            logger.info(f"  Saved softrandom results (version {version}) to {output_file}")

def main():
    """Main function to process all data"""
    
    # Configuration
    data_dir = 'data'  # Base directory containing avg_30, freq_*, and softrandom folders
    output_dir = 'BAL_result'  # Output directory for results
    
    logger.info("="*60)
    logger.info(f"Starting BAL batch processing:")
    logger.info(f"  Data directory: {data_dir}")
    logger.info(f"  Output directory: {output_dir}")
    logger.info("="*60)
    
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process avg30 files
    logger.info("\n" + "="*40)
    logger.info("Processing avg_30 files...")
    logger.info("="*40)
    process_avg_folders(data_dir, output_dir)
    
    # Process random files
    logger.info("\n" + "="*40)
    logger.info("Processing random files...")
    logger.info("="*40)
    process_random_folders(data_dir, output_dir)
    
    # Process softrandom files
    logger.info("\n" + "="*40)
    logger.info("Processing softrandom files...")
    logger.info("="*40)
    process_softrandom_folders(data_dir, output_dir)
    
    logger.info("\n" + "="*60)
    logger.info("BAL batch processing completed successfully!")
    logger.info("="*60)

if __name__ == "__main__":
    main()