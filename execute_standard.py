import multiprocessing
import Read_csv
import RR, SRPT, SETF, FCFS, Dynamic, BAL, SJF
import time
import pandas as pd
import numpy as np
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures import TimeoutError
import logging
from itertools import product
import pickle

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_jobs(jobs, include_index=False, as_list=False):
    """Convert jobs to appropriate format"""
    if not jobs:
        return []
    
    if isinstance(jobs[0], (list, tuple)):
        if as_list:
            return [[float(job[0]), float(job[1])] for job in jobs]
        return [{'arrival_time': float(job[0]), 
                'job_size': float(job[1]), 
                'job_index': i} for i, job in enumerate(jobs)] if include_index else [
                {'arrival_time': float(job[0]), 
                 'job_size': float(job[1])} for job in jobs]
    return jobs

def create_job_reference(job_list):
    """Create a lightweight reference to job_list to avoid copying"""
    # Serialize once and share the serialized data
    return pickle.dumps(job_list)

def get_job_list(job_ref):
    """Deserialize the job list when needed"""
    return pickle.loads(job_ref)

def run_algorithm_with_ref(algo, job_ref, needs_index, as_list, **kwargs):
    """Run a single algorithm with job reference"""
    jobs = get_job_list(job_ref)
    if not jobs:
        return None, None
    try:
        converted_jobs = convert_jobs(jobs, include_index=needs_index, as_list=as_list)
        _, l2n = algo(converted_jobs, **kwargs)
        
        # Create unique key for algorithms with parameters
        if kwargs:
            algo_key = f"{algo.__name__}"
            if 'mode' in kwargs:
                algo_key += f"_mode{kwargs['mode']}"
            if 'nJobsPerRound' in kwargs:
                algo_key += f"_njobs{kwargs['nJobsPerRound']}"
        else:
            algo_key = algo.__name__
            
        return algo_key, l2n
    except Exception as e:
        logger.error(f"Error running algorithm {algo.__name__}: {str(e)}")
        return None, None

def calculate_optimal_workers(num_tasks):
    """Calculate optimal number of workers based on CPU count and task count"""
    cpu_count = multiprocessing.cpu_count()
    # Leave 1-2 CPUs for system/IO, but use at least 1
    optimal = min(num_tasks, max(cpu_count - 2, 1), 32)  # Cap at 32 to avoid overhead
    return max(optimal, 1)

def run_all_algorithms_parallel_optimized(job_list, base_algorithms, dynamic_configs=None):
    """
    Run all algorithms in parallel - optimized version with better memory management
    """
    if not job_list:
        return None
    
    results = {}
    
    # Create a single serialized reference to the job list
    job_ref = create_job_reference(job_list)
    
    # Create all algorithm configurations using list comprehension (no loops)
    all_tasks = [
        (algo, job_ref, needs_idx, as_list, kwargs)
        for algo, _, needs_idx, as_list, kwargs in base_algorithms
    ]
    
    if dynamic_configs:
        all_tasks.extend([
            (algo, job_ref, needs_idx, as_list, kwargs)
            for algo, _, needs_idx, as_list, kwargs in dynamic_configs
        ])
    
    # Calculate optimal workers
    max_workers = calculate_optimal_workers(len(all_tasks))
    logger.debug(f"Using {max_workers} workers for {len(all_tasks)} tasks")
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks at once using list comprehension
        futures = [
            executor.submit(run_algorithm_with_ref, algo, job_ref, needs_idx, as_list, **kwargs)
            for algo, job_ref, needs_idx, as_list, kwargs in all_tasks
        ]
        
        # Collect results as they complete
        try:
            for future in as_completed(futures, timeout=300000):
                algo_name, l2n = future.result(timeout=12000)
                if algo_name and l2n is not None:
                    results[algo_name] = l2n
        except (TimeoutError, Exception) as e:
            logger.error(f"Error in parallel execution: {str(e)}")
            return None
    
    # Verify results
    if len(results) != len(all_tasks):
        logger.warning(f"Expected {len(all_tasks)} results but got {len(results)}")
        if len(results) == 0:
            return None
    
    return results

