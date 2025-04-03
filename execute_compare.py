import multiprocessing as mp
from multiprocessing import Manager
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
from concurrent.futures import TimeoutError

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

class SynchronizedFileHandler:
    """Thread-safe file handler for parallel processing"""
    def __init__(self):
        manager = Manager()
        self._lock = manager.Lock()
    
    @staticmethod
    def ensure_directory_exists(directory_path):
        """Create directory if it doesn't exist"""
        Path(directory_path).mkdir(parents=True, exist_ok=True)
    
    def save_results(self, results_df, source_folder, mode='w'):
        """Thread-safe method to save results"""
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
                self.ensure_directory_exists(result_folder)
                
                # Update combined results file
                combined_file = os.path.join(result_folder, result_file)
                temp_combined = f"{combined_file}.tmp"
                
                if os.path.exists(combined_file):
                    try:
                        all_results_df = pd.read_csv(combined_file)
                        logger.info(f"Read existing results file with {len(all_results_df)} rows")
                        
                        # For freq_X case, we need to be careful about updates
                        # Convert all arrival_rate to float for consistent comparison
                        results_df['arrival_rate'] = results_df['arrival_rate'].astype(float)
                        if 'arrival_rate' in all_results_df.columns:
                            all_results_df['arrival_rate'] = all_results_df['arrival_rate'].astype(float)
                        
                        # IMPROVED: Create a mask for each row to identify duplicates
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
                else:
                    logger.info(f"No existing results file found, creating new file")
                    all_results_df = results_df.copy()
                
                # Sort by arrival_rate for better readability
                all_results_df = all_results_df.sort_values('arrival_rate')
                
                # Atomic write to combined file
                all_results_df.to_csv(temp_combined, index=False)
                os.replace(temp_combined, combined_file)
                
                logger.info(f"Results saved to combined file: {combined_file} with {len(all_results_df)} rows")
                return True
                
            except Exception as e:
                logger.error(f"Error saving results: {e}")
                import traceback
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
    """Execute scheduler with timeout"""
    try:
        # Create a process for the algorithm execution
        with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args)
            return future.result(timeout=timeout)
    except TimeoutError:
        logger.error(f"Timeout in {func.__name__} after {timeout} seconds")
        return None
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
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
        except Exception as e:
            logger.error(f"Error in run {run_number} for {algorithm_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            continue
    
    # Return at least one result if all runs fail
    if not results and job_list:
        logger.warning(f"All runs of {algorithm_name} failed, returning default value")
        return [1000.0]  # Default L2 norm value
    
    return results if results else None

def calculate_ratios(rdynamic_sqrt_2_l2, rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2, phase1_row):
    """Calculate performance ratios between all algorithms"""
    ratios = {}
    
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
    
    # Add raw L2 norms for reference
    ratios.update({
        'Rdynamic_sqrt_2_L2': rdynamic_sqrt_2_l2,
        'Rdynamic_sqrt_6_L2': rdynamic_sqrt_6_l2,
        'Rdynamic_sqrt_8_L2': rdynamic_sqrt_8_l2,
        'Rdynamic_sqrt_10_L2': rdynamic_sqrt_10_l2,
        'Dynamic_L2': dynamic_l2,
        'RR_L2_Norm': rr_norm,
        'SRPT_L2_Norm': srpt_norm,
        'SETF_L2_Norm': setf_norm,
        'FCFS_L2_Norm': fcfs_norm,
        'RMLF_L2_Norm': rmlf_norm
    })
    
    # Add RMLF/FCFS ratio - NEW ADDITION
    ratios.update({
        'RMLF/FCFS_ratio': safe_divide(rmlf_norm, fcfs_norm)
    })
    
    # Rdynamic_sqrt_2 ratios
    ratios.update({
        'Rdynamic_sqrt_2/RR_ratio': safe_divide(rdynamic_sqrt_2_l2, rr_norm),
        'Rdynamic_sqrt_2/SRPT_ratio': safe_divide(rdynamic_sqrt_2_l2, srpt_norm),
        'Rdynamic_sqrt_2/SETF_ratio': safe_divide(rdynamic_sqrt_2_l2, setf_norm),
        'Rdynamic_sqrt_2/FCFS_ratio': safe_divide(rdynamic_sqrt_2_l2, fcfs_norm),
        'Rdynamic_sqrt_2/RMLF_ratio': safe_divide(rdynamic_sqrt_2_l2, rmlf_norm),
        'Rdynamic_sqrt_2/Dynamic_ratio': safe_divide(rdynamic_sqrt_2_l2, dynamic_l2)
    })
    
    # Rdynamic_sqrt_6 ratios
    ratios.update({
        'Rdynamic_sqrt_6/RR_ratio': safe_divide(rdynamic_sqrt_6_l2, rr_norm),
        'Rdynamic_sqrt_6/SRPT_ratio': safe_divide(rdynamic_sqrt_6_l2, srpt_norm),
        'Rdynamic_sqrt_6/SETF_ratio': safe_divide(rdynamic_sqrt_6_l2, setf_norm),
        'Rdynamic_sqrt_6/FCFS_ratio': safe_divide(rdynamic_sqrt_6_l2, fcfs_norm),
        'Rdynamic_sqrt_6/RMLF_ratio': safe_divide(rdynamic_sqrt_6_l2, rmlf_norm),
        'Rdynamic_sqrt_6/Dynamic_ratio': safe_divide(rdynamic_sqrt_6_l2, dynamic_l2)
    })
    
    # Rdynamic_sqrt_8 ratios
    ratios.update({
        'Rdynamic_sqrt_8/RR_ratio': safe_divide(rdynamic_sqrt_8_l2, rr_norm),
        'Rdynamic_sqrt_8/SRPT_ratio': safe_divide(rdynamic_sqrt_8_l2, srpt_norm),
        'Rdynamic_sqrt_8/SETF_ratio': safe_divide(rdynamic_sqrt_8_l2, setf_norm),
        'Rdynamic_sqrt_8/FCFS_ratio': safe_divide(rdynamic_sqrt_8_l2, fcfs_norm),
        'Rdynamic_sqrt_8/RMLF_ratio': safe_divide(rdynamic_sqrt_8_l2, rmlf_norm),
        'Rdynamic_sqrt_8/Dynamic_ratio': safe_divide(rdynamic_sqrt_8_l2, dynamic_l2)
    })
    
    # Rdynamic_sqrt_10 ratios
    ratios.update({
        'Rdynamic_sqrt_10/RR_ratio': safe_divide(rdynamic_sqrt_10_l2, rr_norm),
        'Rdynamic_sqrt_10/SRPT_ratio': safe_divide(rdynamic_sqrt_10_l2, srpt_norm),
        'Rdynamic_sqrt_10/SETF_ratio': safe_divide(rdynamic_sqrt_10_l2, setf_norm),
        'Rdynamic_sqrt_10/FCFS_ratio': safe_divide(rdynamic_sqrt_10_l2, fcfs_norm),
        'Rdynamic_sqrt_10/RMLF_ratio': safe_divide(rdynamic_sqrt_10_l2, rmlf_norm),
        'Rdynamic_sqrt_10/Dynamic_ratio': safe_divide(rdynamic_sqrt_10_l2, dynamic_l2)
    })
    
    # Dynamic ratio
    ratios.update({
        'Dynamic/SRPT_ratio': safe_divide(dynamic_l2, srpt_norm)
    })
    
    # Comparisons between Rdynamic variants
    ratios.update({
        'Rdynamic_sqrt_2/Rdynamic_sqrt_6_ratio': safe_divide(rdynamic_sqrt_2_l2, rdynamic_sqrt_6_l2),
        'Rdynamic_sqrt_2/Rdynamic_sqrt_8_ratio': safe_divide(rdynamic_sqrt_2_l2, rdynamic_sqrt_8_l2),
        'Rdynamic_sqrt_2/Rdynamic_sqrt_10_ratio': safe_divide(rdynamic_sqrt_2_l2, rdynamic_sqrt_10_l2),
        'Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio': safe_divide(rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2),
        'Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio': safe_divide(rdynamic_sqrt_6_l2, rdynamic_sqrt_10_l2),
        'Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio': safe_divide(rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2)
    })
    
    # Add checkpoint value to results
    ratios.update({
        'Rdynamic_sqrt_2_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_2"],
        'Rdynamic_sqrt_6_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_6"],
        'Rdynamic_sqrt_8_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_8"],
        'Rdynamic_sqrt_10_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_10"],
        'Dynamic_checkpoint': CHECKPOINTS["Dynamic"]
    })
    
    return ratios

def calculate_ratios_without_phase1(rdynamic_sqrt_2_l2, rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2):
    """Calculate performance ratios between algorithms without requiring phase1 results"""
    ratios = {}
    
    # Safety check: ensure no division by zero
    def safe_divide(a, b, default=1.0):
        try:
            return a / b if b != 0 else default
        except:
            return default
    
    # Add raw L2 norms for reference
    ratios.update({
        'Rdynamic_sqrt_2_L2': rdynamic_sqrt_2_l2,
        'Rdynamic_sqrt_6_L2': rdynamic_sqrt_6_l2,
        'Rdynamic_sqrt_8_L2': rdynamic_sqrt_8_l2,
        'Rdynamic_sqrt_10_L2': rdynamic_sqrt_10_l2,
        'Dynamic_L2': dynamic_l2
    })
    
    # Ratios between Dynamic and Rdynamic variants
    ratios.update({
        'Rdynamic_sqrt_2/Dynamic_ratio': safe_divide(rdynamic_sqrt_2_l2, dynamic_l2),
        'Rdynamic_sqrt_6/Dynamic_ratio': safe_divide(rdynamic_sqrt_6_l2, dynamic_l2),
        'Rdynamic_sqrt_8/Dynamic_ratio': safe_divide(rdynamic_sqrt_8_l2, dynamic_l2),
        'Rdynamic_sqrt_10/Dynamic_ratio': safe_divide(rdynamic_sqrt_10_l2, dynamic_l2)
    })
    
    # Comparisons between Rdynamic variants
    ratios.update({
        'Rdynamic_sqrt_2/Rdynamic_sqrt_6_ratio': safe_divide(rdynamic_sqrt_2_l2, rdynamic_sqrt_6_l2),
        'Rdynamic_sqrt_2/Rdynamic_sqrt_8_ratio': safe_divide(rdynamic_sqrt_2_l2, rdynamic_sqrt_8_l2),
        'Rdynamic_sqrt_2/Rdynamic_sqrt_10_ratio': safe_divide(rdynamic_sqrt_2_l2, rdynamic_sqrt_10_l2),
        'Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio': safe_divide(rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2),
        'Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio': safe_divide(rdynamic_sqrt_6_l2, rdynamic_sqrt_10_l2),
        'Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio': safe_divide(rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2)
    })
    
    # Add checkpoint value to results
    ratios.update({
        'Rdynamic_sqrt_2_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_2"],
        'Rdynamic_sqrt_6_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_6"],
        'Rdynamic_sqrt_8_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_8"],
        'Rdynamic_sqrt_10_checkpoint': CHECKPOINTS["RDYNAMIC_SQRT_10"],
        'Dynamic_checkpoint': CHECKPOINTS["Dynamic"]
    })
    
    return ratios

def execute_phase2(arrival_rate, bp_parameter, file_handler):
    """Execute phase 2 and calculate ratios"""
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

    results = []
    for bp_param in bp_parameter:
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
                continue
        
        # Run algorithms using the checkpoint constants
        rdynamic_sqrt_2_l2_norms = run_algorithm(
            Rdynamic_sqrt_2.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_2"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_2"
        )
        
        rdynamic_sqrt_6_l2_norms = run_algorithm(
            Rdynamic_sqrt_6.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_6"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_6"
        )
        
        rdynamic_sqrt_8_l2_norms = run_algorithm(
            Rdynamic_sqrt_8.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_8"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_8"
        )
        
        rdynamic_sqrt_10_l2_norms = run_algorithm(
            Rdynamic_sqrt_10.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_10"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_10"
        )
        
        dynamic_l2_norms = run_algorithm(
            Dynamic.DYNAMIC, 
            job_list, 
            CHECKPOINTS["Dynamic"], 
            arrival_rate,
            algorithm_name="Dynamic"
        )
        
        # Even if some algorithms fail, continue with those that succeeded
        # by using default values for failed algorithms
        rdynamic_sqrt_2_l2 = np.mean(rdynamic_sqrt_2_l2_norms) if rdynamic_sqrt_2_l2_norms else 1000.0
        rdynamic_sqrt_6_l2 = np.mean(rdynamic_sqrt_6_l2_norms) if rdynamic_sqrt_6_l2_norms else 1000.0
        rdynamic_sqrt_8_l2 = np.mean(rdynamic_sqrt_8_l2_norms) if rdynamic_sqrt_8_l2_norms else 1000.0
        rdynamic_sqrt_10_l2 = np.mean(rdynamic_sqrt_10_l2_norms) if rdynamic_sqrt_10_l2_norms else 1000.0
        dynamic_l2 = np.mean(dynamic_l2_norms) if dynamic_l2_norms else 1000.0
        
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
        
        # Calculate ratios and include L2 norms
        result_row = {
            'arrival_rate': arrival_rate,
            'bp_parameter': str(bp_param),
            **calculate_ratios(rdynamic_sqrt_2_l2, rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2, phase1_row)
        }
        results.append(result_row)
        logger.info(f"Added result row for bp_parameter: {bp_param}")
    
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

def process_single_setting(args):
    """Process a single random setting with synchronized file handling - REVISED for better phase1 handling"""
    arrival_rate, setting, file_handler = args
    
    try:
        # Set a timeout for the entire process
        start_time = time.time()
        
        # For random data, use the correct source folder
        source_folder = f'freq_{setting}'
        
        # Try to find phase1 results for this specific arrival rate
        # First, try the combined results file directly
        logger.info(f"Processing arrival_rate={arrival_rate} for setting {setting}")
        
        # Try to directly read from the combined file first
        combined_file = f"freq/freq_{setting}_combined_results.csv"
        alt_file = f"freq/{setting}_combined_results.csv"
        
        phase1_row = None
        try:
            if os.path.exists(combined_file):
                combined_df = pd.read_csv(combined_file)
                logger.info(f"Successfully read combined file: {combined_file}")
                
                # Find the exact row for this arrival rate
                matching_rows = combined_df[combined_df['arrival_rate'] == float(arrival_rate)]
                if len(matching_rows) > 0:
                    phase1_row = matching_rows.iloc[0].to_dict()
                    logger.info(f"Found exact matching row for arrival_rate={arrival_rate}")
                else:
                    logger.warning(f"No exact match for arrival_rate={arrival_rate} in combined file")
            elif os.path.exists(alt_file):
                combined_df = pd.read_csv(alt_file)
                logger.info(f"Successfully read combined file: {alt_file}")
                
                # Find the exact row for this arrival rate
                matching_rows = combined_df[combined_df['arrival_rate'] == float(arrival_rate)]
                if len(matching_rows) > 0:
                    phase1_row = matching_rows.iloc[0].to_dict()
                    logger.info(f"Found exact matching row for arrival_rate={arrival_rate}")
                else:
                    logger.warning(f"No exact match for arrival_rate={arrival_rate} in combined file")
        except Exception as e:
            logger.error(f"Error reading combined file: {e}")
        
        # If no phase1_row was found, fall back to the regular method
        if phase1_row is None:
            logger.info(f"Falling back to read_phase1_results for arrival_rate={arrival_rate}")
            phase1_df = file_handler.read_phase1_results(arrival_rate, is_random=True, prefix=setting)
            
            # Use the first row
            if len(phase1_df) > 0:
                phase1_row = phase1_df.iloc[0].to_dict()
                logger.info(f"Using first row from phase1 results")
            else:
                logger.warning(f"No phase1 data available, will use dummy values")
                # We'll create a dummy row later if needed
        
        # Read job data for this specific arrival rate
        job_file = f'data/{source_folder}/({arrival_rate}).csv'
        logger.info(f"Attempting to read job data from: {job_file}")
        
        job_list = None
        try:
            job_list = Read_csv.Read_csv(job_file)
            logger.info(f"Successfully read job data from {job_file}")
        except Exception as e:
            logger.error(f"Error reading job file {job_file}: {e}")
            # Try alternatives with preference to formats used by execute_standard.py
            alternatives = [
                f'data/{source_folder}/({str(arrival_rate)}).csv',
                f'data/{source_folder}/{arrival_rate}.csv',
                f'data/{source_folder}/({int(float(arrival_rate)*10)}).csv',  # Added for decimal conversion
                f'{source_folder}/({arrival_rate}).csv'
            ]
            
            for alt_file in alternatives:
                logger.info(f"Trying alternative file path: {alt_file}")
                try:
                    job_list = Read_csv.Read_csv(alt_file)
                    logger.info(f"Successfully read from {alt_file}")
                    break
                except Exception as e2:
                    logger.warning(f"Failed to read from {alt_file}: {e2}")
                    continue
            
            if job_list is None:
                logger.error(f"Failed to read job data from all attempted paths")
                return None
        
        logger.info(f"Using checkpoints for setting {setting}: {CHECKPOINTS}")

        # Run algorithms using the checkpoint constants
        rdynamic_sqrt_2_l2_norms = run_algorithm(
            Rdynamic_sqrt_2.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_2"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_2"
        )
        
        rdynamic_sqrt_6_l2_norms = run_algorithm(
            Rdynamic_sqrt_6.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_6"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_6"
        )
        
        rdynamic_sqrt_8_l2_norms = run_algorithm(
            Rdynamic_sqrt_8.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_8"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_8"
        )
        
        rdynamic_sqrt_10_l2_norms = run_algorithm(
            Rdynamic_sqrt_10.Rdynamic, 
            job_list, 
            CHECKPOINTS["RDYNAMIC_SQRT_10"], 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_10"
        )
        
        dynamic_l2_norms = run_algorithm(
            Dynamic.DYNAMIC, 
            job_list, 
            CHECKPOINTS["Dynamic"], 
            arrival_rate,
            algorithm_name="Dynamic"
        )

        # Check if process timeout is approaching
        elapsed_time = time.time() - start_time
        if elapsed_time >= PROCESS_TIMEOUT:
            logger.warning(f"Process timeout approaching for arrival_rate={arrival_rate}, setting={setting}")
            return None

        # Calculate means of L2 norms with fallbacks
        rdynamic_sqrt_2_l2 = np.mean(rdynamic_sqrt_2_l2_norms) if rdynamic_sqrt_2_l2_norms else 1000.0
        rdynamic_sqrt_6_l2 = np.mean(rdynamic_sqrt_6_l2_norms) if rdynamic_sqrt_6_l2_norms else 1000.0
        rdynamic_sqrt_8_l2 = np.mean(rdynamic_sqrt_8_l2_norms) if rdynamic_sqrt_8_l2_norms else 1000.0
        rdynamic_sqrt_10_l2 = np.mean(rdynamic_sqrt_10_l2_norms) if rdynamic_sqrt_10_l2_norms else 1000.0
        dynamic_l2 = np.mean(dynamic_l2_norms) if dynamic_l2_norms else 1000.0
        
        # If phase1 data is available, use it for complete comparison
        if phase1_row is not None:
            logger.info(f"Using phase1 row: {phase1_row}")
            
            # Calculate full ratios with phase1 data
            result_row = {
                'arrival_rate': float(arrival_rate),  # Ensure arrival_rate is consistent
                **calculate_ratios(rdynamic_sqrt_2_l2, rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2, phase1_row)
            }
            logger.info("Calculated ratios with phase1 data")
        else:
            # If no phase1 data, use limited comparison
            logger.warning("No phase1 data available, using limited ratios")
            result_row = {
                'arrival_rate': float(arrival_rate),
                **calculate_ratios_without_phase1(rdynamic_sqrt_2_l2, rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2)
            }
        
        # Create and save DataFrame
        results_df = pd.DataFrame([result_row])
        logger.info(f"Saving results for arrival_rate={arrival_rate}, setting={setting}")
        return file_handler.save_results(
            results_df,
            source_folder
        )
    except Exception as e:
        logger.error(f"Error in process_single_setting for arrival_rate={arrival_rate}, setting={setting}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def process_compare_setting(args):
    """Process a compare setting (avg_30, avg_60, avg_90, freq) - REVISED for better phase1 handling"""
    arrival_rate, setting, file_handler = args
    
    try:
        # Set a timeout for the entire process
        start_time = time.time()
        
        # Read phase1 results using execute_standard.py's naming pattern
        logger.info(f"Reading phase1 results for {setting} with arrival_rate={arrival_rate}")
        phase1_df = file_handler.read_phase1_results(arrival_rate, is_random=False, prefix=setting)
        logger.info(f"Read phase1 results with {len(phase1_df)} rows")
        
        # Convert bp_parameter to dict format if needed
        if 'bp_parameter' in phase1_df.columns and len(phase1_df) > 0 and isinstance(phase1_df['bp_parameter'].iloc[0], str):
            try:
                phase1_df['bp_parameter'] = phase1_df['bp_parameter'].apply(
                    lambda x: ast.literal_eval(x) if isinstance(x, str) else x
                )
                logger.info("Successfully converted bp_parameter to dict format")
            except Exception as e:
                logger.warning(f"Error parsing bp_parameter as dict: {e}")

        # Define bp_parameters according to execute_standard.py's structure
        if setting == 'avg_30':
            bp_parameters = [
                {"L": 16.772, "H": pow(2, 6)},
                {"L": 7.918, "H": pow(2, 9)},
                {"L": 5.649, "H": pow(2, 12)},
                {"L": 4.639, "H": pow(2, 15)},
                {"L": 4.073, "H": pow(2, 18)}
            ]
        elif setting == 'avg_60':
            bp_parameters = [
                {"L": 56.300, "H": pow(2, 6)},
                {"L": 18.900, "H": pow(2, 9)},
                {"L": 12.400, "H": pow(2, 12)},
                {"L": 9.800, "H": pow(2, 15)},
                {"L": 8.500, "H": pow(2, 18)}
            ]
        elif setting == 'avg_90':
            bp_parameters = [
                {"L": 32.300, "H": pow(2, 9)},
                {"L": 19.700, "H": pow(2, 12)},
                {"L": 15.300, "H": pow(2, 15)},
                {"L": 13.000, "H": pow(2, 18)}
            ]
        elif setting == 'freq':
            # Special case for freq - use a default L value
            bp_parameters = [{"L": 10.0, "H": pow(2, 10)}]
        else:
            logger.error(f"Unknown setting: {setting}")
            return None
        
        source_folder = setting
        
        # Process each bp_parameter
        results_for_all_params = []
        
        for bp_param in bp_parameters:
            # Check if process timeout is approaching
            elapsed_time = time.time() - start_time
            if elapsed_time >= PROCESS_TIMEOUT:
                logger.warning(f"Process timeout approaching, stopping further processing")
                break

            # Try to read job data using standard path
            job_file = f'data/{setting}/({arrival_rate}, {bp_param["L"]}).csv'
            logger.info(f"Attempting to read job data from: {job_file}")
            
            job_list = None
            try:
                job_list = Read_csv.Read_csv(job_file)
                logger.info(f"Successfully read job data from {job_file}")
            except Exception as e:
                logger.error(f"Error reading job file {job_file}: {e}")
                # Try alternative file formats
                possible_job_files = [
                    f'data/{setting}/({str(arrival_rate)}, {str(bp_param["L"])}).csv',
                    f'data/{setting}/{arrival_rate}_{bp_param["L"]}.csv',
                    f'data/{setting}/({int(arrival_rate*10)}, {bp_param["L"]}).csv',
                    f'{setting}/({arrival_rate}, {bp_param["L"]}).csv'
                ]
                
                for alt_file in possible_job_files:
                    logger.info(f"Trying alternative file path: {alt_file}")
                    try:
                        job_list = Read_csv.Read_csv(alt_file)
                        logger.info(f"Successfully read from {alt_file}")
                        break
                    except Exception as e2:
                        logger.warning(f"Failed to read from {alt_file}: {e2}")
                        continue
            
            if job_list is None:
                logger.error(f"Skipping bp_parameter {bp_param} due to file read error")
                continue

            logger.info(f"Using checkpoints for setting {setting}: {CHECKPOINTS}")
            
            # Run algorithms using the checkpoint constants
            rdynamic_sqrt_2_l2_norms = run_algorithm(
                Rdynamic_sqrt_2.Rdynamic, 
                job_list, 
                CHECKPOINTS["RDYNAMIC_SQRT_2"], 
                arrival_rate,
                algorithm_name="RDYNAMIC_SQRT_2"
            )
            
            rdynamic_sqrt_6_l2_norms = run_algorithm(
                Rdynamic_sqrt_6.Rdynamic, 
                job_list, 
                CHECKPOINTS["RDYNAMIC_SQRT_6"], 
                arrival_rate,
                algorithm_name="RDYNAMIC_SQRT_6"
            )
            
            rdynamic_sqrt_8_l2_norms = run_algorithm(
                Rdynamic_sqrt_8.Rdynamic, 
                job_list, 
                CHECKPOINTS["RDYNAMIC_SQRT_8"], 
                arrival_rate,
                algorithm_name="RDYNAMIC_SQRT_8"
            )
            
            rdynamic_sqrt_10_l2_norms = run_algorithm(
                Rdynamic_sqrt_10.Rdynamic, 
                job_list, 
                CHECKPOINTS["RDYNAMIC_SQRT_10"], 
                arrival_rate,
                algorithm_name="RDYNAMIC_SQRT_10"
            )
            
            dynamic_l2_norms = run_algorithm(
                Dynamic.DYNAMIC, 
                job_list, 
                CHECKPOINTS["Dynamic"], 
                arrival_rate,
                algorithm_name="Dynamic"
            )

            # Calculate means of L2 norms with fallbacks
            rdynamic_sqrt_2_l2 = np.mean(rdynamic_sqrt_2_l2_norms) if rdynamic_sqrt_2_l2_norms else 1000.0
            rdynamic_sqrt_6_l2 = np.mean(rdynamic_sqrt_6_l2_norms) if rdynamic_sqrt_6_l2_norms else 1000.0
            rdynamic_sqrt_8_l2 = np.mean(rdynamic_sqrt_8_l2_norms) if rdynamic_sqrt_8_l2_norms else 1000.0
            rdynamic_sqrt_10_l2 = np.mean(rdynamic_sqrt_10_l2_norms) if rdynamic_sqrt_10_l2_norms else 1000.0
            dynamic_l2 = np.mean(dynamic_l2_norms) if dynamic_l2_norms else 1000.0
            
            # Find matching phase1 row - simplified matching logic
            matching_rows = None
            # Try exact match first
            try:
                matching_rows = phase1_df[
                    phase1_df['bp_parameter'].apply(
                        lambda x: isinstance(x, dict) and 
                                abs(float(x.get('L', 0)) - float(bp_param.get('L', 0))) < 0.1 and
                                abs(float(x.get('H', 0)) - float(bp_param.get('H', 0))) < 0.1
                    )
                ]
                
                if len(matching_rows) > 0:
                    logger.info(f"Found exact match for bp_parameter: {bp_param}")
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
                        logger.info(f"Found match by L value for bp_parameter: {bp_param}")
                        phase1_row = matching_rows.iloc[0].to_dict()
                    else:
                        # Use first row if no match found
                        if len(phase1_df) > 0:
                            logger.warning(f"No matching row, using first available phase1 row")
                            phase1_row = phase1_df.iloc[0].to_dict()
                        else:
                            # Create default phase1 row with warning
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
            except Exception as e:
                logger.error(f"Error in phase1 matching: {e}")
                # Create default phase1 row
                logger.warning(f"Using default phase1 values due to error")
                phase1_row = {
                    'arrival_rate': arrival_rate,
                    'bp_parameter': bp_param,
                    'RR_L2_Norm': 100.0,
                    'SRPT_L2_Norm': 100.0,
                    'SETF_L2_Norm': 100.0,
                    'FCFS_L2_Norm': 100.0,
                    'RMLF_L2_Norm': 100.0
                }
            
            # Calculate full ratios with phase1 data
            result_row = {
                'arrival_rate': arrival_rate,
                'bp_parameter': str(bp_param),
                **calculate_ratios(rdynamic_sqrt_2_l2, rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2, phase1_row)
            }
            
            # Add to results list
            results_for_all_params.append(result_row)
            logger.info(f"Added result row for bp_parameter: {bp_param}")
        
        # Save results if we have any
        if results_for_all_params:
            results_df = pd.DataFrame(results_for_all_params)
            logger.info(f"Saving {len(results_df)} results for {setting}")
            save_result = file_handler.save_results(results_df, source_folder)
            logger.info(f"Save result for {setting}: {save_result}")
            return save_result
        else:
            logger.error(f"No results to save for {setting}")
            return False
    except Exception as e:
        logger.error(f"Error in process_compare_setting for arrival_rate={arrival_rate}, setting={setting}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def random_execute_phase2(arrival_rate_default, Csettings: list):
    """Execute phase 2 and calculate ratios for random data in parallel"""
    logger.info(f"Starting parallel random phase 2 for settings: {Csettings}")
    
    # Create shared file handler before creating the pool
    file_handler = SynchronizedFileHandler()
    
    # Convert settings to strings
    string_settings = [str(setting) for setting in Csettings]
    
    # For each setting, read all arrival rates from the phase1 results file
    all_tasks = []
    for setting in string_settings:
        # Try to read the combined results file first (from execute_standard.py)
        combined_file = f"freq/freq_{setting}_combined_results.csv"
        alt_file = f"freq/{setting}_combined_results.csv"
        
        logger.info(f"Looking for combined results file: {combined_file} or {alt_file}")
        
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
            
            if 'arrival_rate' in phase1_df.columns and len(phase1_df) > 0:
                # Extract unique arrival rates and create tasks for each one
                arrival_rates = phase1_df['arrival_rate'].unique()
                logger.info(f"Found {len(arrival_rates)} arrival rates for setting {setting}: {arrival_rates}")
                
                for arr_rate in arrival_rates:
                    all_tasks.append((float(arr_rate), setting, file_handler))
            else:
                # Fall back to default arrival rate if no arrival_rates found
                logger.warning(f"No arrival_rates found in phase1 results for {setting}, using default: {arrival_rate_default}")
                all_tasks.append((float(arrival_rate_default), setting, file_handler))
                
        except Exception as e:
            logger.error(f"Error reading phase1 results for setting {setting}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fall back to default arrival rate
            all_tasks.append((float(arrival_rate_default), setting, file_handler))
    
    # Log the number of tasks
    logger.info(f"Created {len(all_tasks)} tasks in total")
    
    # Use ProcessPoolExecutor with timeout handling
    results = []
    # Reduce max_workers to avoid resource contention
    max_workers = min(len(all_tasks), max(1, mp.cpu_count() - 1))
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {executor.submit(process_single_setting, task): task for task in all_tasks}
        
        # Process completed tasks as they complete
        for future in concurrent.futures.as_completed(future_to_task):
            task = future_to_task[future]
            arr_rate, setting, _ = task
            try:
                result = future.result(timeout=PROCESS_TIMEOUT)
                if result:
                    results.append(result)
                    logger.info(f"Successfully processed arrival_rate={arr_rate}, setting={setting}")
                else:
                    logger.warning(f"Processing for arrival_rate={arr_rate}, setting={setting} returned None")
            except TimeoutError:
                logger.error(f"Timeout processing arrival_rate={arr_rate}, setting={setting}")
            except Exception as e:
                logger.error(f"Error processing arrival_rate={arr_rate}, setting={setting}: {e}")
    
    # Count successful executions
    successful = sum(1 for r in results if r)
    logger.info(f"Completed {successful}/{len(all_tasks)} tasks successfully")
    return successful > 0

def compare_execute_phase2(arrival_rate, settings: list):
    """Execute phase 2 and calculate ratios for comparison data in parallel"""
    logger.info(f"Starting parallel compare phase 2 with arrival_rate={arrival_rate}")
    
    # Create shared file handler before creating the pool
    file_handler = SynchronizedFileHandler()
    
    # Include file_handler in arguments
    args = [(arrival_rate, setting, file_handler) for setting in settings]
    
    # If there's only one setting, process it directly to avoid process creation overhead
    if len(settings) == 1:
        logger.info(f"Processing single setting directly: {settings[0]}")
        try:
            result = process_compare_setting(args[0])
            logger.info(f"Direct processing result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error processing setting {settings[0]}: {e}")
            return False
    
    # For multiple settings, use parallel processing
    results = []
    # Reduce max_workers to avoid resource contention
    max_workers = min(len(settings), max(1, mp.cpu_count() - 1))
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_setting = {executor.submit(process_compare_setting, arg): arg[1] for arg in args}
        
        # Process completed tasks as they complete
        for future in concurrent.futures.as_completed(future_to_setting):
            setting = future_to_setting[future]
            try:
                result = future.result(timeout=PROCESS_TIMEOUT)
                if result:
                    results.append(result)
                    logger.info(f"Successfully processed setting {setting}")
                else:
                    logger.warning(f"Processing for setting {setting} returned None")
            except TimeoutError:
                logger.error(f"Timeout processing setting {setting}")
            except Exception as e:
                logger.error(f"Error processing setting {setting}: {e}")
    
    # Count successful executions
    successful = sum(1 for r in results if r)
    logger.info(f"Completed {successful}/{len(settings)} settings successfully")
    return successful > 0

def execute(arrival_rate, bp_parameter):
    """Main execution function"""
    file_handler = SynchronizedFileHandler()
    return execute_phase2(arrival_rate, bp_parameter, file_handler)

def execute_random(arrival_rate_default, Csettings: list):
    """Main execution function for random data
    
    This function processes random data from multiple folders (freq_1, freq_10, etc.)
    and compares with target results from freq/freq_X_combined_results.csv
    The results are saved to freq_comp_result/all_result_freq_X_cpXX.csv
    """
    logger.info(f"Starting random execution for settings: {Csettings}")
    
    # Create shared file handler
    file_handler = SynchronizedFileHandler()
    
    # Verify CHECKPOINTS dictionary is accessible
    logger.info(f"Using checkpoints: {CHECKPOINTS}")
    # Ensure all required keys exist
    if "RDYNAMIC_SQRT_2" not in CHECKPOINTS:
        logger.warning("RDYNAMIC_SQRT_2 not found in CHECKPOINTS, setting default value of 80")
        CHECKPOINTS["RDYNAMIC_SQRT_2"] = 80
    if "RDYNAMIC_SQRT_6" not in CHECKPOINTS:
        logger.warning("RDYNAMIC_SQRT_6 not found in CHECKPOINTS, setting default value of 60")
        CHECKPOINTS["RDYNAMIC_SQRT_6"] = 60
    if "RDYNAMIC_SQRT_8" not in CHECKPOINTS:
        logger.warning("RDYNAMIC_SQRT_8 not found in CHECKPOINTS, setting default value of 80")
        CHECKPOINTS["RDYNAMIC_SQRT_8"] = 80
    if "RDYNAMIC_SQRT_10" not in CHECKPOINTS:
        logger.warning("RDYNAMIC_SQRT_10 not found in CHECKPOINTS, setting default value of 100")
        CHECKPOINTS["RDYNAMIC_SQRT_10"] = 100
    if "Dynamic" not in CHECKPOINTS:
        logger.warning("Dynamic not found in CHECKPOINTS, setting default value of 100")
        CHECKPOINTS["Dynamic"] = 100
    
    # Process each setting (freq_1, freq_10, etc.)
    for setting in Csettings:
        setting_str = str(setting)
        logger.info(f"Processing random setting: freq_{setting_str}")
        
        # Read target data from freq/freq_X_combined_results.csv
        # Note: This should contain multiple arrival rates
        target_file = f"freq/freq_{setting_str}_combined_results.csv"
        alt_target_file = f"freq/{setting_str}_combined_results.csv"
        
        target_df = None
        try:
            # Try both potential file paths
            if os.path.exists(target_file):
                target_df = pd.read_csv(target_file)
                logger.info(f"Read target file: {target_file} with {len(target_df)} rows")
            elif os.path.exists(alt_target_file):
                target_df = pd.read_csv(alt_target_file)
                logger.info(f"Read target file: {alt_target_file} with {len(target_df)} rows")
            else:
                logger.error(f"No target file found for setting freq_{setting_str}")
                continue
        except Exception as e:
            logger.error(f"Error reading target file for setting freq_{setting_str}: {e}")
            continue
        
        # Make sure we have arrival_rate in the target data
        if 'arrival_rate' not in target_df.columns:
            logger.error(f"Target file for freq_{setting_str} doesn't contain arrival_rate column")
            continue
        
        # Get all unique arrival rates from the target data
        arrival_rates = target_df['arrival_rate'].unique()
        logger.info(f"Found {len(arrival_rates)} unique arrival rates in target data: {arrival_rates}")
        
        # Create a list to store all processed results for this setting
        all_results = []
        source_folder = f'freq_{setting_str}'
        
        # Process each arrival rate
        for arr_rate in arrival_rates:
            logger.info(f"Processing arrival_rate={arr_rate} for setting freq_{setting_str}")
            
            # Get the target row for this arrival rate
            target_row = target_df[target_df['arrival_rate'] == arr_rate]
            if len(target_row) == 0:
                logger.warning(f"No target data found for arrival_rate={arr_rate}, skipping")
                continue
            target_row = target_row.iloc[0].to_dict()
            
            # FIXED: In random case, file name is just (arrival_rate).csv, not (arrival_rate, param).csv
            # Read job data from data/freq_X/(arrival_rate).csv - note the simplified naming convention
            job_file = f'data/{source_folder}/({arr_rate}).csv'
            job_list = None
            
            try:
                job_list = Read_csv.Read_csv(job_file)
                logger.info(f"Successfully read job data from {job_file}")
            except Exception as e:
                logger.error(f"Error reading {job_file}: {e}")
                # Try alternative file paths - simplified for random case
                alternatives = [
                    f'data/{source_folder}/({str(arr_rate)}).csv',
                    f'data/{source_folder}/{arr_rate}.csv',
                    f'data/{source_folder}/({int(float(arr_rate)*10)}).csv',
                    f'{source_folder}/({arr_rate}).csv'
                ]
                
                for alt_file in alternatives:
                    try:
                        job_list = Read_csv.Read_csv(alt_file)
                        logger.info(f"Successfully read job data from {alt_file}")
                        break
                    except Exception as e2:
                        pass
            
            if job_list is None:
                logger.error(f"Failed to read any job data for arrival_rate={arr_rate}, skipping")
                continue
            
            # Run algorithms with checkpoint values - add try/except to catch any algorithm failures
            logger.info(f"Running algorithms for arrival_rate={arr_rate}")
            
            try:
                # Check if CHECKPOINTS dictionary is accessible and contains required keys
                rdyn2_checkpoint = CHECKPOINTS.get("RDYNAMIC_SQRT_2", 80)
                rdyn6_checkpoint = CHECKPOINTS.get("RDYNAMIC_SQRT_6", 60)
                rdyn8_checkpoint = CHECKPOINTS.get("RDYNAMIC_SQRT_8", 80)
                rdyn10_checkpoint = CHECKPOINTS.get("RDYNAMIC_SQRT_10", 100)
                dyn_checkpoint = CHECKPOINTS.get("Dynamic", 100)
                
                logger.info(f"Using checkpoints: RDYNAMIC_SQRT_2={rdyn2_checkpoint}, RDYNAMIC_SQRT_6={rdyn6_checkpoint}, RDYNAMIC_SQRT_8={rdyn8_checkpoint}, RDYNAMIC_SQRT_10={rdyn10_checkpoint}, Dynamic={dyn_checkpoint}")
                
                # Run all dynamic variants
                rdynamic_sqrt_2_l2_norms = run_algorithm(
                    Rdynamic_sqrt_2.Rdynamic, 
                    job_list, 
                    rdyn2_checkpoint, 
                    arr_rate,
                    algorithm_name="RDYNAMIC_SQRT_2"
                )
                
                rdynamic_sqrt_6_l2_norms = run_algorithm(
                    Rdynamic_sqrt_6.Rdynamic, 
                    job_list, 
                    rdyn6_checkpoint, 
                    arr_rate,
                    algorithm_name="RDYNAMIC_SQRT_6"
                )
                
                rdynamic_sqrt_8_l2_norms = run_algorithm(
                    Rdynamic_sqrt_8.Rdynamic, 
                    job_list, 
                    rdyn8_checkpoint, 
                    arr_rate,
                    algorithm_name="RDYNAMIC_SQRT_8"
                )
                
                rdynamic_sqrt_10_l2_norms = run_algorithm(
                    Rdynamic_sqrt_10.Rdynamic, 
                    job_list, 
                    rdyn10_checkpoint, 
                    arr_rate,
                    algorithm_name="RDYNAMIC_SQRT_10"
                )
                
                dynamic_l2_norms = run_algorithm(
                    Dynamic.DYNAMIC, 
                    job_list, 
                    dyn_checkpoint, 
                    arr_rate,
                    algorithm_name="Dynamic"
                )
                
                # Calculate mean L2 norms with fallbacks
                rdynamic_sqrt_2_l2 = np.mean(rdynamic_sqrt_2_l2_norms) if rdynamic_sqrt_2_l2_norms else 1000.0
                rdynamic_sqrt_6_l2 = np.mean(rdynamic_sqrt_6_l2_norms) if rdynamic_sqrt_6_l2_norms else 1000.0
                rdynamic_sqrt_8_l2 = np.mean(rdynamic_sqrt_8_l2_norms) if rdynamic_sqrt_8_l2_norms else 1000.0
                rdynamic_sqrt_10_l2 = np.mean(rdynamic_sqrt_10_l2_norms) if rdynamic_sqrt_10_l2_norms else 1000.0
                dynamic_l2 = np.mean(dynamic_l2_norms) if dynamic_l2_norms else 1000.0
                
                # Calculate performance ratios
                result_row = {
                    'arrival_rate': float(arr_rate),
                    **calculate_ratios(rdynamic_sqrt_2_l2, rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2, target_row)
                }
                
                # Add to results collection
                all_results.append(result_row)
                logger.info(f"Added result for arrival_rate={arr_rate}")
            except Exception as e:
                logger.error(f"Error processing arrival_rate={arr_rate}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue with next arrival rate
                continue
        
        # Save all results for this setting to freq_comp_result
        if all_results:
            results_df = pd.DataFrame(all_results)
            
            # Important: Save to the freq_comp_result folder with filename all_result_freq_X_cpXX.csv
            result_folder = 'freq_comp_result'
            # Ensure directory exists
            os.makedirs(result_folder, exist_ok=True)
            
            # Get checkpoint value for file naming
            checkpoint_6 = CHECKPOINTS.get("RDYNAMIC_SQRT_6", 60)
            result_file = f'all_result_freq_{setting_str}_cp{checkpoint_6}.csv'
            
            # Final path
            output_file = os.path.join(result_folder, result_file)
            
            # Save directly to correct location
            try:
                # Create temp file for atomic write
                temp_file = f"{output_file}.tmp"
                results_df.to_csv(temp_file, index=False)
                os.replace(temp_file, output_file)
                logger.info(f"Successfully saved {len(results_df)} results to {output_file}")
            except Exception as e:
                logger.error(f"Error saving results to {output_file}: {e}")
        else:
            logger.error(f"No results to save for setting freq_{setting_str}")
    
    return True

def execute_compare(arrival_rate, settings: list):
    """Main execution function for comparison data (avg_30, avg_60, avg_90, freq)"""
    return compare_execute_phase2(arrival_rate, settings)
