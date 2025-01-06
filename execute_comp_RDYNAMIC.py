import multiprocessing
import Read_csv
import RDYNAMIC
import logging
import time
import pandas as pd
import os
from functools import partial

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

def calculate_average_ratios(checkpoint):
    """Calculate average ratios from multiple runs"""
    logger.info(f"Calculating average ratios for checkpoint {checkpoint}")
    all_ratios = []
    
    # Read all ratio files for this checkpoint
    for run in range(1, 11):
        filename = f"log/{run}ratio@{checkpoint}.csv"
        try:
            if os.path.exists(filename):
                df = pd.read_csv(filename)
                all_ratios.append(df)
        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
            continue
    
    if not all_ratios:
        logger.error(f"No ratio files found for checkpoint {checkpoint}")
        return
    
    # Combine and calculate averages
    combined = pd.concat(all_ratios, ignore_index=True)
    averaged = combined.groupby(['checkpoint', 'arrival_rate', 'bp_parameter']).agg({
        'rmlf_ratio': 'mean',
        'fcfs_ratio': 'mean'
    }).reset_index()
    
    # Round the ratios to 1 decimal place
    averaged['rmlf_ratio'] = averaged['rmlf_ratio'].round(1)
    averaged['fcfs_ratio'] = averaged['fcfs_ratio'].round(1)
    
    # Save the averaged results
    output_file = f"log/ratio{checkpoint}.csv"
    averaged.to_csv(output_file, index=False)
    logger.info(f"Averaged ratios saved to {output_file}")
    return averaged

def execute_single_run(job_list, checkpoint, arrival_rate, bp_param, run_number):
    """Execute a single run of RDYNAMIC"""
    logger.info(f"Starting run {run_number} for arrival rate {arrival_rate}")
    converted_jobs = convert_jobs(job_list.copy(), include_index=True)
    
    result = process_scheduler_with_timeout(
        RDYNAMIC.RDYNAMIC,
        (converted_jobs, checkpoint, arrival_rate, bp_param, 1.0, run_number)
    )
    
    if result is None:
        logger.error(f"Run {run_number} failed")
        return None
    
    return result

def execute_phase2(Arrival_rate, bp_parameter, checkpoint):
    """Execute multiple runs of RDYNAMIC"""
    logger.info(f"Starting phase 2 with Arrival_rate={Arrival_rate}, checkpoint={checkpoint}")
    
    # Ensure log directory exists
    os.makedirs('log', exist_ok=True)
    
    results = []
    for bp_param in bp_parameter:
        logger.info(f"Processing bp_parameter: {bp_param}")
        
        # Get job list
        job_list = Read_csv.Read_csv('data/'+str((Arrival_rate, bp_param["L"]))+".csv")
        
        # Execute 10 runs
        for run in range(1, 11):
            result = execute_single_run(job_list, checkpoint, Arrival_rate, bp_param, run)
            if result:
                avg_flow_time, l2_norm = result
                results.append({
                    "arrival_rate": Arrival_rate,
                    "bp_parameter": bp_param,
                    "run": run,
                    "avg_flow_time": avg_flow_time,
                    "l2_norm": l2_norm
                })
    
    # Calculate and save average ratios
    calculate_average_ratios(checkpoint)
    
    return results

def execute(Arrival_rate, bp_parameter, checkpoint):
    """Main execution function"""
    return execute_phase2(Arrival_rate, bp_parameter, int(checkpoint))