def execute_phase1(Arrival_rate, bp_parameter):
    """Execute phase 1 for normal data with fully parallel processing"""
    avg_statuses = ["avg_30", "avg_60", "avg_90"]
    
    for avg_status in avg_statuses:
        results = []
        for i in bp_parameter:
            try:
                # File path
                file_path = f'data/{avg_status}/({Arrival_rate}, {i["L"]}).csv'
                
                # Read job list
                job_list = Read_csv.Read_csv(file_path)
                if not job_list:
                    logger.warning(f"No data found in {file_path}")
                    continue

                # Define algorithm parameters using list comprehension (no loops!)
                modes = [1, 2, 3, 4, 5, 6]
                njobs_per_round = [100]
                
                # Create all configurations at once using list comprehension
                base_algorithms = [
                    (RR.RR, job_list, False, True, {}),
                    (SRPT.Srpt, job_list, False, False, {}),
                    (SETF.Setf, job_list, False, True, {}),
                    (FCFS.Fcfs, job_list, False, False, {}),
                    (BAL.Bal, job_list, False, False, {}),
                    (SJF.Sjf, job_list, False, True, {})
                ]
                
                # Use product to create all combinations without explicit loops
                dynamic_params = list(product(modes, njobs_per_round))
                dynamic_configs = [
                    (Dynamic.DYNAMIC, job_list, False, False, 
                     {'nJobsPerRound': njobs, 'mode': mode, 'input_file_name': file_path})
                    for mode, njobs in dynamic_params
                ]
                
                # Run everything in parallel
                all_results = run_all_algorithms_parallel_optimized(
                    job_list, base_algorithms, dynamic_configs
                )
                
                if not all_results:
                    logger.error(f"Failed to get results for {file_path}")
                    continue
                
                # Create result dictionary
                result_entry = {
                    "arrival_rate": Arrival_rate,
                    "bp_parameter_L": i["L"],
                    "bp_parameter_H": i["H"]
                }
                result_entry.update(all_results)
                results.append(result_entry)
                
                logger.info(f"Processed {file_path}: {len(all_results)} algorithms completed")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")
                continue

        # Save results
        if results:
            os.makedirs('phase1', exist_ok=True)
            df = pd.DataFrame(results)
            csv_filename = f'phase1/phase1_results_{avg_status}_{Arrival_rate}.csv'
            df.to_csv(csv_filename, index=False)
            logger.info(f"Saved {len(results)} results to {csv_filename}")

def execute_phase1_random(freq_folders):
    """Execute phase 1 for frequency-based random data with fully parallel processing"""
    all_results = []
    
    for freq_folder in freq_folders:
        logger.info(f"Processing random {freq_folder}...")
        
        try:
            file_path = f'data/{freq_folder}/random_{freq_folder}.csv'
            
            # Read job list
            job_list = Read_csv.Read_csv(file_path)
            if not job_list:
                logger.warning(f"No data found for {file_path}")
                continue
            
            # Create all configurations using list comprehensions
            modes = [1, 2, 3, 4, 5, 6]
            njobs_per_round = [100]
            
            base_algorithms = [
                (RR.RR, job_list, False, True, {}),
                (SRPT.Srpt, job_list, False, False, {}),
                (SETF.Setf, job_list, False, True, {}),
                (FCFS.Fcfs, job_list, False, False, {}),
                (BAL.Bal, job_list, False, False, {}),
                (SJF.Sjf, job_list, False, True, {})
            ]
            
            # Use product for creating all combinations
            dynamic_params = list(product(modes, njobs_per_round))
            dynamic_configs = [
                (Dynamic.DYNAMIC, job_list, False, False, 
                 {'nJobsPerRound': njobs, 'mode': mode, 'input_file_name': file_path})
                for mode, njobs in dynamic_params
            ]
            
            # Run everything in parallel
            freq_results = run_all_algorithms_parallel_optimized(
                job_list, base_algorithms, dynamic_configs
            )
            
            if not freq_results:
                logger.error(f"Failed to get results for {file_path}")
                continue
            
            # Create result entry
            result_entry = {"frequency": freq_folder}
            result_entry.update(freq_results)
            all_results.append(result_entry)
            
            logger.info(f"Successfully processed random {freq_folder}: {len(freq_results)} algorithms")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            continue
    
    # Save merged results
    if all_results:
        os.makedirs('result', exist_ok=True)
        df = pd.DataFrame(all_results)
        csv_filename = 'result/random_result.csv'
        df.to_csv(csv_filename, index=False)
        logger.info(f"Saved merged random results to {csv_filename} with {len(all_results)} frequency configurations")

