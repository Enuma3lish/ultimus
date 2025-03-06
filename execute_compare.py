import multiprocessing as mp
from multiprocessing import Manager
import Read_csv
import Rdynamic_sqrt_6, Rdynamic_sqrt_8, Rdynamic_sqrt_10
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
                
                # Create result folder
                self.ensure_directory_exists(result_folder)
                
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
                
                logger.info(f"Results saved to combined file: {combined_file}")
                return True
                
            except Exception as e:
                logger.error(f"Error saving results: {e}")
                return False
    
    def read_phase1_results(self, arrival_rate, is_random=False, prefix=''):
        """Thread-safe method to read phase1 results"""
        with self._lock:
            try:
                if is_random:
                    # For random data with freq_X format
                    file_name = f"phase1/phase1_results_freq_{prefix}_{arrival_rate}.csv"
                elif prefix.startswith('avg_'):
                    # Handle avg_30, avg_60, avg_90 files
                    file_name = f"phase1/phase1_results_{prefix}_{arrival_rate}.csv"
                elif prefix == 'freq':
                    # Special case for freq
                    file_name = f"phase1/phase1_results_{prefix}_{arrival_rate}.csv"
                else:
                    file_name = f"phase1/phase1_results_{arrival_rate}.csv"
                
                logger.info(f"Reading phase1 results from: {file_name}")
                
                # Try to read the file, and if it doesn't exist, try alternative paths
                try:
                    df = pd.read_csv(file_name)
                except Exception as file_error:
                    logger.warning(f"Could not read {file_name}: {file_error}")
                    
                    # Try alternative paths based on the type of data
                    alternatives = []
                    if is_random:
                        alternatives = [
                            f"phase1/phase1_results_freq_{prefix}_{arrival_rate}.csv",
                            f"phase1/phase1_results_freq{prefix}_{arrival_rate}.csv",  # without underscore
                            f"phase1/phase1_results_{prefix}_random_{arrival_rate}.csv",  # old format
                            f"phase1/freq_{prefix}_phase1_results_{arrival_rate}.csv"  # another possible format
                        ]
                    
                    for alt_file in alternatives:
                        logger.info(f"Trying alternative phase1 file: {alt_file}")
                        try:
                            df = pd.read_csv(alt_file)
                            logger.info(f"Successfully read from {alt_file}")
                            break
                        except Exception:
                            continue
                    else:
                        # Re-raise if no alternative worked
                        raise Exception(f"Could not read phase1 results from any alternative path for {file_name}")
                
                # Parse bp_parameter if needed
                if not is_random and prefix not in ['freq', 'avg_30', 'avg_60', 'avg_90']:
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

def calculate_ratios(rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2, phase1_row):
    """Calculate performance ratios between all algorithms"""
    ratios = {}
    
    # Rdynamic_sqrt_6 ratios
    ratios.update({
        'Rdynamic_sqrt_6/RR_ratio': rdynamic_sqrt_6_l2 / phase1_row['RR_L2_Norm'],
        'Rdynamic_sqrt_6/SRPT_ratio': rdynamic_sqrt_6_l2 / phase1_row['SRPT_L2_Norm'],
        'Rdynamic_sqrt_6/SETF_ratio': rdynamic_sqrt_6_l2 / phase1_row['SETF_L2_Norm'],
        'Rdynamic_sqrt_6/FCFS_ratio': rdynamic_sqrt_6_l2 / phase1_row['FCFS_L2_Norm'],
        'Rdynamic_sqrt_6/RMLF_ratio': rdynamic_sqrt_6_l2 / phase1_row['RMLF_L2_Norm'],
        'Rdynamic_sqrt_6/Dynamic_ratio': rdynamic_sqrt_6_l2 / dynamic_l2
    })
    
    # Rdynamic_sqrt_8 ratios
    ratios.update({
        'Rdynamic_sqrt_8/RR_ratio': rdynamic_sqrt_8_l2 / phase1_row['RR_L2_Norm'],
        'Rdynamic_sqrt_8/SRPT_ratio': rdynamic_sqrt_8_l2 / phase1_row['SRPT_L2_Norm'],
        'Rdynamic_sqrt_8/SETF_ratio': rdynamic_sqrt_8_l2 / phase1_row['SETF_L2_Norm'],
        'Rdynamic_sqrt_8/FCFS_ratio': rdynamic_sqrt_8_l2 / phase1_row['FCFS_L2_Norm'],
        'Rdynamic_sqrt_8/RMLF_ratio': rdynamic_sqrt_8_l2 / phase1_row['RMLF_L2_Norm'],
        'Rdynamic_sqrt_8/Dynamic_ratio': rdynamic_sqrt_8_l2 / dynamic_l2
    })
    
    # Rdynamic_sqrt_10 ratios
    ratios.update({
        'Rdynamic_sqrt_10/RR_ratio': rdynamic_sqrt_10_l2 / phase1_row['RR_L2_Norm'],
        'Rdynamic_sqrt_10/SRPT_ratio': rdynamic_sqrt_10_l2 / phase1_row['SRPT_L2_Norm'],
        'Rdynamic_sqrt_10/SETF_ratio': rdynamic_sqrt_10_l2 / phase1_row['SETF_L2_Norm'],
        'Rdynamic_sqrt_10/FCFS_ratio': rdynamic_sqrt_10_l2 / phase1_row['FCFS_L2_Norm'],
        'Rdynamic_sqrt_10/RMLF_ratio': rdynamic_sqrt_10_l2 / phase1_row['RMLF_L2_Norm'],
        'Rdynamic_sqrt_10/Dynamic_ratio': rdynamic_sqrt_10_l2 / dynamic_l2
    })
    
    # Dynamic ratio
    ratios.update({
        'Dynamic/SRPT_ratio': dynamic_l2 / phase1_row['SRPT_L2_Norm']
    })
    
    # Comparisons between Rdynamic variants
    ratios.update({
        'Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio': rdynamic_sqrt_6_l2 / rdynamic_sqrt_8_l2,
        'Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio': rdynamic_sqrt_6_l2 / rdynamic_sqrt_10_l2,
        'Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio': rdynamic_sqrt_8_l2 / rdynamic_sqrt_10_l2
    })
    
    return ratios

