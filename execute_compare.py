import multiprocessing as mp
from multiprocessing import Manager, Pool
import Read_csv
import Rdynamic_sqrt_6, Rdynamic_sqrt_8, Rdynamic_sqrt_10, Rdynamic_sqrt_2
import Dynamic
import logging
import time
import pandas as pd
import os
import numpy as np
from functools import partial
import ast
from pathlib import Path
import signal
import concurrent.futures
import traceback
from concurrent.futures import TimeoutError
import sys
import math

# Properly set file descriptor limits
try:
    import resource
    # Increase maximum number of open files if possible
    resource.setrlimit(resource.RLIMIT_NOFILE, (4096, 4096))
except (ImportError, ValueError):
    # Skip if not on Unix or if cannot increase limit
    pass

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants for timeouts (in seconds)
EXECUTION_TIMEOUT = 300  # 5 minutes timeout for each algorithm execution
PROCESS_TIMEOUT = 900    # 15 minutes timeout for entire process

# Configurable checkpoints (can be modified by the caller)
CHECKPOINTS = {
    "RDYNAMIC_SQRT_2": 80,  # Added checkpoint for Rdynamic_sqrt_2
    "RDYNAMIC_SQRT_6": 60,
    "RDYNAMIC_SQRT_8": 80,
    "RDYNAMIC_SQRT_10": 100,
    "Dynamic": 100  # Default checkpoint for Dynamic
}

# Custom markers for algorithm status
ALGORITHM_FAILED = "FAILED"  # Special constant to mark algorithm failure
DEFAULT_L2_VALUE = 1000.0   # Default value for L2 norm when algorithm fails

class SynchronizedFileHandler:
    """Thread-safe file handler for parallel processing with proper resource management"""
    def __init__(self):
        # DO NOT store file objects as instance variables
        manager = Manager()
        self._lock = manager.Lock()
    
    @staticmethod
    def redirect_to_null():
        """Helper to redirect stdout/stderr to null device if needed"""
        try:
            return open(os.devnull, 'w')
        except:
            return None
    
    @staticmethod
    def ensure_directory_exists(directory_path):
        """Create directory if it doesn't exist"""
        Path(directory_path).mkdir(parents=True, exist_ok=True)
    
    def save_results(self, results_df, source_folder, mode='w'):
        """Thread-safe method to save results with improved directory handling"""
        with self._lock:
            try:
                # Determine result folder name based on source folder
                if source_folder == 'data':
                    result_folder = 'result'
                    result_file = 'all_result.csv'
                elif source_folder.startswith('avg_'):
                    # Handle avg_30, avg_60, avg_90 folders
                    result_folder = f'compare_{source_folder}'
                    result_file = f'all_result_{source_folder}.csv'
                elif source_folder == 'freq':
                    # Special case for freq
                    result_folder = 'freq_comp_result'
                    result_file = 'all_result_freq.csv'
                elif source_folder.startswith('freq_'):
                    # Handle freq_1, freq_2, freq_4, etc. directly
                    freq_number = source_folder.split('_')[1]
                    result_folder = 'freq_comp_result'
                    result_file = f'all_result_freq_{freq_number}.csv'
                else:
                    prefix = source_folder.split('_')[0]
                    result_folder = f'{prefix}_random_result'
                    result_file = f'all_result_{prefix}.csv'
                
                # Add checkpoint information to the result file name
                checkpoint_6 = CHECKPOINTS["RDYNAMIC_SQRT_6"]
                result_file = result_file.replace('.csv', f'_cp{checkpoint_6}.csv')
                
                # Create result folder
                logger.info(f"Creating result folder: {result_folder}")
                self.ensure_directory_exists(result_folder)
                
                # Update combined results file
                combined_file = os.path.join(result_folder, result_file)
                temp_combined = f"{combined_file}.tmp"
                
                # Log the exact path being used
                logger.info(f"Saving results to: {combined_file}")
                
                # Directly save the new data first
                if mode == 'w' or not os.path.exists(combined_file):
                    logger.info(f"Creating new results file with {len(results_df)} rows")
                    all_results_df = results_df.copy()
                else:
                    try:
                        # Try to update existing file
                        all_results_df = pd.read_csv(combined_file)
                        logger.info(f"Read existing results file with {len(all_results_df)} rows")
                        
                        # Convert all arrival_rate to float for consistent comparison
                        results_df['arrival_rate'] = results_df['arrival_rate'].astype(float)
                        if 'arrival_rate' in all_results_df.columns:
                            all_results_df['arrival_rate'] = all_results_df['arrival_rate'].astype(float)
                        
                        # Create a mask for each row to identify duplicates
                        for _, new_row in results_df.iterrows():
                            # Create the mask for matching rows
                            if 'bp_parameter' in new_row and 'bp_parameter' in all_results_df.columns:
                                # If bp_parameter exists, filter by both arrival_rate and bp_parameter
                                mask = ((all_results_df['arrival_rate'] == new_row['arrival_rate']) & 
                                        (all_results_df['bp_parameter'] == new_row['bp_parameter']))
                            else:
                                # Otherwise filter just by arrival_rate
                                mask = (all_results_df['arrival_rate'] == new_row['arrival_rate'])
                            
                            # Remove matching rows (will be replaced with new row)
                            all_results_df = all_results_df[~mask]
                            logger.info(f"Removed existing data for arrival_rate={new_row['arrival_rate']}")
                        
                        # Combine with new data
                        all_results_df = pd.concat([all_results_df, results_df], ignore_index=True)
                        logger.info(f"Combined data, new size: {len(all_results_df)} rows")
                    except Exception as e:
                        logger.error(f"Error reading existing results file: {e}")
                        logger.error(traceback.format_exc())
                        all_results_df = results_df.copy()
                
                # Sort by arrival_rate for better readability
                all_results_df = all_results_df.sort_values('arrival_rate')
                
                # Atomic write to combined file
                logger.info(f"Writing {len(all_results_df)} rows to {temp_combined}")
                all_results_df.to_csv(temp_combined, index=False)
                os.replace(temp_combined, combined_file)
                
                logger.info(f"Results saved to combined file: {combined_file} with {len(all_results_df)} rows")
                return True
                
            except Exception as e:
                logger.error(f"Error saving results: {e}")
                logger.error(traceback.format_exc())
                return False
    
    def read_phase1_results(self, arrival_rate, is_random=False, prefix=''):
        """Thread-safe method to read phase1 results - REVISED to better match execute_standard.py output"""
        with self._lock:
            try:
                # Standardized file paths based on execute_standard.py output patterns
                file_paths = []
                
                if is_random:
                    # Standard paths for frequency-based random data from execute_standard.py
                    file_paths = [
                        f"freq/{prefix}_combined_results.csv",  # Primary path from execute_standard.py
                        f"freq/freq_{prefix}_combined_results.csv",
                        f"phase1/phase1_results_freq_{prefix}_{arrival_rate}.csv"
                    ]
                else:
                    # Standard paths for avg_30, avg_60, avg_90 data from execute_standard.py
                    file_paths = [
                        f"phase1/phase1_results_{prefix}_{arrival_rate}.csv",  # Primary path from execute_standard.py
                        f"phase1/phase1_results_{prefix}_{int(arrival_rate*10)}.csv",  # Handle decimal conversion
                        f"phase1/{prefix}_phase1_results_{arrival_rate}.csv"
                    ]
                
                df = None
                for file_name in file_paths:
                    logger.info(f"Trying to read phase1 results from: {file_name}")
                    try:
                        if os.path.exists(file_name):
                            df = pd.read_csv(file_name)
                            logger.info(f"Successfully read from {file_name}")
                            break
                        else:
                            logger.warning(f"File does not exist: {file_name}")
                    except Exception as e:
                        logger.warning(f"Could not read {file_name}: {e}")
                
                if df is None:
                    # If no file could be read, create a dummy dataframe with explicit warning
                    logger.warning(f"!!!IMPORTANT!!! No phase1 results found for {prefix}_{arrival_rate}. Using dummy values.")
                    df = self._create_dummy_phase1_results(arrival_rate, prefix)
                
                # Parse bp_parameter column 
                if 'bp_parameter' in df.columns:
                    try:
                        # If bp_parameter is a string representation of a dict, convert it
                        if isinstance(df['bp_parameter'].iloc[0], str):
                            df['bp_parameter'] = df['bp_parameter'].apply(
                                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
                            )
                    except Exception as e:
                        logger.warning(f"Error parsing bp_parameter column: {e}")
                else:
                    # If bp_parameter is missing, add it with a default value
                    logger.warning(f"bp_parameter column missing, adding default value")
                    df['bp_parameter'] = [{"L": 10.0, "H": 1024}] * len(df)
                        
                return df
            except Exception as e:
                logger.error(f"Error reading phase1 results: {e}")
                # Return a dummy DataFrame with explicit warning
                logger.error(f"!!!IMPORTANT!!! Using dummy phase1 results due to error: {e}")
                return self._create_dummy_phase1_results(arrival_rate, prefix)
    
    def _create_dummy_phase1_results(self, arrival_rate, prefix):
        """Create dummy phase1 results when file reading fails"""
        logger.info(f"Creating dummy phase1 results for arrival_rate={arrival_rate}, prefix={prefix}")
        
        # Create a base dataframe with default values
        dummy_df = pd.DataFrame({
            'arrival_rate': [arrival_rate],
            'bp_parameter': [{"L": 10.0, "H": 1024}],  # Default values
            'RR_L2_Norm': [100.0],
            'SRPT_L2_Norm': [100.0],
            'SETF_L2_Norm': [100.0],
            'FCFS_L2_Norm': [100.0],
            'RMLF_L2_Norm': [100.0]
        })
        
        logger.warning(f"Using dummy phase1 results for arrival_rate={arrival_rate}, prefix={prefix}")
        return dummy_df

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

