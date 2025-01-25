import multiprocessing
import Read_csv
import RDYNAMIC
import logging
import time
import pandas as pd
import os
import numpy as np
from functools import partial
import ast

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_jobs(jobs, include_index=False, as_list=False):
    """Convert jobs to appropriate format"""
    if jobs and isinstance(jobs[0], (list, tuple)):
        if as_list:
            return [[float(job[0]), float(job[1])] for job in jobs]
        return [{'arrival_time': float(job[0]), 
                'job_size': float(job[1]), 
                'job_index': i} for i, job in enumerate(jobs)] if include_index else [
                {'arrival_time': float(job[0]), 
                 'job_size': float(job[1])} for job in jobs]
    return jobs

def process_scheduler_with_timeout(func, args, timeout=300000):
    """Execute scheduler with timeout"""
    try:
        with multiprocessing.Pool(1) as pool:
            result = pool.apply_async(func, args)
            return result.get(timeout=timeout)
    except multiprocessing.TimeoutError:
        logger.error(f"Timeout occurred for {func.__name__}")
        return None
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
        return None

def execute_single_run(job_list, checkpoint, arrival_rate, run_number):
    """Execute a single run of RDYNAMIC"""
    logger.info(f"Starting run {run_number} for arrival rate {arrival_rate}")
    converted_jobs = convert_jobs(job_list.copy(), include_index=True)
    
    result = process_scheduler_with_timeout(
        RDYNAMIC.RDYNAMIC,
        (converted_jobs, checkpoint, arrival_rate, 1.0, run_number)
    )
    
    if result is None:
        logger.error(f"Run {run_number} failed")
        return None
    
    return result

def execute_phase2(arrival_rate, bp_parameter, checkpoint):
    """Execute phase 2 and calculate ratios"""
    logger.info(f"Starting phase 2 with arrival_rate={arrival_rate}, checkpoint={checkpoint}")
    
    try:
        # Read phase1 results
        phase1_df = pd.read_csv(f"phase1_results_{arrival_rate}.csv")
        # Convert string representation of dictionary to actual dictionary
        phase1_df['bp_parameter'] = phase1_df['bp_parameter'].apply(ast.literal_eval)
    except Exception as e:
        logger.error(f"Error reading phase1 results: {e}")
        return None

    results = []
    for bp_param in bp_parameter:
        logger.info(f"Processing bp_parameter: {bp_param}")
        
        # Get job list
        job_list = Read_csv.Read_csv('data/'+str((arrival_rate, bp_param["L"]))+".csv")
        
        # Run RDYNAMIC 10 times and get average L2 norm
        l2_norms = []
        for run in range(1, 11):
            result = execute_single_run(job_list, checkpoint, arrival_rate, run)
            if result:
                _, l2_norm = result
                l2_norms.append(l2_norm)
        
        if l2_norms:
            rdynamic_l2 = np.mean(l2_norms)
            
            # Get phase1 results for this bp_parameter
            phase1_row = phase1_df[phase1_df['bp_parameter'].apply(lambda x: x['L'] == bp_param['L'])].iloc[0]
            
            # Create result row with ratios for each algorithm
            result_row = {
                'arrival_rate': arrival_rate,
                'bp_parameter': str(bp_param),
                'RR_ratio': rdynamic_l2 / phase1_row['RR_L2_Norm'],
                'SRPT_ratio': rdynamic_l2 / phase1_row['SRPT_L2_Norm'],
                'SETF_ratio': rdynamic_l2 / phase1_row['SETF_L2_Norm'],
                'FCFS_ratio': rdynamic_l2 / phase1_row['FCFS_L2_Norm'],
                'RMLF_ratio': rdynamic_l2 / phase1_row['RMLF_L2_Norm']
            }
            results.append(result_row)
    
    if results:
        # Save results to CSV
        results_df = pd.DataFrame(results)
        
        # If file doesn't exist, create it with header
        if not os.path.exists(f"final_result_{checkpoint}.csv"):
            results_df.to_csv(f"final_result_{checkpoint}.csv", index=False)
        else:
            # Append without header
            results_df.to_csv(f"final_result_{checkpoint}.csv", mode='a', header=False, index=False)
    
    return results
def random_execute_single_run(job_list, checkpoint, arrival_rate, run_number):
    """Execute a single run of RDYNAMIC"""
    logger.info(f"Starting run {run_number} for arrival rate {arrival_rate}")
    converted_jobs = convert_jobs(job_list.copy(), include_index=True)
    
    result = process_scheduler_with_timeout(
        RDYNAMIC.RDYNAMIC,
        (converted_jobs, checkpoint, arrival_rate, 1.0, run_number)
    )
    
    if result is None:
        logger.error(f"Run {run_number} failed")
        return None
    
    return result

def random_execute_phase2(arrival_rate, checkpoint):
    """Execute phase 2 and calculate ratios"""
    logger.info(f"Starting phase 2 with arrival_rate={arrival_rate}, checkpoint={checkpoint}")
    
    try:
        # Read phase1 results
        phase1_row = pd.read_csv(f"random_phase1_results_{arrival_rate}.csv").iloc[0]
    except Exception as e:
        logger.error(f"Error reading phase1 results: {e}")
        return None

    # Get job list
    job_list = Read_csv.Read_csv('random_data/'+'inter_arrival_'+str(arrival_rate)+".csv")
        
    # Run RDYNAMIC 10 times and get average L2 norm
    l2_norms = []
    for run in range(1, 11):
        result = execute_single_run(job_list, checkpoint, arrival_rate, run)
        if result:
            _, l2_norm = result
            l2_norms.append(l2_norm)
        
    if l2_norms:
        rdynamic_l2 = np.mean(l2_norms)
            
        # Create result row with ratios for each algorithm
        result_row = {
            'arrival_rate': arrival_rate,
            'RDYNAMIC/RR_ratio': rdynamic_l2 / phase1_row['RR_L2_Norm'],
            'RDYNAMIC/SRPT_ratio': rdynamic_l2 / phase1_row['SRPT_L2_Norm'],
            'RDYNAMIC/SETF_ratio': rdynamic_l2 / phase1_row['SETF_L2_Norm'],
            'RDYNAMIC/FCFS_ratio': rdynamic_l2 / phase1_row['FCFS_L2_Norm'],
            'RDYNAMIC/RMLF_ratio': rdynamic_l2 / phase1_row['RMLF_L2_Norm']
        }
        
        # Save results to CSV
        results_df = pd.DataFrame([result_row])
        
        # If file doesn't exist, create it with header
        if not os.path.exists(f"random_final_result_{checkpoint}.csv"):
            results_df.to_csv(f"random_final_result_{checkpoint}.csv", index=False)
        else:
            # Append without header
            results_df.to_csv(f"random_final_result_{checkpoint}.csv", mode='a', header=False, index=False)
def execute(arrival_rate, bp_parameter, checkpoint):
    """Main execution function"""
    return execute_phase2(arrival_rate, bp_parameter, int(checkpoint))

def execute_random(arrival_rate, checkpoint):
    """Main execution function"""
    return random_execute_phase2(arrival_rate, int(checkpoint))