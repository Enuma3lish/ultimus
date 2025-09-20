from math import sqrt
from typing import List, Tuple, Union, Dict
from SETF_Selector import SETFSelector
import os
import csv
import re
import glob
import copy
import process_avg_folders as paf
import process_random_folders as prf
import process_softrandom_folders as psf
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def Setf(jobs: Union[List[Tuple[float, float]], List[Dict]]) -> Tuple[float, float]:
    """
    Shortest Elapsed Time First (SETF) scheduling algorithm
    
    Args:
        jobs: List of jobs, either as tuples (arrival_time, job_size) 
              or as dictionaries {'arrival_time': float, 'job_size': float}
    
    Returns:
        Tuple of (average_flow_time, l2_norm_flow_time)
    """
    # Convert dictionary format to tuple format if needed
    if jobs and isinstance(jobs[0], dict):
        jobs = [(job['arrival_time'], job['job_size']) for job in jobs]
    
    current_time = 0
    total_flow_time = 0
    squared_flow_time = 0
    completed_jobs = 0
    
    # Initialize job selector
    selector = SETFSelector()
    
    # Sort jobs by arrival time
    sorted_jobs = sorted(jobs, key=lambda x: x[0])
    n_jobs = len(sorted_jobs)
    job_pointer = 0
    
    while job_pointer < n_jobs or selector.has_active_jobs():
        # 1. Determine next event time
        next_arrival = sorted_jobs[job_pointer][0] if job_pointer < n_jobs else float('inf')
        
        # If no active jobs, jump to next arrival
        if not selector.has_active_jobs():
            current_time = next_arrival
            if job_pointer < n_jobs:
                selector.add_job(job_pointer, *sorted_jobs[job_pointer])
                job_pointer += 1
            continue
        
        # 2. Get job with shortest elapsed time
        next_job = selector.get_next_job()
        elapsed, job_id, arrival_time, size = next_job
        remaining = size - selector.job_elapsed[job_id]
        
        # 3. Determine how long to run current job
        if job_pointer < n_jobs:
            run_time = min(remaining, next_arrival - current_time)
        else:
            run_time = remaining
            
        # 4. Update job progress and time
        current_time += run_time
        selector.update_job_progress(job_id, run_time)
        
        # 5. Check if job completed
        if selector.is_job_completed(job_id, size):
            flow_time = current_time - arrival_time
            total_flow_time += flow_time
            squared_flow_time += flow_time * flow_time
            completed_jobs += 1
        else:
            selector.requeue_job(job_id, arrival_time, size)
            
        # 6. Add any new arrivals
        while job_pointer < n_jobs and sorted_jobs[job_pointer][0] <= current_time:
            selector.add_job(job_pointer, *sorted_jobs[job_pointer])
            job_pointer += 1
    
    if completed_jobs == 0:
        return 0.0, 0.0
        
    average_flow_time = total_flow_time / completed_jobs
    l2_norm_flow_time = sqrt(squared_flow_time)
    
    return average_flow_time, l2_norm_flow_time

def main():
    """Main function to process all data"""
    
    # Configuration
    data_dir = 'data'  # Base directory containing all folders
    output_dir = 'SETF_result'  # Output directory for results
    
    logger.info("="*60)
    logger.info(f"Starting SETF batch processing:")
    logger.info(f"  Data directory: {data_dir}")
    logger.info(f"  Output directory: {output_dir}")
    logger.info("="*60)
    
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process avg folders
    logger.info("\n" + "="*40)
    logger.info("Processing avg folders...")
    logger.info("="*40)
    paf.process_avg_folders(Setf, 'SETF', data_dir, output_dir)
    
    # Process random files
    logger.info("\n" + "="*40)
    logger.info("Processing random files...")
    logger.info("="*40)
    prf.process_random_folders(Setf, 'SETF', data_dir, output_dir)
    
    # Process softrandom files
    logger.info("\n" + "="*40)
    logger.info("Processing softrandom files...")
    logger.info("="*40)
    psf.process_softrandom_folders(Setf, 'SETF', data_dir, output_dir)
    
    logger.info("\n" + "="*60)
    logger.info("SETF batch processing completed successfully!")
    logger.info("="*60)

if __name__ == "__main__":
    main()