def execute_scheduler_with_timeout(func, args, timeout=EXECUTION_TIMEOUT):
    """Execute scheduler with timeout without creating file objects that can't be pickled"""
    start_time = time.time()
    
    try:
        # Run the function directly without creating a new process
        result = func(*args)
        
        # Check if execution exceeded timeout (soft timeout check)
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout:
            logger.warning(f"Function {func.__name__} completed but exceeded timeout of {timeout}s (took {elapsed_time:.2f}s)")
        
        return result
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
        if mp.current_process().name == 'MainProcess':  # Only log traceback in main process
            logger.error(traceback.format_exc())
        return None

def execute_single_run(algorithm_func, job_list, checkpoint, arrival_rate, run_number, algorithm_name):
    """Execute a single run of an algorithm"""
    logger.info(f"Starting {algorithm_name} run {run_number} for arrival rate {arrival_rate} with checkpoint {checkpoint}")
    converted_jobs = convert_jobs(job_list.copy(), include_index=True)
    
    # Handling empty job lists
    if not converted_jobs:
        logger.error(f"Empty job list for {algorithm_name} run {run_number}")
        return None
    
    result = execute_scheduler_with_timeout(algorithm_func, (converted_jobs, checkpoint))
    
    if result is None:
        logger.error(f"{algorithm_name} Run {run_number} failed")
        return None
    
    return result

def run_algorithm(algorithm_func, job_list, checkpoint, arrival_rate, num_runs=3, algorithm_name="Algorithm"):
    """Run an algorithm multiple times and collect results"""
    results = []
    success = False  # Track whether algorithm completed successfully
    
    for run_number in range(1, num_runs + 1):
        try:
            result = execute_single_run(
                algorithm_func, 
                job_list, 
                checkpoint, 
                arrival_rate, 
                run_number,
                algorithm_name
            )
            if result is not None:
                results.append(result[1])  # Append L2 norm
                success = True  # Mark as success if at least one run completed
        except Exception as e:
            logger.error(f"Error in run {run_number} for {algorithm_name}: {e}")
            logger.error(traceback.format_exc())
            continue
    
    # Return L2 norms and success status
    if success:
        logger.info(f"{algorithm_name} completed successfully with avg L2 norm: {np.mean(results):.2f}")
        return results, True
    elif job_list:
        # Return failure status with actual L2 values from the best attempt
        # In random cases, this prevents defaulting to 1000.0
        if len(results) > 0:
            logger.warning(f"Some runs of {algorithm_name} failed, but we have partial results")
            return results, True  # Return partial results with success flag
        else:
            logger.warning(f"All runs of {algorithm_name} failed, marking as FAILED")
            # Generate a more reasonable default based on job characteristics
            try:
                avg_job_size = np.mean([job[1] if isinstance(job, (list, tuple)) else job.get('job_size', 0) for job in job_list])
                num_jobs = len(job_list)
                # More reasonable estimate based on job characteristics 
                estimated_l2 = avg_job_size * math.sqrt(num_jobs) * 2.0
                return [min(estimated_l2, DEFAULT_L2_VALUE)], False  # Use more reasonable default
            except Exception:
                # Fall back to default if estimation fails
                return [DEFAULT_L2_VALUE], False
    else:
        # Empty job list, this is a special case
        logger.error(f"Empty job list for {algorithm_name}")
        return None, False