def calculate_ratios_without_phase1(rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2):
    """Calculate performance ratios between algorithms without requiring phase1 results"""
    ratios = {}
    
    # Ratios between Dynamic and Rdynamic variants
    ratios.update({
        'Rdynamic_sqrt_6/Dynamic_ratio': rdynamic_sqrt_6_l2 / dynamic_l2,
        'Rdynamic_sqrt_8/Dynamic_ratio': rdynamic_sqrt_8_l2 / dynamic_l2,
        'Rdynamic_sqrt_10/Dynamic_ratio': rdynamic_sqrt_10_l2 / dynamic_l2
    })
    
    # Comparisons between Rdynamic variants
    ratios.update({
        'Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio': rdynamic_sqrt_6_l2 / rdynamic_sqrt_8_l2,
        'Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio': rdynamic_sqrt_6_l2 / rdynamic_sqrt_10_l2,
        'Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio': rdynamic_sqrt_8_l2 / rdynamic_sqrt_10_l2
    })
    
    # Add raw L2 norms for reference
    ratios.update({
        'Rdynamic_sqrt_6_L2': rdynamic_sqrt_6_l2,
        'Rdynamic_sqrt_8_L2': rdynamic_sqrt_8_l2,
        'Rdynamic_sqrt_10_L2': rdynamic_sqrt_10_l2,
        'Dynamic_L2': dynamic_l2
    })
    
    return ratios

def execute_phase2(arrival_rate, bp_parameter, file_handler):
    """Execute phase 2 and calculate ratios"""
    logger.info(f"Starting phase 2 with arrival_rate={arrival_rate}")
    logger.info(f"Number of bp_parameters to process: {len(bp_parameter)}")
    
    # Read phase1 results
    phase1_df = file_handler.read_phase1_results(arrival_rate)
    if phase1_df is None:
        return None

    results = []
    for bp_param in bp_parameter:
        logger.info(f"Processing bp_parameter: {bp_param}")
        
        # Get job list with the correct file naming pattern
        job_file = f'data/({arrival_rate}, {bp_param["L"]}).csv'
        logger.info(f"Reading job data from: {job_file}")
        job_list = Read_csv.Read_csv(job_file)
        
        # Run algorithms
        rdynamic_sqrt_6_l2_norms = run_algorithm(
            Rdynamic_sqrt_6.Rdynamic, 
            job_list, 
            6, 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_6"
        )
        
        rdynamic_sqrt_8_l2_norms = run_algorithm(
            Rdynamic_sqrt_8.Rdynamic, 
            job_list, 
            8, 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_8"
        )
        
        rdynamic_sqrt_10_l2_norms = run_algorithm(
            Rdynamic_sqrt_10.Rdynamic, 
            job_list, 
            10, 
            arrival_rate,
            algorithm_name="RDYNAMIC_SQRT_10"
        )
        
        dynamic_l2_norms = run_algorithm(
            Dynamic.DYNAMIC, 
            job_list, 
            6,  # Using 6 as default checkpoint for Dynamic
            arrival_rate,
            algorithm_name="Dynamic"
        )
        
        if (rdynamic_sqrt_6_l2_norms and rdynamic_sqrt_8_l2_norms and 
            rdynamic_sqrt_10_l2_norms and dynamic_l2_norms):
            
            rdynamic_sqrt_6_l2 = np.mean(rdynamic_sqrt_6_l2_norms)
            rdynamic_sqrt_8_l2 = np.mean(rdynamic_sqrt_8_l2_norms)
            rdynamic_sqrt_10_l2 = np.mean(rdynamic_sqrt_10_l2_norms)
            dynamic_l2 = np.mean(dynamic_l2_norms)
            
            # Get phase1 results for this bp_parameter
            phase1_row = phase1_df[phase1_df['bp_parameter'].apply(lambda x: x['L'] == bp_param['L'])].iloc[0]
            
            # Calculate ratios and include L2 norms
            result_row = {
                'arrival_rate': arrival_rate,
                'bp_parameter': str(bp_param),
                **calculate_ratios(rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2, phase1_row)
            }
            results.append(result_row)
    
    if results:
        results_df = pd.DataFrame(results)
        file_handler.save_results(
            results_df, 
            'data'  # Source folder
        )

