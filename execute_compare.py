import multiprocessing as mp
from multiprocessing import Manager
import Read_csv
import Rdynamic
import Dynamic
import logging
import time
import pandas as pd
import os
import numpy as np
from functools import partial
import ast
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SynchronizedFileHandler:
    """Thread-safe file handler for parallel processing"""
    def __init__(self):
        manager = Manager()
        self._lock = manager.Lock()
    
    @staticmethod
    def ensure_directory_exists(directory_path):
        """Create directory if it doesn't exist"""
        Path(directory_path).mkdir(parents=True, exist_ok=True)
    
    def save_results(self, results_df, source_folder, checkpoint, mode='w'):
        """Thread-safe method to save results"""
        with self._lock:
            try:
                # Determine result folder name based on source folder
                if source_folder == 'data':
                    result_folder = 'result'
                    result_file = 'all_result.csv'
                else:
                    prefix = source_folder.split('_')[0]
                    result_folder = f'{prefix}_random_result'
                    result_file = f'all_result_{prefix}.csv'
                
                # Create result folder
                self.ensure_directory_exists(result_folder)
                
                # Save checkpoint specific results
                checkpoint_file = os.path.join(result_folder, f"result_{checkpoint}.csv")
                temp_checkpoint = f"{checkpoint_file}.tmp"
                
                if os.path.exists(checkpoint_file):
                    existing_df = pd.read_csv(checkpoint_file)
                    existing_df = existing_df[~existing_df['arrival_rate'].isin(results_df['arrival_rate'])]
                    combined_df = pd.concat([existing_df, results_df], ignore_index=True)
                    combined_df = combined_df.sort_values('arrival_rate')
                else:
                    combined_df = results_df.copy()
                
                # Atomic write to checkpoint file
                combined_df.to_csv(temp_checkpoint, index=False)
                os.replace(temp_checkpoint, checkpoint_file)
                
                # Update combined results file
                combined_file = os.path.join(result_folder, result_file)
                temp_combined = f"{combined_file}.tmp"
                
                if os.path.exists(combined_file):
                    all_results_df = pd.read_csv(combined_file)
                    all_results_df = all_results_df[~all_results_df['arrival_rate'].isin(results_df['arrival_rate'])]
                    all_results_df = pd.concat([all_results_df, results_df], ignore_index=True)
                else:
                    all_results_df = results_df.copy()
                
                all_results_df = all_results_df.sort_values('arrival_rate')
                
                # Atomic write to combined file
                all_results_df.to_csv(temp_combined, index=False)
                os.replace(temp_combined, combined_file)
                
                logger.info(f"Results saved to checkpoint file: {checkpoint_file}")
                logger.info(f"Results saved to combined file: {combined_file}")
                return True
                
            except Exception as e:
                logger.error(f"Error saving results: {e}")
                return False
    
    def read_phase1_results(self, arrival_rate, is_random=False, prefix=''):
        """Thread-safe method to read phase1 results"""
        with self._lock:
            try:
                file_name = f"{prefix}_random_phase1_results_{arrival_rate}.csv" if is_random else f"phase1_results_{arrival_rate}.csv"
                df = pd.read_csv(file_name)
                if not is_random:
                    df['bp_parameter'] = df['bp_parameter'].apply(ast.literal_eval)
                return df
            except Exception as e:
                logger.error(f"Error reading phase1 results: {e}")
                return None

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

def execute_scheduler(func, args):
    """Execute scheduler without timeout"""
    try:
        return func(*args)
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
        return None

def execute_single_run(algorithm_func, job_list, checkpoint, arrival_rate, run_number, algorithm_name):
    """Execute a single run of an algorithm"""
    logger.info(f"Starting {algorithm_name} run {run_number} for arrival rate {arrival_rate}")
    converted_jobs = convert_jobs(job_list.copy(), include_index=True)
    
    result = execute_scheduler(algorithm_func, (converted_jobs, checkpoint))
    
    if result is None:
        logger.error(f"{algorithm_name} Run {run_number} failed")
        return None
    
    return result

def run_algorithm(algorithm_func, job_list, checkpoint, arrival_rate, num_runs=3, algorithm_name="Algorithm"):
    """Run an algorithm multiple times and collect results"""
    results = []
    for run_number in range(1, num_runs + 1):
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
    return results if results else None

def calculate_ratios(rdynamic_l2, dynamic_l2, phase1_row):
    """Calculate performance ratios"""
    return {
        'Rdynamic/RR_ratio': rdynamic_l2 / phase1_row['RR_L2_Norm'],
        'Rdynamic/SRPT_ratio': rdynamic_l2 / phase1_row['SRPT_L2_Norm'],
        'Dynamic/SRPT_ratio': dynamic_l2 / phase1_row['SRPT_L2_Norm'],
        'Rdynamic/SETF_ratio': rdynamic_l2 / phase1_row['SETF_L2_Norm'],
        'Rdynamic/FCFS_ratio': rdynamic_l2 / phase1_row['FCFS_L2_Norm'],
        'Rdynamic/RMLF_ratio': rdynamic_l2 / phase1_row['RMLF_L2_Norm'],
        'Rdynamic/Dynamic_ratio': rdynamic_l2 / dynamic_l2
    }