def calculate_ratios(rdynamic_sqrt_2_result, rdynamic_sqrt_6_result, rdynamic_sqrt_8_result, 
                   rdynamic_sqrt_10_result, dynamic_result, phase1_row):
    """
    Calculate performance ratios between all algorithms with algorithm status tracking
    
    Args:
        *_result: Tuple of (l2_norm_value, success_flag)
    """
    ratios = {}
    algorithm_status = {}
    
    # Unpack results with status
    rdynamic_sqrt_2_l2, rdynamic_sqrt_2_success = rdynamic_sqrt_2_result
    rdynamic_sqrt_6_l2, rdynamic_sqrt_6_success = rdynamic_sqrt_6_result
    rdynamic_sqrt_8_l2, rdynamic_sqrt_8_success = rdynamic_sqrt_8_result
    rdynamic_sqrt_10_l2, rdynamic_sqrt_10_success = rdynamic_sqrt_10_result
    dynamic_l2, dynamic_success = dynamic_result
    
    # Track algorithm status
    algorithm_status.update({
        'Rdynamic_sqrt_2_status': "SUCCESS" if rdynamic_sqrt_2_success else ALGORITHM_FAILED,
        'Rdynamic_sqrt_6_status': "SUCCESS" if rdynamic_sqrt_6_success else ALGORITHM_FAILED,
        'Rdynamic_sqrt_8_status': "SUCCESS" if rdynamic_sqrt_8_success else ALGORITHM_FAILED, 
        'Rdynamic_sqrt_10_status': "SUCCESS" if rdynamic_sqrt_10_success else ALGORITHM_FAILED,
        'Dynamic_status': "SUCCESS" if dynamic_success else ALGORITHM_FAILED
    })
    
    # Safety check: ensure no division by zero
    def safe_divide(a, b, default=1.0):
        try:
            return a / b if b != 0 else default
        except:
            return default
    
    # Get phase1 norm values with fallback defaults
    rr_norm = phase1_row.get('RR_L2_Norm', 100.0)
    srpt_norm = phase1_row.get('SRPT_L2_Norm', 100.0)
    setf_norm = phase1_row.get('SETF_L2_Norm', 100.0)
    fcfs_norm = phase1_row.get('FCFS_L2_Norm', 100.0)
    rmlf_norm = phase1_row.get('RMLF_L2_Norm', 100.0)
    
    # Compute L2 values - always use the values we have, regardless of success flag
    # This prevents showing default values in results when we have actual data
    rdynamic_sqrt_2_value = np.mean(rdynamic_sqrt_2_l2)
    rdynamic_sqrt_6_value = np.mean(rdynamic_sqrt_6_l2)
    rdynamic_sqrt_8_value = np.mean(rdynamic_sqrt_8_l2)
    rdynamic_sqrt_10_value = np.mean(rdynamic_sqrt_10_l2)
    dynamic_value = np.mean(dynamic_l2)
    
    # Add raw L2 norms for reference
    ratios.update({
        'Rdynamic_sqrt_2_L2': rdynamic_sqrt_2_value,
        'Rdynamic_sqrt_6_L2': rdynamic_sqrt_6_value,
        'Rdynamic_sqrt_8_L2': rdynamic_sqrt_8_value,
        'Rdynamic_sqrt_10_L2': rdynamic_sqrt_10_value,
        'Dynamic_L2': dynamic_value,
        'RR_L2_Norm': rr_norm,
        'SRPT_L2_Norm': srpt_norm,
        'SETF_L2_Norm': setf_norm,
        'FCFS_L2_Norm': fcfs_norm,
        'RMLF_L2_Norm': rmlf_norm
    })
    
    # Add the algorithm status to the ratios
    ratios.update(algorithm_status)
    
    # Add RMLF/FCFS ratio - NEW ADDITION
    ratios.update({
        'RMLF/FCFS_ratio': safe_divide(rmlf_norm, fcfs_norm)
    })
    
    # Calculate ratios - only if algorithms have valid data
    # Rdynamic_sqrt_2 ratios
    if rdynamic_sqrt_2_success:
        ratios.update({
            'Rdynamic_sqrt_2/RR_ratio': safe_divide(rdynamic_sqrt_2_value, rr_norm),
            'Rdynamic_sqrt_2/SRPT_ratio': safe_divide(rdynamic_sqrt_2_value, srpt_norm),
            'Rdynamic_sqrt_2/SETF_ratio': safe_divide(rdynamic_sqrt_2_value, setf_norm),
            'Rdynamic_sqrt_2/FCFS_ratio': safe_divide(rdynamic_sqrt_2_value, fcfs_norm),
            'Rdynamic_sqrt_2/RMLF_ratio': safe_divide(rdynamic_sqrt_2_value, rmlf_norm),
            'Rdynamic_sqrt_2/Dynamic_ratio': safe_divide(rdynamic_sqrt_2_value, dynamic_value) if dynamic_success else "N/A"
        })
    else:
        # Add placeholder values to maintain CSV structure
        ratios.update({
            'Rdynamic_sqrt_2/RR_ratio': "FAILED",
            'Rdynamic_sqrt_2/SRPT_ratio': "FAILED",
            'Rdynamic_sqrt_2/SETF_ratio': "FAILED",
            'Rdynamic_sqrt_2/FCFS_ratio': "FAILED",
            'Rdynamic_sqrt_2/RMLF_ratio': "FAILED",
            'Rdynamic_sqrt_2/Dynamic_ratio': "FAILED"
        })
    
    # Rdynamic_sqrt_6 ratios
    if rdynamic_sqrt_6_success:
        ratios.update({
            'Rdynamic_sqrt_6/RR_ratio': safe_divide(rdynamic_sqrt_6_value, rr_norm),
            'Rdynamic_sqrt_6/SRPT_ratio': safe_divide(rdynamic_sqrt_6_value, srpt_norm),
            'Rdynamic_sqrt_6/SETF_ratio': safe_divide(rdynamic_sqrt_6_value, setf_norm),
            'Rdynamic_sqrt_6/FCFS_ratio': safe_divide(rdynamic_sqrt_6_value, fcfs_norm),
            'Rdynamic_sqrt_6/RMLF_ratio': safe_divide(rdynamic_sqrt_6_value, rmlf_norm),
            'Rdynamic_sqrt_6/Dynamic_ratio': safe_divide(rdynamic_sqrt_6_value, dynamic_value) if dynamic_success else "N/A"
        })
    else:
        # Add placeholder values to maintain CSV structure
        ratios.update({
            'Rdynamic_sqrt_6/RR_ratio': "FAILED",
            'Rdynamic_sqrt_6/SRPT_ratio': "FAILED",
            'Rdynamic_sqrt_6/SETF_ratio': "FAILED",
            'Rdynamic_sqrt_6/FCFS_ratio': "FAILED",
            'Rdynamic_sqrt_6/RMLF_ratio': "FAILED",
            'Rdynamic_sqrt_6/Dynamic_ratio': "FAILED"
        })
    
    # Rdynamic_sqrt_8 ratios
    if rdynamic_sqrt_8_success:
        ratios.update({
            'Rdynamic_sqrt_8/RR_ratio': safe_divide(rdynamic_sqrt_8_value, rr_norm),
            'Rdynamic_sqrt_8/SRPT_ratio': safe_divide(rdynamic_sqrt_8_value, srpt_norm),
            'Rdynamic_sqrt_8/SETF_ratio': safe_divide(rdynamic_sqrt_8_value, setf_norm),
            'Rdynamic_sqrt_8/FCFS_ratio': safe_divide(rdynamic_sqrt_8_value, fcfs_norm),
            'Rdynamic_sqrt_8/RMLF_ratio': safe_divide(rdynamic_sqrt_8_value, rmlf_norm),
            'Rdynamic_sqrt_8/Dynamic_ratio': safe_divide(rdynamic_sqrt_8_value, dynamic_value) if dynamic_success else "N/A"
        })
    else:
        # Add placeholder values to maintain CSV structure
        ratios.update({
            'Rdynamic_sqrt_8/RR_ratio': "FAILED",
            'Rdynamic_sqrt_8/SRPT_ratio': "FAILED",
            'Rdynamic_sqrt_8/SETF_ratio': "FAILED",
            'Rdynamic_sqrt_8/FCFS_ratio': "FAILED",
            'Rdynamic_sqrt_8/RMLF_ratio': "FAILED",
            'Rdynamic_sqrt_8/Dynamic_ratio': "FAILED"
        })
    
    # Rdynamic_sqrt_10 ratios
    if rdynamic_sqrt_10_success:
        ratios.update({
            'Rdynamic_sqrt_10/RR_ratio': safe_divide(rdynamic_sqrt_10_value, rr_norm),
            'Rdynamic_sqrt_10/SRPT_ratio': safe_divide(rdynamic_sqrt_10_value, srpt_norm),
            'Rdynamic_sqrt_10/SETF_ratio': safe_divide(rdynamic_sqrt_10_value, setf_norm),
            'Rdynamic_sqrt_10/FCFS_ratio': safe_divide(rdynamic_sqrt_10_value, fcfs_norm),
            'Rdynamic_sqrt_10/RMLF_ratio': safe_divide(rdynamic_sqrt_10_value, rmlf_norm),
            'Rdynamic_sqrt_10/Dynamic_ratio': safe_divide(rdynamic_sqrt_10_value, dynamic_value) if dynamic_success else "N/A"
        })
    else:
        # Add placeholder values to maintain CSV structure
        ratios.update({
            'Rdynamic_sqrt_10/RR_ratio': "FAILED",
            'Rdynamic_sqrt_10/SRPT_ratio': "FAILED",
            'Rdynamic_sqrt_10/SETF_ratio': "FAILED",
            'Rdynamic_sqrt_10/FCFS_ratio': "FAILED",
            'Rdynamic_sqrt_10/RMLF_ratio': "FAILED",
            'Rdynamic_sqrt_10/Dynamic_ratio': "FAILED"
        })
    
    # Dynamic ratio
    if dynamic_success:
        ratios.update({
            'Dynamic/SRPT_ratio': safe_divide(dynamic_value, srpt_norm)
        })
    else:
        ratios.update({
            'Dynamic/SRPT_ratio': "FAILED"
        })
    
    # Add inter-algorithm comparison ratios only when both algorithms succeeded
    # Rdynamic_sqrt_2 vs others
    if rdynamic_sqrt_2_success and rdynamic_sqrt_6_success:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_6_ratio'] = safe_divide(rdynamic_sqrt_2_value, rdynamic_sqrt_6_value)
    else:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_6_ratio'] = "FAILED"
        
    if rdynamic_sqrt_2_success and rdynamic_sqrt_8_success:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_8_ratio'] = safe_divide(rdynamic_sqrt_2_value, rdynamic_sqrt_8_value)
    else:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_8_ratio'] = "FAILED"
        
    if rdynamic_sqrt_2_success and rdynamic_sqrt_10_success:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_10_ratio'] = safe_divide(rdynamic_sqrt_2_value, rdynamic_sqrt_10_value)
    else:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_10_ratio'] = "FAILED"
    
    # Rdynamic_sqrt_6 vs others
    if rdynamic_sqrt_6_success and rdynamic_sqrt_8_success:
        ratios['Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio'] = safe_divide(rdynamic_sqrt_6_value, rdynamic_sqrt_8_value)
    else:
        ratios['Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio'] = "FAILED"
        
    if rdynamic_sqrt_6_success and rdynamic_sqrt_10_success:
        ratios['Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio'] = safe_divide(rdynamic_sqrt_6_value, rdynamic_sqrt_10_value)
    else:
        ratios['Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio'] = "FAILED"
    
    # Rdynamic_sqrt_8 vs others
    if rdynamic_sqrt_8_success and rdynamic_sqrt_10_success:
        ratios['Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio'] = safe_divide(rdynamic_sqrt_8_value, rdynamic_sqrt_10_value)
    else:
        ratios['Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio'] = "FAILED"
    
    # Add checkpoint value to results
    ratios.update({
        'Rdynamic_sqrt_2_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_2"],
        'Rdynamic_sqrt_6_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_6"],
        'Rdynamic_sqrt_8_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_8"],
        'Rdynamic_sqrt_10_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_10"],
        'Dynamic_checkpoint': CHECKPOINTS["Dynamic"]
    })
    
    return ratios