def execute_phase1_softrandom(freq_folders):
    """Execute phase 1 for softrandom frequency-based data with fully parallel processing"""
    all_results = []
    
    for freq_folder in freq_folders:
        logger.info(f"Processing softrandom {freq_folder}...")
        
        try:
            file_path = f'data/softrandom/{freq_folder}/softrandom_{freq_folder}.csv'
            
            # Read job list
            job_list = Read_csv.Read_csv(file_path)
            if not job_list:
                logger.warning(f"No data found for {file_path}")
                continue
            
            # Create all configurations using list comprehensions
            modes = [1, 2, 3, 4, 5, 6]
            njobs_per_round = [100]
            
            base_algorithms = [
                (RR.RR, job_list, False, True, {}),
                (SRPT.Srpt, job_list, False, False, {}),
                (SETF.Setf, job_list, False, True, {}),
                (FCFS.Fcfs, job_list, False, False, {}),
                (BAL.Bal, job_list, False, False, {}),
                (SJF.Sjf, job_list, False, True, {})
            ]
            
            # Use product for creating all combinations
            dynamic_params = list(product(modes, njobs_per_round))
            dynamic_configs = [
                (Dynamic.DYNAMIC, job_list, False, False, 
                 {'nJobsPerRound': njobs, 'mode': mode, 'input_file_name': file_path})
                for mode, njobs in dynamic_params
            ]
            
            # Run everything in parallel
            freq_results = run_all_algorithms_parallel_optimized(
                job_list, base_algorithms, dynamic_configs
            )
            
            if not freq_results:
                logger.error(f"Failed to get results for {file_path}")
                continue
            
            # Create result entry
            result_entry = {"frequency": freq_folder}
            result_entry.update(freq_results)
            all_results.append(result_entry)
            
            logger.info(f"Successfully processed softrandom {freq_folder}: {len(freq_results)} algorithms")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            continue
    
    # Save merged results
    if all_results:
        os.makedirs('result', exist_ok=True)
        df = pd.DataFrame(all_results)
        csv_filename = 'result/softrandom_result.csv'
        df.to_csv(csv_filename, index=False)
        logger.info(f"Saved merged softrandom results to {csv_filename} with {len(all_results)} frequency configurations")

# Keep the verify_results function as is
def verify_results(csv_file):
    """Verify the correctness of results in a CSV file"""
    try:
        df = pd.read_csv(csv_file)
        logger.info(f"\nVerifying {csv_file}:")
        logger.info(f"  - Total rows: {len(df)}")
        logger.info(f"  - Total columns: {len(df.columns)}")
        
        # Check for expected columns
        expected_base = ['RR', 'Srpt', 'Setf', 'Fcfs', 'Bal', 'Sjf']
        expected_dynamic = [f'DYNAMIC_mode{i}_njobs100' for i in range(1, 7)]
        
        missing_base = [col for col in expected_base if col not in df.columns]
        missing_dynamic = [col for col in expected_dynamic if col not in df.columns]
        
        if missing_base:
            logger.warning(f"  - Missing base algorithms: {missing_base}")
        if missing_dynamic:
            logger.warning(f"  - Missing Dynamic configurations: {missing_dynamic}")
        
        # Check for NaN values
        nan_counts = df.isna().sum()
        if nan_counts.any():
            logger.warning(f"  - Columns with NaN values: {nan_counts[nan_counts > 0].to_dict()}")
        
        # Verify L2 norm values are positive
        for col in df.columns:
            if col in expected_base + expected_dynamic:
                if (df[col] < 0).any():
                    logger.error(f"  - Negative values found in {col}")
                else:
                    logger.info(f"  - {col}: min={df[col].min():.2f}, max={df[col].max():.2f}")
        
        return True
    except Exception as e:
        logger.error(f"Error verifying {csv_file}: {e}")
        return False