def process_single_setting(args):
    """Process a single random setting with synchronized file handling"""
    arrival_rate, setting, file_handler = args
    
    # For random data, we'll skip phase1 results since they don't exist
    # The random folder structure is directly like freq_1, not {setting}_random_data
    source_folder = f'freq_{setting}'
    job_file = f'data/{source_folder}/({arrival_rate}).csv'
    logger.info(f"Reading random job data from: {job_file}")
    
    try:
        job_list = Read_csv.Read_csv(job_file)
    except Exception as e:
        # Try alternatives if the first attempt fails
        alternatives = [
            f'data/{source_folder}/({str(arrival_rate)}).csv',
            f'data/{source_folder}/inter_arrival_{arrival_rate}.csv'
        ]
        
        job_list = None
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

    # Run algorithms
    rdynamic_sqrt_6_l2_norms = run_algorithm(
        Rdynamic_sqrt_6.Rdynamic, 
        job_list, 
        6, 
        arrival_rate,
        algorithm_name="RDYNAMIC_SQRT_6"
    )
    
    rdynamic_sqrt_8_l2_norms = run_algorithm(
        Rdynamic_sqrt_8.Rdynamic, 
        job_list, 
        8, 
        arrival_rate,
        algorithm_name="RDYNAMIC_SQRT_8"
    )
    
    rdynamic_sqrt_10_l2_norms = run_algorithm(
        Rdynamic_sqrt_10.Rdynamic, 
        job_list, 
        10, 
        arrival_rate,
        algorithm_name="RDYNAMIC_SQRT_10"
    )
    
    dynamic_l2_norms = run_algorithm(
        Dynamic.DYNAMIC, 
        job_list, 
        6,  # Using 6 as default checkpoint for Dynamic
        arrival_rate,
        algorithm_name="Dynamic"
    )

    if (rdynamic_sqrt_6_l2_norms and rdynamic_sqrt_8_l2_norms and 
        rdynamic_sqrt_10_l2_norms and dynamic_l2_norms):
        
        rdynamic_sqrt_6_l2 = np.mean(rdynamic_sqrt_6_l2_norms)
        rdynamic_sqrt_8_l2 = np.mean(rdynamic_sqrt_8_l2_norms)
        rdynamic_sqrt_10_l2 = np.mean(rdynamic_sqrt_10_l2_norms)
        dynamic_l2 = np.mean(dynamic_l2_norms)
    
        # For random data, we use the version without phase1 results
        result_row = {
            'arrival_rate': arrival_rate,
            **calculate_ratios_without_phase1(rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2)
        }
    
        results_df = pd.DataFrame([result_row])
        return file_handler.save_results(
            results_df,
            source_folder
        )
    return None