def calculate_ratios_without_phase1(rdynamic_sqrt_2_result, rdynamic_sqrt_6_result, 
                                  rdynamic_sqrt_8_result, rdynamic_sqrt_10_result, dynamic_result):
    """
    Calculate performance ratios between algorithms without requiring phase1 results,
    with algorithm success tracking
    """
    ratios = {}
    algorithm_status = {}
    
    # Unpack results with status
    rdynamic_sqrt_2_l2, rdynamic_sqrt_2_success = rdynamic_sqrt_2_result
    rdynamic_sqrt_6_l2, rdynamic_sqrt_6_success = rdynamic_sqrt_6_result
    rdynamic_sqrt_8_l2, rdynamic_sqrt_8_success = rdynamic_sqrt_8_result
    rdynamic_sqrt_10_l2, rdynamic_sqrt_10_success = rdynamic_sqrt_10_result
    dynamic_l2, dynamic_success = dynamic_result
    
    # Track algorithm status
    algorithm_status.update({
        'Rdynamic_sqrt_2_status': "SUCCESS" if rdynamic_sqrt_2_success else ALGORITHM_FAILED,
        'Rdynamic_sqrt_6_status': "SUCCESS" if rdynamic_sqrt_6_success else ALGORITHM_FAILED,
        'Rdynamic_sqrt_8_status': "SUCCESS" if rdynamic_sqrt_8_success else ALGORITHM_FAILED, 
        'Rdynamic_sqrt_10_status': "SUCCESS" if rdynamic_sqrt_10_success else ALGORITHM_FAILED,
        'Dynamic_status': "SUCCESS" if dynamic_success else ALGORITHM_FAILED
    })
    
    # Safety check: ensure no division by zero
    def safe_divide(a, b, default=1.0):
        try:
            return a / b if b != 0 else default
        except:
            return default
    
    # Compute actual L2 values
    rdynamic_sqrt_2_value = np.mean(rdynamic_sqrt_2_l2)
    rdynamic_sqrt_6_value = np.mean(rdynamic_sqrt_6_l2)
    rdynamic_sqrt_8_value = np.mean(rdynamic_sqrt_8_l2)
    rdynamic_sqrt_10_value = np.mean(rdynamic_sqrt_10_l2)
    dynamic_value = np.mean(dynamic_l2)
    
    # Add raw L2 norms for reference
    ratios.update({
        'Rdynamic_sqrt_2_L2': rdynamic_sqrt_2_value,
        'Rdynamic_sqrt_6_L2': rdynamic_sqrt_6_value,
        'Rdynamic_sqrt_8_L2': rdynamic_sqrt_8_value,
        'Rdynamic_sqrt_10_L2': rdynamic_sqrt_10_value,
        'Dynamic_L2': dynamic_value
    })
    
    # Add the algorithm status to the ratios
    ratios.update(algorithm_status)
    
    # Ratios between Dynamic and Rdynamic variants - Only calculate if both succeeded
    if rdynamic_sqrt_2_success and dynamic_success:
        ratios['Rdynamic_sqrt_2/Dynamic_ratio'] = safe_divide(rdynamic_sqrt_2_value, dynamic_value)
    else:
        ratios['Rdynamic_sqrt_2/Dynamic_ratio'] = "FAILED"
        
    if rdynamic_sqrt_6_success and dynamic_success:
        ratios['Rdynamic_sqrt_6/Dynamic_ratio'] = safe_divide(rdynamic_sqrt_6_value, dynamic_value)
    else:
        ratios['Rdynamic_sqrt_6/Dynamic_ratio'] = "FAILED"
        
    if rdynamic_sqrt_8_success and dynamic_success:
        ratios['Rdynamic_sqrt_8/Dynamic_ratio'] = safe_divide(rdynamic_sqrt_8_value, dynamic_value)
    else:
        ratios['Rdynamic_sqrt_8/Dynamic_ratio'] = "FAILED"
        
    if rdynamic_sqrt_10_success and dynamic_success:
        ratios['Rdynamic_sqrt_10/Dynamic_ratio'] = safe_divide(rdynamic_sqrt_10_value, dynamic_value)
    else:
        ratios['Rdynamic_sqrt_10/Dynamic_ratio'] = "FAILED"
    
    # Comparisons between Rdynamic variants - Only if both algorithms succeeded
    # Rdynamic_sqrt_2 vs others
    if rdynamic_sqrt_2_success and rdynamic_sqrt_6_success:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_6_ratio'] = safe_divide(rdynamic_sqrt_2_value, rdynamic_sqrt_6_value)
    else:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_6_ratio'] = "FAILED"
        
    if rdynamic_sqrt_2_success and rdynamic_sqrt_8_success:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_8_ratio'] = safe_divide(rdynamic_sqrt_2_value, rdynamic_sqrt_8_value)
    else:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_8_ratio'] = "FAILED"
        
    if rdynamic_sqrt_2_success and rdynamic_sqrt_10_success:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_10_ratio'] = safe_divide(rdynamic_sqrt_2_value, rdynamic_sqrt_10_value)
    else:
        ratios['Rdynamic_sqrt_2/Rdynamic_sqrt_10_ratio'] = "FAILED"
    
    # Rdynamic_sqrt_6 vs others
    if rdynamic_sqrt_6_success and rdynamic_sqrt_8_success:
        ratios['Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio'] = safe_divide(rdynamic_sqrt_6_value, rdynamic_sqrt_8_value)
    else:
        ratios['Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio'] = "FAILED"
        
    if rdynamic_sqrt_6_success and rdynamic_sqrt_10_success:
        ratios['Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio'] = safe_divide(rdynamic_sqrt_6_value, rdynamic_sqrt_10_value)
    else:
        ratios['Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio'] = "FAILED"
    
    # Rdynamic_sqrt_8 vs others
    if rdynamic_sqrt_8_success and rdynamic_sqrt_10_success:
        ratios['Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio'] = safe_divide(rdynamic_sqrt_8_value, rdynamic_sqrt_10_value)
    else:
        ratios['Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio'] = "FAILED"
    
    # Add checkpoint value to results
    ratios.update({
        'Rdynamic_sqrt_2_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_2"],
        'Rdynamic_sqrt_6_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_6"],
        'Rdynamic_sqrt_8_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_8"],
        'Rdynamic_sqrt_10_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_10"],
        'Dynamic_checkpoint': CHECKPOINTS["Dynamic"]
    })
    
    return ratios