def execute_phase2(arrival_rate, bp_parameter, checkpoint, file_handler):
    """Execute phase 2 and calculate ratios"""
    logger.info(f"Starting phase 2 with arrival_rate={arrival_rate}, checkpoint={checkpoint}")
    logger.info(f"Number of bp_parameters to process: {len(bp_parameter)}")
    
    # Read phase1 results
    phase1_df = file_handler.read_phase1_results(arrival_rate)
    if phase1_df is None:
        return None

    results = []
    for bp_param in bp_parameter:
        logger.info(f"Processing bp_parameter: {bp_param}")
        
        # Get job list
        job_list = Read_csv.Read_csv('data/'+str((arrival_rate, bp_param["L"]))+".csv")
        
        # Run algorithms
        rdynamic_l2_norms = run_algorithm(
            Rdynamic.Rdynamic, 
            job_list, 
            checkpoint, 
            arrival_rate,
            algorithm_name="RDYNAMIC"
        )
        dynamic_l2_norms = run_algorithm(
            Dynamic.DYNAMIC, 
            job_list, 
            checkpoint, 
            arrival_rate,
            algorithm_name="Dynamic"
        )
        
        if rdynamic_l2_norms and dynamic_l2_norms:
            rdynamic_l2 = np.mean(rdynamic_l2_norms)
            dynamic_l2 = np.mean(dynamic_l2_norms)
            
            # Get phase1 results for this bp_parameter
            phase1_row = phase1_df[phase1_df['bp_parameter'].apply(lambda x: x['L'] == bp_param['L'])].iloc[0]
            
            # Calculate ratios and include L2 norms
            result_row = {
                'arrival_rate': arrival_rate,
                'bp_parameter': str(bp_param),
                **calculate_ratios(rdynamic_l2, dynamic_l2, phase1_row)
            }
            results.append(result_row)
    
    if results:
        results_df = pd.DataFrame(results)
        # Reorder columns to match desired format
        column_order = [
            'arrival_rate', 
            'bp_parameter',
            'Rdynamic/RR_ratio',
            'Rdynamic/SRPT_ratio',
            'Dynamic/SRPT_ratio',
            'Rdynamic/SETF_ratio',
            'Rdynamic/FCFS_ratio',
            'Rdynamic/RMLF_ratio',
            'Rdynamic/Dynamic_ratio'
        ]
        results_df = results_df[column_order]
        file_handler.save_results(
            results_df, 
            'data',  # Source folder
            checkpoint,
            mode='a'
        )

def process_single_setting(args):
    """Process a single random setting with synchronized file handling"""
    arrival_rate, checkpoint, setting, file_handler = args
    
    # Read phase1 results
    phase1_row = file_handler.read_phase1_results(arrival_rate, is_random=True, prefix=setting)
    if phase1_row is None:
        return None

    # Get job list
    source_folder = f'{setting}_random_data'
    job_list = Read_csv.Read_csv(f'{source_folder}/inter_arrival_{arrival_rate}.csv')

    # Run algorithms
    rdynamic_l2_norms = run_algorithm(
        Rdynamic.Rdynamic, 
        job_list, 
        checkpoint, 
        arrival_rate,
        algorithm_name="RDYNAMIC"
    )
    dynamic_l2_norms = run_algorithm(
        Dynamic.DYNAMIC, 
        job_list, 
        checkpoint, 
        arrival_rate,
        algorithm_name="Dynamic"
    )

    if rdynamic_l2_norms and dynamic_l2_norms:
        rdynamic_l2 = np.mean(rdynamic_l2_norms)
        dynamic_l2 = np.mean(dynamic_l2_norms)
    
        # For random data, we don't include bp_parameter
        result_row = {
            'arrival_rate': arrival_rate,
            **calculate_ratios(rdynamic_l2, dynamic_l2, phase1_row.iloc[0])
        }
    
        results_df = pd.DataFrame([result_row])
        return file_handler.save_results(
            results_df,
            source_folder,
            checkpoint,
            mode='a'
        )
    return None

def random_execute_phase2(arrival_rate, checkpoint, Csettings: list):
    """Execute phase 2 and calculate ratios for random data in parallel"""
    logger.info(f"Starting parallel random phase 2 with arrival_rate={arrival_rate}, checkpoint={checkpoint}")
    
    # Create shared file handler before creating the pool
    file_handler = SynchronizedFileHandler()
    
    # Create a pool of workers
    num_cores = mp.cpu_count()
    pool = mp.Pool(processes=min(len(Csettings), num_cores))
    
    try:
        # Include file_handler in arguments
        args = [(arrival_rate, checkpoint, setting, file_handler) for setting in Csettings]
        
        # Execute processes in parallel
        results = pool.map(process_single_setting, args)
        
        # Close the pool and wait for all processes to complete
        pool.close()
        pool.join()
        
        # Count successful executions
        successful = sum(1 for r in results if r)
        logger.info(f"Completed {successful}/{len(Csettings)} settings successfully")
        
    except Exception as e:
        logger.error(f"Error in parallel execution: {e}")
        pool.terminate()
        raise
    finally:
        pool.join()

def execute(arrival_rate, bp_parameter, checkpoint):
    """Main execution function"""
    file_handler = SynchronizedFileHandler()
    return execute_phase2(arrival_rate, bp_parameter, int(checkpoint), file_handler)

def execute_random(arrival_rate, checkpoint, Csettings: list):
    """Main execution function for random data"""
    return random_execute_phase2(arrival_rate, int(checkpoint), Csettings)