def process_compare_setting(args):
    """Process a compare setting (avg_30, avg_60, avg_90, freq)"""
    arrival_rate, setting, file_handler = args
    
    # Read phase1 results with the appropriate prefix
    phase1_row = file_handler.read_phase1_results(arrival_rate, is_random=False, prefix=setting)
    if phase1_row is None:
        return None

    # Get bp_parameters for this setting and arrival rate
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
        # Special case for freq - use a default L value if needed
        # Adjust this based on your actual freq data structure
        bp_parameters = [{"L": 10.0, "H": pow(2, 10)}]  # Example default
    else:
        logger.error(f"Unknown setting: {setting}")
        return None
    
    source_folder = setting
    
    # Process each bp_parameter and create an average result
    results_for_all_params = []
    
    for bp_param in bp_parameters:
        # Construct the job file path based on the correct naming convention
        job_file = f'data/{setting}/({arrival_rate}, {bp_param["L"]}).csv'
        logger.info(f"Reading job data from: {job_file}")
        
        try:
            job_list = Read_csv.Read_csv(job_file)

                # Run algorithms
            rdynamic_sqrt_6_l2_norms = run_algorithm(
                Rdynamic_sqrt_6.Rdynamic, 
                job_list, 
                6, 
                arrival_rate,
                algorithm_name="RDYNAMIC_SQRT_6"
            )
            
            rdynamic_sqrt_8_l2_norms = run_algorithm(
                Rdynamic_sqrt_8.Rdynamic, 
                job_list, 
                8, 
                arrival_rate,
                algorithm_name="RDYNAMIC_SQRT_8"
            )
            
            rdynamic_sqrt_10_l2_norms = run_algorithm(
                Rdynamic_sqrt_10.Rdynamic, 
                job_list, 
                10, 
                arrival_rate,
                algorithm_name="RDYNAMIC_SQRT_10"
            )
            
            dynamic_l2_norms = run_algorithm(
                Dynamic.DYNAMIC, 
                job_list, 
                6,  # Using 6 as default checkpoint for Dynamic
                arrival_rate,
                algorithm_name="Dynamic"
            )

            if (rdynamic_sqrt_6_l2_norms and rdynamic_sqrt_8_l2_norms and 
                rdynamic_sqrt_10_l2_norms and dynamic_l2_norms):
                
                rdynamic_sqrt_6_l2 = np.mean(rdynamic_sqrt_6_l2_norms)
                rdynamic_sqrt_8_l2 = np.mean(rdynamic_sqrt_8_l2_norms)
                rdynamic_sqrt_10_l2 = np.mean(rdynamic_sqrt_10_l2_norms)
                dynamic_l2 = np.mean(dynamic_l2_norms)
            
                # Include bp_parameter in results for this setting
                result_row = {
                    'arrival_rate': arrival_rate,
                    'bp_parameter': str(bp_param),
                    **calculate_ratios(rdynamic_sqrt_6_l2, rdynamic_sqrt_8_l2, rdynamic_sqrt_10_l2, dynamic_l2, phase1_row.iloc[0])
                }
                results_for_all_params.append(result_row)
            
        except Exception as e:
            logger.error(f"Error processing file {job_file}: {e}")
            continue
    
    if results_for_all_params:
        results_df = pd.DataFrame(results_for_all_params)
        return file_handler.save_results(
            results_df,
            source_folder
        )
    return None

def random_execute_phase2(arrival_rate, Csettings: list):
    """Execute phase 2 and calculate ratios for random data in parallel"""
    logger.info(f"Starting parallel random phase 2 with arrival_rate={arrival_rate}")
    logger.info(f"Random settings to process: {Csettings}")
    
    # Create shared file handler before creating the pool
    file_handler = SynchronizedFileHandler()
    
    # Create a pool of workers
    num_cores = mp.cpu_count()
    pool = mp.Pool(processes=min(len(Csettings), num_cores))
    
    try:
        # Convert the settings to strings for processing
        # Each setting is a power of 2 (1, 2, 4, 8, 16, etc.)
        string_settings = [str(setting) for setting in Csettings]
        args = [(arrival_rate, setting, file_handler) for setting in string_settings]
        
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

def compare_execute_phase2(arrival_rate, settings: list):
    """Execute phase 2 and calculate ratios for comparison data in parallel"""
    logger.info(f"Starting parallel compare phase 2 with arrival_rate={arrival_rate}")
    
    # Create shared file handler before creating the pool
    file_handler = SynchronizedFileHandler()
    
    # Create a pool of workers
    num_cores = mp.cpu_count()
    pool = mp.Pool(processes=min(len(settings), num_cores))
    
    try:
        # Include file_handler in arguments
        args = [(arrival_rate, setting, file_handler) for setting in settings]
        
        # Execute processes in parallel
        results = pool.map(process_compare_setting, args)
        
        # Close the pool and wait for all processes to complete
        pool.close()
        pool.join()
        # Count successful executions
        successful = sum(1 for r in results if r)
        logger.info(f"Completed {successful}/{len(settings)} settings successfully")
        
    except Exception as e:
        logger.error(f"Error in parallel execution: {e}")
        pool.terminate()
        raise
    finally:
        pool.join()

def execute(arrival_rate, bp_parameter):
    """Main execution function"""
    file_handler = SynchronizedFileHandler()
    return execute_phase2(arrival_rate, bp_parameter, file_handler)

def execute_random(arrival_rate, Csettings: list):
    """Main execution function for random data"""
    return random_execute_phase2(arrival_rate, Csettings)

def execute_compare(arrival_rate, settings: list):
    """Main execution function for comparison data (avg_30, avg_60, avg_90, freq)"""
    return compare_execute_phase2(arrival_rate, settings)