def run_algorithm_wrapper(args):
    """A wrapper function for run_algorithm that avoids pickling issues"""
    algorithm_name, job_list_data, checkpoint, arrival_rate, num_runs = args
    
    # Recreate algorithm function references inside the process
    algorithm_funcs = {
        'RDYNAMIC_SQRT_2': Rdynamic_sqrt_2.Rdynamic,
        'RDYNAMIC_SQRT_6': Rdynamic_sqrt_6.Rdynamic,
        'RDYNAMIC_SQRT_8': Rdynamic_sqrt_8.Rdynamic,
        'RDYNAMIC_SQRT_10': Rdynamic_sqrt_10.Rdynamic,
        'DYNAMIC': Dynamic.DYNAMIC,
    }
    
    # Get the appropriate algorithm function
    algorithm_func = algorithm_funcs.get(algorithm_name)
    if not algorithm_func:
        logger.error(f"Unknown algorithm: {algorithm_name}")
        return None
    
    # Run algorithm
    result = run_algorithm(
        algorithm_func,
        job_list_data,
        checkpoint,
        arrival_rate,
        num_runs=num_runs,
        algorithm_name=algorithm_name
    )
    
    return result

def process_task_mp(args):
    """Process a task with multiprocessing-safe approach"""
    task_type, setting, arrival_rate, bp_param, additional_data = args
    
    try:
        # Determine job file path based on task type
        if task_type == 'random':
            source_folder = f'freq_{setting}'
            job_file = f'data/{source_folder}/({arrival_rate}).csv'
            alternatives = [
                f'data/{source_folder}/({str(arrival_rate)}).csv',
                f'data/{source_folder}/{arrival_rate}.csv',
                f'data/{source_folder}/({int(float(arrival_rate)*10)}).csv',
                f'{source_folder}/({arrival_rate}).csv',
                f'freq_{setting}/({arrival_rate}).csv',
                f'data/freq_{setting}/({arrival_rate}).csv'
            ]
        else:  # compare
            data_folder = f'data/{setting}'
            job_file = f'{data_folder}/({arrival_rate}, {bp_param["L"]}).csv'
            alternatives = [
                f'{data_folder}/({str(arrival_rate)}, {str(bp_param["L"])}).csv',
                f'{data_folder}/{arrival_rate}_{bp_param["L"]}.csv',
                f'{data_folder}/({int(float(arrival_rate)*10)}, {bp_param["L"]}).csv',
                f'{setting}/({arrival_rate}, {bp_param["L"]}).csv',
                f'({arrival_rate}, {bp_param["L"]}).csv',
                f'data/({arrival_rate}, {bp_param["L"]}).csv',
                f'data_{setting}/({arrival_rate}, {bp_param["L"]}).csv',
            ]
        
        # Read job data
        job_list = None
        try:
            job_list = Read_csv.Read_csv(job_file)
            print(f"Successfully read job data from {job_file}")
        except Exception as e:
            print(f"Error reading {job_file}: {e}")
            # Try alternatives
            for alt_file in alternatives:
                try:
                    job_list = Read_csv.Read_csv(alt_file)
                    print(f"Successfully read from {alt_file}")
                    break
                except Exception:
                    continue
        
        if job_list is None:
            print(f"Failed to read any job data for task, skipping")
            return None
        
        # Get checkpoints
        rdyn2_checkpoint = CHECKPOINTS.get("RDYNAMIC_SQRT_2", 80)
        rdyn6_checkpoint = CHECKPOINTS.get("RDYNAMIC_SQRT_6", 60)
        rdyn8_checkpoint = CHECKPOINTS.get("RDYNAMIC_SQRT_8", 80)
        rdyn10_checkpoint = CHECKPOINTS.get("RDYNAMIC_SQRT_10", 100)
        dyn_checkpoint = CHECKPOINTS.get("Dynamic", 100)
        
        # Run algorithms in parallel but within this process
        # This avoids pickling issues since we're not passing file handles
        algorithm_tasks = [
            ('RDYNAMIC_SQRT_2', job_list, rdyn2_checkpoint, arrival_rate, 3),
            ('RDYNAMIC_SQRT_6', job_list, rdyn6_checkpoint, arrival_rate, 3),
            ('RDYNAMIC_SQRT_8', job_list, rdyn8_checkpoint, arrival_rate, 3),
            ('RDYNAMIC_SQRT_10', job_list, rdyn10_checkpoint, arrival_rate, 3),
            ('DYNAMIC', job_list, dyn_checkpoint, arrival_rate, 3)
        ]
        
        # Process algorithms sequentially (could use ThreadPool if needed)
        results = {
            'RDYNAMIC_SQRT_2': None,
            'RDYNAMIC_SQRT_6': None,
            'RDYNAMIC_SQRT_8': None,
            'RDYNAMIC_SQRT_10': None,
            'DYNAMIC': None
        }
        
        for task in algorithm_tasks:
            algo_name = task[0]
            algo_result = run_algorithm_wrapper(task)
            results[algo_name] = algo_result
        
        # Prepare result data
        rdynamic_sqrt_2_result = results['RDYNAMIC_SQRT_2']
        rdynamic_sqrt_6_result = results['RDYNAMIC_SQRT_6']
        rdynamic_sqrt_8_result = results['RDYNAMIC_SQRT_8']
        rdynamic_sqrt_10_result = results['RDYNAMIC_SQRT_10']
        dynamic_result = results['DYNAMIC']
        
        # Check if any algorithm succeeded
        algos_succeeded = any([
            rdynamic_sqrt_2_result and rdynamic_sqrt_2_result[1],
            rdynamic_sqrt_6_result and rdynamic_sqrt_6_result[1],
            rdynamic_sqrt_8_result and rdynamic_sqrt_8_result[1],
            rdynamic_sqrt_10_result and rdynamic_sqrt_10_result[1],
            dynamic_result and dynamic_result[1]
        ])
        
        if not algos_succeeded:
            print(f"All algorithms failed for task")
            # Provide default values
            rdynamic_sqrt_2_result = rdynamic_sqrt_2_result or ([DEFAULT_L2_VALUE], False)
            rdynamic_sqrt_6_result = rdynamic_sqrt_6_result or ([DEFAULT_L2_VALUE], False)
            rdynamic_sqrt_8_result = rdynamic_sqrt_8_result or ([DEFAULT_L2_VALUE], False)
            rdynamic_sqrt_10_result = rdynamic_sqrt_10_result or ([DEFAULT_L2_VALUE], False)
            dynamic_result = dynamic_result or ([DEFAULT_L2_VALUE], False)
        
        # Get phase1 data
        phase1_row = additional_data
        
        # Calculate ratios
        result_row = {
            'arrival_rate': float(arrival_rate),
            'bp_parameter': str(bp_param) if bp_param else ""
        }
        
        # Add calculated ratios
        ratio_data = calculate_ratios(
            rdynamic_sqrt_2_result, rdynamic_sqrt_6_result, 
            rdynamic_sqrt_8_result, rdynamic_sqrt_10_result, 
            dynamic_result, phase1_row
        )
        result_row.update(ratio_data)
        
        return (setting, result_row)
        
    except Exception as e:
        print(f"Error in process_task_mp: {e}")
        return None

