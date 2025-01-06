import multiprocessing
import Read_csv
import RR, SRPT, SETF, FCFS, RMLF
import logging
import time
import pandas as pd
import numpy as np
from functools import partial

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_jobs(jobs, include_index=False, as_list=False):
    """
    Convert jobs to appropriate format based on algorithm requirements
    as_list: True returns [[arrival_time, job_size], ...] format for RR, SETF
    include_index: True includes job_index for RDYNAMIC
    """
    if jobs and isinstance(jobs[0], (list, tuple)):
        if as_list:
            return [[float(job[0]), float(job[1])] for job in jobs]
        return [{'arrival_time': float(job[0]), 
                'job_size': float(job[1]), 
                'job_index': i} for i, job in enumerate(jobs)] if include_index else [
                {'arrival_time': float(job[0]), 
                 'job_size': float(job[1])} for job in jobs]
    return jobs

def process_scheduler_with_timeout(func, args, timeout=300000):  # 5 minutes timeout
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

def run_algorithm_multiple_times(algo, jobs, needs_index, as_list, num_runs=10):
    """Run an algorithm multiple times and return average L2 norm"""
    l2_norms = []
    for _ in range(num_runs):
        converted_jobs = convert_jobs(jobs.copy(), include_index=needs_index, as_list=as_list)
        result = process_scheduler_with_timeout(algo, (converted_jobs,))
        if result is None:
            return None
        _, l2n = result
        l2_norms.append(l2n)
    return np.mean(l2_norms)

def execute_phase1(Arrival_rate, bp_parameter):
    """Execute first phase algorithms and save results to CSV"""
    logger.info(f"Starting phase 1 execution with Arrival_rate={Arrival_rate}, bp_parameter={bp_parameter}")
    
    results = []
    for i in bp_parameter:
        logger.info(f"Processing bp_parameter: {i}")
        job_list = Read_csv.Read_csv('data/'+str((Arrival_rate,i["L"]))+".csv")
        logger.debug(f"Read job_list: {job_list[:5]}...")  

        algorithm_results = {}
        
        # Execute algorithms with multiple runs
        algorithms = [
            (RR.RR, job_list.copy(), False, True),
            (SRPT.Srpt, job_list.copy(), False, False),
            (SETF.Setf, job_list.copy(), False, True),
            (FCFS.Fcfs, job_list.copy(), False, False),
            (RMLF.RMLF, job_list.copy(), True, False)
        ]
        
        for algo, jobs, needs_index, as_list in algorithms:
            logger.info(f"Running {algo.__name__} 10 times")
            start_time = time.time()
            avg_l2n = run_algorithm_multiple_times(algo, jobs, needs_index, as_list)
            end_time = time.time()
            logger.info(f"{algo.__name__} completed 10 runs in {end_time - start_time:.2f} seconds")
            
            if avg_l2n is None:
                logger.error(f"{algo.__name__} failed or timed out")
                return []
                
            algorithm_results[algo.__name__] = avg_l2n

        results.append({
            "arrival_rate": Arrival_rate,
            "bp_parameter": i,
            "RR_L2_Norm": algorithm_results['RR'],
            "SRPT_L2_Norm": algorithm_results['Srpt'],
            "SETF_L2_Norm": algorithm_results['Setf'],
            "FCFS_L2_Norm": algorithm_results['Fcfs'],
            "RMLF_L2_Norm": algorithm_results['RMLF']
        })

    # Save results to CSV
    df = pd.DataFrame(results)
    csv_filename = f'phase1_results_{Arrival_rate}.csv'
    df.to_csv(csv_filename, index=False)
    logger.info(f"Phase 1 results saved to {csv_filename}")
    
    return job_list  # Return job_list for potential further use