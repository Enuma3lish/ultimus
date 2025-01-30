import multiprocessing
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

def execute_scheduler(func, args):
    """Execute scheduler without timeout"""
    try:
        return func(*args)
    except Exception as e:
        logger.error(f"Error in {func.__name__}: {e}")
        return None

def execute_single_run_rdynamic(job_list, checkpoint, arrival_rate, run_number):
    """Execute a single run of RDYNAMIC"""
    logger.info(f"Starting RDYNAMIC run {run_number} for arrival rate {arrival_rate}")
    converted_jobs = convert_jobs(job_list.copy(), include_index=True)
    
    result = execute_scheduler(
        Rdynamic.Rdynamic,
        (converted_jobs, checkpoint)
    )
    
    if result is None:
        logger.error(f"RDYNAMIC Run {run_number} failed")
        return None
    
    return result

def execute_single_run_dynamic(job_list, checkpoint, arrival_rate, run_number):
    """Execute a single run of Dynamic"""
    logger.info(f"Starting Dynamic run {run_number} for arrival rate {arrival_rate}")
    converted_jobs = convert_jobs(job_list.copy(), include_index=True)
    
    result = execute_scheduler(
        Dynamic.DYNAMIC,
        (converted_jobs, checkpoint)
    )
    
    if result is None:
        logger.error(f"Dynamic Run {run_number} failed")
        return None
    
    return result

def run_algorithm(func, job_list, checkpoint, arrival_rate, num_runs=10):
    """Run an algorithm multiple times and collect results"""
    results = []
    for run_number in range(1, num_runs + 1):
        result = func(job_list, checkpoint, arrival_rate, run_number)
        if result is not None:
            results.append(result[1])  # Append L2 norm
    return results if results else None

def execute_phase2(arrival_rate, bp_parameter, checkpoint):
    """Execute phase 2 and calculate ratios"""
    logger.info(f"Starting phase 2 with arrival_rate={arrival_rate}, checkpoint={checkpoint}")
    
    try:
        # Read phase1 results
        phase1_df = pd.read_csv(f"phase1_results_{arrival_rate}.csv")
        phase1_df['bp_parameter'] = phase1_df['bp_parameter'].apply(ast.literal_eval)
    except Exception as e:
        logger.error(f"Error reading phase1 results: {e}")
        return None

    results = []
    for bp_param in bp_parameter:
        logger.info(f"Processing bp_parameter: {bp_param}")
        
        # Get job list
        job_list = Read_csv.Read_csv('data/'+str((arrival_rate, bp_param["L"]))+".csv")
        
        # Run algorithms
        rdynamic_l2_norms = run_algorithm(execute_single_run_rdynamic, job_list, checkpoint, arrival_rate)
        dynamic_l2_norms = run_algorithm(execute_single_run_dynamic, job_list, checkpoint, arrival_rate)
        
        if rdynamic_l2_norms and dynamic_l2_norms:
            rdynamic_l2 = np.mean(rdynamic_l2_norms)
            dynamic_l2 = np.mean(dynamic_l2_norms)
            
            # Get phase1 results for this bp_parameter
            phase1_row = phase1_df[phase1_df['bp_parameter'].apply(lambda x: x['L'] == bp_param['L'])].iloc[0]
            
            # Create result row
            result_row = {
                'arrival_rate': arrival_rate,
                'bp_parameter': str(bp_param),
                'Rdynamic/RR_ratio': rdynamic_l2 / phase1_row['RR_L2_Norm'],
                'Rdynamic/SRPT_ratio': rdynamic_l2 / phase1_row['SRPT_L2_Norm'],
                'Dynamic/SRPT_ratio': dynamic_l2 / phase1_row['SRPT_L2_Norm'],
                'Rdynamic/SETF_ratio': rdynamic_l2 / phase1_row['SETF_L2_Norm'],
                'Rdynamic/FCFS_ratio': rdynamic_l2 / phase1_row['FCFS_L2_Norm'],
                'Rdynamic/RMLF_ratio': rdynamic_l2 / phase1_row['RMLF_L2_Norm'],
                'Rdynamic/Dynamic_ratio': rdynamic_l2 / dynamic_l2
            }
            results.append(result_row)
    
    if results:
        results_df = pd.DataFrame(results)
        if not os.path.exists(f"final_result_{checkpoint}.csv"):
            results_df.to_csv(f"final_result_{checkpoint}.csv", index=False)
        else:
            results_df.to_csv(f"final_result_{checkpoint}.csv", mode='a', header=False, index=False)

def random_execute_phase2(arrival_rate, checkpoint):
    """Execute phase 2 and calculate ratios for random data"""
    logger.info(f"Starting phase 2 with arrival_rate={arrival_rate}, checkpoint={checkpoint}")
    Csettings = [1,25,50,100,200,300,400,500,1000,2000,3000,4000,5000,10000]
    for i in Csettings:
        try:
            phase1_row = pd.read_csv(f"{i}_random_phase1_results_{arrival_rate}.csv").iloc[0]
        except Exception as e:
            logger.error(f"Error reading phase1 results: {e}")
            return None

        job_list = Read_csv.Read_csv(f'{i}_random_data/'+'inter_arrival_'+str(arrival_rate)+".csv")
    
         # Run algorithms
        rdynamic_l2_norms = run_algorithm(execute_single_run_rdynamic, job_list, checkpoint, arrival_rate)
        dynamic_l2_norms = run_algorithm(execute_single_run_dynamic, job_list, checkpoint, arrival_rate)

        if rdynamic_l2_norms and dynamic_l2_norms:
            rdynamic_l2 = np.mean(rdynamic_l2_norms)
            dynamic_l2 = np.mean(dynamic_l2_norms)
        
            result_row = {
                'arrival_rate': arrival_rate,
                'Rdynamic/RR_ratio': rdynamic_l2 / phase1_row['RR_L2_Norm'],
                'Rdynamic/SRPT_ratio': rdynamic_l2 / phase1_row['SRPT_L2_Norm'],
                'Dynamic/SRPT_ratio' : dynamic_l2 / phase1_row['SRPT_L2_Norm'],
                'Rdynamic/SETF_ratio': rdynamic_l2 / phase1_row['SETF_L2_Norm'],
                'Rdynamic/FCFS_ratio': rdynamic_l2 / phase1_row['FCFS_L2_Norm'],
                'Rdynamic/RMLF_ratio': rdynamic_l2 / phase1_row['RMLF_L2_Norm'],
                'Rdynamic/Dynamic_ratio': rdynamic_l2 / dynamic_l2
            }
        
            results_df = pd.DataFrame([result_row])
            if not os.path.exists(f"{i}_random_final_result_{checkpoint}.csv"):
                results_df.to_csv(f"{i}_random_final_result_{checkpoint}.csv", index=False)
            else:
                results_df.to_csv(f"{i}_random_final_result_{checkpoint}.csv", mode='a', header=False, index=False)

def execute(arrival_rate, bp_parameter, checkpoint):
    """Main execution function"""
    return execute_phase2(arrival_rate, bp_parameter, int(checkpoint))

def execute_random(arrival_rate, checkpoint):
    """Main execution function for random data"""
    return random_execute_phase2(arrival_rate, int(checkpoint))