def check_data_directories(settings):
    """Check and report on data directory structure for debugging"""
    logger.info("Checking data directories...")
    
    # Check main data folder
    if os.path.exists('data'):
        logger.info("Main 'data' directory exists")
        # List contents of data directory
        contents = os.listdir('data')
        logger.info(f"Contents of data directory: {contents}")
    else:
        logger.warning("Main 'data' directory does not exist!")
    
    # Check for specific setting folders
    for setting in settings:
        # Check various possible folder structures
        possible_folders = [
            f'data/{setting}',
            f'data_{setting}',
            setting,
            f'{setting}_data'
        ]
        
        found = False
        for folder in possible_folders:
            if os.path.exists(folder):
                logger.info(f"Found folder for setting '{setting}': {folder}")
                if os.path.isdir(folder):
                    try:
                        files = os.listdir(folder)
                        logger.info(f"First 5 files in {folder}: {files[:5] if len(files) > 5 else files}")
                        found = True
                        break
                    except Exception as e:
                        logger.error(f"Error listing contents of {folder}: {e}")
                else:
                    logger.warning(f"{folder} exists but is not a directory")
        
        if not found:
            logger.error(f"Could not find any data folder for setting '{setting}'")
    
    # Check result directories
    for setting in settings:
        result_folder = f'compare_{setting}'
        if os.path.exists(result_folder):
            logger.info(f"Result folder '{result_folder}' exists")
        else:
            logger.info(f"Result folder '{result_folder}' will be created")

def random_execute_phase2(arrival_rate_default, Csettings: list):
    """Execute phase 2 and calculate ratios for random data with hybrid multiprocessing"""
    logger.info(f"Starting hybrid multiprocessing random phase 2 for settings: {Csettings}")
    
    # Create shared file handler (only used for initial data reading)
    file_handler = SynchronizedFileHandler()
    
    # Convert settings to strings
    string_settings = [str(setting) for setting in Csettings]
    logger.info(f"Processing settings: {string_settings}")
    
    # Read phase1 data for each setting
    all_tasks = []
    
    for setting in string_settings:
        logger.info(f"Preparing tasks for setting: {setting}")
        # Try to read the combined results file first
        combined_file = f"freq/freq_{setting}_combined_results.csv"
        alt_file = f"freq/{setting}_combined_results.csv"
        
        phase1_df = None
        try:
            # Try both potential file paths
            if os.path.exists(combined_file):
                phase1_df = pd.read_csv(combined_file)
                logger.info(f"Successfully read combined file: {combined_file}")
            elif os.path.exists(alt_file):
                phase1_df = pd.read_csv(alt_file)
                logger.info(f"Successfully read combined file: {alt_file}")
            else:
                logger.warning(f"Combined files not found, reading with default arrival_rate")
                phase1_df = file_handler.read_phase1_results(arrival_rate_default, is_random=True, prefix=setting)
        except Exception as e:
            logger.error(f"Error reading phase1 results for setting {setting}: {e}")
            phase1_df = pd.DataFrame({'arrival_rate': [arrival_rate_default]})
        
        # Get arrival rates
        arrival_rates = []
        if phase1_df is not None and 'arrival_rate' in phase1_df.columns and len(phase1_df) > 0:
            arrival_rates = phase1_df['arrival_rate'].unique()
            
            # Limit to 5 rates to prevent excessive processing
            if len(arrival_rates) > 5:
                logger.warning(f"Too many arrival rates ({len(arrival_rates)}), limiting to 5")
                arrival_rates = arrival_rates[:5]
        else:
            arrival_rates = [arrival_rate_default]
        
        # Create tasks for each arrival rate
        for arr_rate in arrival_rates:
            logger.info(f"Creating task for arrival_rate={arr_rate}, setting={setting}")
            
            # Find the phase1 data for this arrival rate
            target_row = None
            if phase1_df is not None:
                matching_rows = phase1_df[phase1_df['arrival_rate'] == float(arr_rate)]
                if len(matching_rows) > 0:
                    target_row = matching_rows.iloc[0].to_dict()
            
            # If no target row found, create a default one
            if target_row is None:
                target_row = {
                    'arrival_rate': float(arr_rate),
                    'RR_L2_Norm': 100.0,
                    'SRPT_L2_Norm': 100.0,
                    'SETF_L2_Norm': 100.0,
                    'FCFS_L2_Norm': 100.0,
                    'RMLF_L2_Norm': 100.0
                }
            
            # Add task to list - bp_param is None for random tasks
            all_tasks.append(('random', setting, arr_rate, None, target_row))
    
    # Process tasks in parallel
    logger.info(f"Created {len(all_tasks)} tasks for processing")
    
    # Determine number of processes
    num_processes = min(len(all_tasks), max(1, mp.cpu_count() // 2))
    logger.info(f"Using {num_processes} processes")
    
    # Process tasks in parallel
    results_by_setting = {}
    
    if len(all_tasks) <= 2:  # Process sequentially for small number of tasks
        logger.info("Processing tasks sequentially")
        for task in all_tasks:
            result = process_task_mp(task)
            if result is not None:
                setting_str, result_row = result
                if setting_str not in results_by_setting:
                    results_by_setting[setting_str] = []
                results_by_setting[setting_str].append(result_row)
    else:  # Use multiprocessing for larger task sets
        with mp.Pool(processes=num_processes, maxtasksperchild=1) as pool:
            for result in pool.map(process_task_mp, all_tasks):
                if result is not None:
                    setting_str, result_row = result
                    if setting_str not in results_by_setting:
                        results_by_setting[setting_str] = []
                    results_by_setting[setting_str].append(result_row)
    
    # Process results for each setting
    successful = 0
    for setting_str, results in results_by_setting.items():
        if results:
            results_df = pd.DataFrame(results)
            
            # Save to the freq_comp_result folder
            result_folder = 'freq_comp_result'
            os.makedirs(result_folder, exist_ok=True)
            
            checkpoint_6 = CHECKPOINTS.get("RDYNAMIC_SQRT_6", 60)
            result_file = f'all_result_freq_{setting_str}_cp{checkpoint_6}.csv'
            
            output_file = os.path.join(result_folder, result_file)
            
            try:
                # Atomic write
                temp_file = f"{output_file}.tmp"
                results_df.to_csv(temp_file, index=False)
                os.replace(temp_file, output_file)
                logger.info(f"Successfully saved {len(results_df)} results to {output_file}")
                successful += 1
            except Exception as e:
                logger.error(f"Error saving results to {output_file}: {e}")
        else:
            logger.error(f"No results to save for setting freq_{setting_str}")
    
    logger.info(f"Successfully processed {successful}/{len(string_settings)} settings")
    return successful > 0

def compare_execute_phase2(arrival_rate, settings: list):
    """Execute phase 2 and calculate ratios for comparison data with hybrid multiprocessing"""
    logger.info(f"Starting hybrid multiprocessing compare phase 2 with arrival_rate={arrival_rate}")
    logger.info(f"Processing settings: {settings}")
    
    # Create shared file handler (only for initial reads)
    file_handler = SynchronizedFileHandler()
    
    # Collect all tasks upfront - each task is (task_type, setting, arrival_rate, bp_param, phase1_row)
    all_tasks = []
    
    for setting in settings:
        logger.info(f"Processing setting: {setting}")
        
        # Read phase1 results
        phase1_df = file_handler.read_phase1_results(arrival_rate, is_random=False, prefix=setting)
        logger.info(f"Read phase1 results for {setting} with {len(phase1_df)} rows")
        
        # Get bp_parameters for this setting
        bp_parameters = get_bp_parameters_for_setting(setting)
        if not bp_parameters:
            logger.error(f"No bp_parameters defined for setting {setting}")
            continue
        
        logger.info(f"Found {len(bp_parameters)} bp_parameters for setting {setting}")
        
        # Create tasks for each bp_parameter
        for bp_param in bp_parameters:
            logger.info(f"Creating task for bp_param {bp_param}, setting {setting}")
            
            # Find matching phase1 row
            phase1_row = None
            try:
                if 'bp_parameter' in phase1_df.columns:
                    try:
                        matching_rows = phase1_df[
                            phase1_df['bp_parameter'].apply(
                                lambda x: isinstance(x, dict) and 
                                        abs(float(x.get('L', 0)) - float(bp_param.get('L', 0))) < 0.1 and
                                        abs(float(x.get('H', 0)) - float(bp_param.get('H', 0))) < 0.1
                            )
                        ]
                        
                        if len(matching_rows) > 0:
                            phase1_row = matching_rows.iloc[0].to_dict()
                        else:
                            # If no exact match, try matching by L value only
                            matching_rows = phase1_df[
                                phase1_df['bp_parameter'].apply(
                                    lambda x: isinstance(x, dict) and 
                                            abs(float(x.get('L', 0)) - float(bp_param.get('L', 0))) < 0.1
                                )
                            ]
                            
                            if len(matching_rows) > 0:
                                phase1_row = matching_rows.iloc[0].to_dict()
                    except Exception as e:
                        logger.error(f"Error matching bp_parameter: {e}")
                
                # If we still don't have a match, use the first row
                if phase1_row is None:
                    if len(phase1_df) > 0:
                        phase1_row = phase1_df.iloc[0].to_dict()
                    else:
                        # Create default phase1 row
                        phase1_row = {
                            'arrival_rate': arrival_rate,
                            'bp_parameter': bp_param,
                            'RR_L2_Norm': 100.0,
                            'SRPT_L2_Norm': 100.0,
                            'SETF_L2_Norm': 100.0,
                            'FCFS_L2_Norm': 100.0,
                            'RMLF_L2_Norm': 100.0
                        }
            except Exception as e:
                logger.error(f"Error in phase1 matching: {e}")
                # Create default phase1 row
                phase1_row = {
                    'arrival_rate': arrival_rate,
                    'bp_parameter': bp_param,
                    'RR_L2_Norm': 100.0,
                    'SRPT_L2_Norm': 100.0,
                    'SETF_L2_Norm': 100.0,
                    'FCFS_L2_Norm': 100.0,
                    'RMLF_L2_Norm': 100.0
                }
            
            # Add task to list
            all_tasks.append(('compare', setting, arrival_rate, bp_param, phase1_row))
    
    # Process tasks in parallel
    logger.info(f"Created {len(all_tasks)} tasks for processing")
    
    # Determine number of processes
    num_processes = min(len(all_tasks), max(1, mp.cpu_count() // 2))
    logger.info(f"Using {num_processes} processes")
    
    # Process tasks in parallel
    results_by_setting = {}
    
    if len(all_tasks) <= 2:  # Process sequentially for small number of tasks
        logger.info("Processing tasks sequentially")
        for task in all_tasks:
            result = process_task_mp(task)
            if result is not None:
                setting_str, result_row = result
                if setting_str not in results_by_setting:
                    results_by_setting[setting_str] = []
                results_by_setting[setting_str].append(result_row)
    else:  # Use multiprocessing for larger task sets
        with mp.Pool(processes=num_processes, maxtasksperchild=1) as pool:
            for result in pool.map(process_task_mp, all_tasks):
                if result is not None:
                    setting_str, result_row = result
                    if setting_str not in results_by_setting:
                        results_by_setting[setting_str] = []
                    results_by_setting[setting_str].append(result_row)
    
    # Save results for each setting
    successful = 0
    for setting, results in results_by_setting.items():
        if results:
            results_df = pd.DataFrame(results)
            logger.info(f"Saving {len(results_df)} results for {setting}")
            
            # Save to correct folder
            result_folder = f'compare_{setting}'
            os.makedirs(result_folder, exist_ok=True)
            
            checkpoint_6 = CHECKPOINTS.get("RDYNAMIC_SQRT_6", 60)
            result_file = f'all_result_{setting}_cp{checkpoint_6}.csv'
            
            output_file = os.path.join(result_folder, result_file)
            
            try:
                # Atomic write
                temp_file = f"{output_file}.tmp"
                results_df.to_csv(temp_file, index=False)
                os.replace(temp_file, output_file)
                logger.info(f"Successfully saved {len(results_df)} results to {output_file}")
                successful += 1
            except Exception as e:
                logger.error(f"Error saving results to {output_file}: {e}")
        else:
            logger.error(f"No results to save for setting {setting}")
    
    return successful > 0

def get_bp_parameters_for_setting(setting):
    """Get the appropriate bp_parameters for a given setting with improved logging"""
    logger.info(f"Getting bp_parameters for setting {setting}")
    if setting == 'avg_30':
        return [
            {"L": 16.772, "H": pow(2, 6)},
            {"L": 7.918, "H": pow(2, 9)},
            {"L": 5.649, "H": pow(2, 12)},
            {"L": 4.639, "H": pow(2, 15)},
            {"L": 4.073, "H": pow(2, 18)}
        ]
    elif setting == 'avg_60':
        return [
            {"L": 56.300, "H": pow(2, 6)},
            {"L": 18.900, "H": pow(2, 9)},
            {"L": 12.400, "H": pow(2, 12)},
            {"L": 9.800, "H": pow(2, 15)},
            {"L": 8.500, "H": pow(2, 18)}
        ]
    elif setting == 'avg_90':
        return [
            {"L": 32.300, "H": pow(2, 9)},
            {"L": 19.700, "H": pow(2, 12)},
            {"L": 15.300, "H": pow(2, 15)},
            {"L": 13.000, "H": pow(2, 18)}
        ]
    elif setting == 'freq':
        # Special case for freq - use a default L value
        return [{"L": 10.0, "H": pow(2, 10)}]
    else:
        logger.error(f"Unknown setting: {setting}, using default bp_parameter")
        # Return a default parameter rather than empty list
        return [{"L": 10.0, "H": pow(2, 10)}]

def process_single_bp_parameter(args):
    """Process a single bp_parameter entry - SIMPLIFIED VERSION TO AVOID PICKLING"""
    arrival_rate, bp_param, phase1_df, file_handler = args
    
    try:
        logger.info(f"Processing bp_parameter: {bp_param}")
        
        # Standardized job file naming that matches execute_standard.py's output
        job_file = f'data/({arrival_rate}, {bp_param["L"]}).csv'
        logger.info(f"Reading job data from: {job_file}")
        
        job_list = None
        try:
            job_list = Read_csv.Read_csv(job_file)
        except Exception as e:
            logger.error(f"Error reading job file {job_file}: {e}")
            # Try alternative file naming - prioritize formats from execute_standard.py
            alt_files = [
                f'data/({str(arrival_rate)}, {str(bp_param["L"])}).csv',
                f'data/{arrival_rate}_{bp_param["L"]}.csv',
                f'data/({int(arrival_rate*10)}, {bp_param["L"]}).csv',  # For formats like (20, 16.772)
                f'({arrival_rate}, {bp_param["L"]}).csv'
            ]
            
            for alt_file in alt_files:
                try:
                    job_list = Read_csv.Read_csv(alt_file)
                    logger.info(f"Successfully read from alternative file: {alt_file}")
                    break
                except Exception as e2:
                    continue
            
            if job_list is None:
                logger.error(f"Skipping bp_parameter {bp_param} due to file read error")
                return None
        
        # Run algorithms using the checkpoint constants - now with success tracking
        rdynamic_sqrt_2_result = run_algorithm(
            Rdynamic_sqrt_2.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_2"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_2"
        )
        
        rdynamic_sqrt_6_result = run_algorithm(
            Rdynamic_sqrt_6.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_6"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_6"
        )
        
        rdynamic_sqrt_8_result = run_algorithm(
            Rdynamic_sqrt_8.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_8"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_8"
        )
        
        rdynamic_sqrt_10_result = run_algorithm(
            Rdynamic_sqrt_10.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_10"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_10"
        )
        
        dynamic_result = run_algorithm(
            Dynamic.DYNAMIC, 
            job_list, 
            CHECKPOINTS["Dynamic"], 
            arrival_rate,
            algorithm_name="Dynamic"
        )
        
        # Check if any algorithm succeeded
        algos_succeeded = any([
            rdynamic_sqrt_2_result[1], rdynamic_sqrt_6_result[1], 
            rdynamic_sqrt_8_result[1], rdynamic_sqrt_10_result[1], 
            dynamic_result[1]
        ])
        
        if not algos_succeeded:
            logger.error(f"All algorithms failed for bp_parameter {bp_param}")
            return None
        
        # Simplified matching logic - first try exact match on both L and H
        matching_rows = phase1_df[
            phase1_df['bp_parameter'].apply(
                lambda x: isinstance(x, dict) and 
                          x.get('L') == bp_param.get('L') and 
                          x.get('H') == bp_param.get('H')
            )
        ]
        
        if len(matching_rows) > 0:
            logger.info(f"Found exact match for bp_parameter: {bp_param}")
            phase1_row = matching_rows.iloc[0].to_dict()
        else:
            # If no exact match, try matching only by L value with small tolerance
            logger.warning(f"No exact match, trying match by L value only")
            matching_rows = phase1_df[
                phase1_df['bp_parameter'].apply(
                    lambda x: isinstance(x, dict) and 
                            abs(float(x.get('L', 0)) - float(bp_param.get('L', 0))) < 0.1
                )
            ]
            
            if len(matching_rows) > 0:
                logger.info(f"Found match by L value for bp_parameter: {bp_param}")
                phase1_row = matching_rows.iloc[0].to_dict()
            else:
                # Just use the first row if still no match
                if len(phase1_df) > 0:
                    logger.warning(f"No matching row, using first available row from phase1")
                    phase1_row = phase1_df.iloc[0].to_dict()
                else:
                    # Create a default phase1 row with warning
                    logger.warning(f"No phase1 data available, using default values")
                    phase1_row = {
                        'arrival_rate': arrival_rate,
                        'bp_parameter': bp_param,
                        'RR_L2_Norm': 100.0,
                        'SRPT_L2_Norm': 100.0,
                        'SETF_L2_Norm': 100.0,
                        'FCFS_L2_Norm': 100.0,
                        'RMLF_L2_Norm': 100.0
                    }
        
        # Calculate ratios and include L2 norms - now with algorithm success tracking
        result_row = {
            'arrival_rate': arrival_rate,
            'bp_parameter': str(bp_param),
            **calculate_ratios(
                rdynamic_sqrt_2_result, rdynamic_sqrt_6_result, 
                rdynamic_sqrt_8_result, rdynamic_sqrt_10_result, 
                dynamic_result, phase1_row
            )
        }
        
        logger.info(f"Completed processing for bp_parameter: {bp_param}")
        logger.info(f"Algorithm statuses: R2={rdynamic_sqrt_2_result[1]}, R6={rdynamic_sqrt_6_result[1]}, " + 
                   f"R8={rdynamic_sqrt_8_result[1]}, R10={rdynamic_sqrt_10_result[1]}, " +
                   f"Dynamic={dynamic_result[1]}")
        
        return result_row
    
    except Exception as e:
        logger.error(f"Error in process_single_bp_parameter for bp_param={bp_param}: {e}")
        logger.error(traceback.format_exc())
        return None

def execute_phase2(arrival_rate, bp_parameter, file_handler):
    """Execute phase 2 and calculate ratios in parallel"""
    logger.info(f"Starting phase 2 with arrival_rate={arrival_rate}")
    logger.info(f"Number of bp_parameters to process: {len(bp_parameter)}")
    logger.info(f"Using checkpoints: {CHECKPOINTS}")
    
    # Read phase1 results - use consistent file naming based on execute_standard.py
    phase1_df = file_handler.read_phase1_results(arrival_rate)
    logger.info(f"Read phase1 results with {len(phase1_df)} rows")

    # Convert bp_parameter to dict format if needed
    if 'bp_parameter' in phase1_df.columns and isinstance(phase1_df['bp_parameter'].iloc[0], str):
        try:
            phase1_df['bp_parameter'] = phase1_df['bp_parameter'].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            logger.info("Successfully converted bp_parameter to dict format")
        except Exception as e:
            logger.warning(f"Error parsing bp_parameter as dict: {e}")
    
    # CRITICAL CHANGE: Process sequentially for small number of parameters
    # This avoids process pool overhead and potential resource issues
    if len(bp_parameter) <= 3:
        logger.info(f"Processing {len(bp_parameter)} bp_parameters sequentially")
        results = []
        for bp_param in bp_parameter:
            result = process_single_bp_parameter((arrival_rate, bp_param, phase1_df, file_handler))
            if result is not None:
                results.append(result)
                
        if results:
            results_df = pd.DataFrame(results)
            logger.info(f"Saving results with {len(results_df)} rows")
            file_handler.save_results(
                results_df, 
                'data'  # Source folder
            )
            return True
        
        logger.error("No results to save")
        return False
    
    # Only use process pool for larger parameter sets
    # Prepare arguments for parallel processing
    process_args = [(arrival_rate, bp_param, phase1_df, file_handler) for bp_param in bp_parameter]
    
    # Limit the number of processes to avoid resource exhaustion
    num_processes = min(len(bp_parameter), max(1, mp.cpu_count() // 2))  # Use at most half of available CPUs
    logger.info(f"Using {num_processes} processes for parallel execution")
    
    results = []
    # CRITICAL: Set maxtasksperchild to ensure processes are recycled
    with mp.Pool(processes=num_processes, maxtasksperchild=1) as pool:
        # Apply the process_single_bp_parameter function to each parameter set
        for result in pool.map(process_single_bp_parameter, process_args):
            if result is not None:
                results.append(result)
    
    if results:
        results_df = pd.DataFrame(results)
        logger.info(f"Saving results with {len(results_df)} rows")
        file_handler.save_results(
            results_df, 
            'data'  # Source folder
        )
        return True
    
    logger.error("No results to save")
    return False

def execute(arrival_rate, bp_parameter):
    """Main execution function"""
    logger.info(f"execute() called with arrival_rate={arrival_rate}, {len(bp_parameter)} bp_parameters")
    file_handler = SynchronizedFileHandler()
    return execute_phase2(arrival_rate, bp_parameter, file_handler)

def execute_random(arrival_rate_default, Csettings: list):
    """Main execution function for random data using hybrid multiprocessing"""
    return random_execute_phase2(arrival_rate_default, Csettings)

def execute_softrandom(arrival_rate_default, Csettings: list):
    """Main execution function for soft random data using hybrid multiprocessing"""
    logger.info(f"Starting softrandom execution for settings: {Csettings}")
    return random_execute_phase2(arrival_rate_default, Csettings)

def execute_compare(arrival_rate, settings: list):
    """Main execution function for comparison data using hybrid multiprocessing"""
    logger.info(f"execute_compare called with arrival_rate={arrival_rate}, settings={settings}")
    check_data_directories(settings)
    return compare_execute_phase2(arrival_rate, settings)