import pandas as pd
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

def Sjf(jobs):
    """
    Shortest Job First (SJF) scheduling algorithm - non-preemptive
    
    Args:
        jobs: List of jobs (either as lists or dictionaries)
             If lists: [[arrival_time, job_size], ...]
             If dicts: [{'arrival_time': int, 'job_size': int}, ...]
    
    Returns:
        Tuple of (average_flow_time, l2_norm_flow_time)
    """
    # Convert dictionary format to list format if needed
    if jobs and isinstance(jobs[0], dict):
        jobs = [[job['arrival_time'], job['job_size']] for job in jobs]
    
    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x[0])
    time = 0
    waiting_time = []
    job_logs = []
    jobs_queue = []
    
    while jobs or jobs_queue:
        # Add jobs to the queue if they have arrived
        while jobs and jobs[0][0] <= time:
            # Add job to queue: [arrival_time, job_size]
            jobs_queue.append(jobs.pop(0))
        
        # Sort jobs in queue by job size (Shortest Job First)
        jobs_queue.sort(key=lambda x: x[1])
        
        if jobs_queue:
            job = jobs_queue.pop(0)
            start_time = time  # Record actual start time when job begins execution
            time += job[1]  # Execute the job for its full duration
            flow_time = time - job[0]  # Completion time - arrival time
            waiting_time.append(flow_time)
            job_logs.append({
                "arrival_time": job[0], 
                "first_executed_time": start_time, 
                "completion_time": time,
                "ifdone": True
            })
        else:
            # If no jobs are ready to be executed, advance to next arrival
            if jobs:
                time = jobs[0][0]
    
    # Calculate average flow time
    total_flow_time = sum(waiting_time)
    avg_flow_time = total_flow_time / len(waiting_time) if waiting_time else 0
    
    # Calculate L2 norm of flow time
    l2_norm_flow_time = (sum(f ** 2 for f in waiting_time)) ** 0.5
    
    return avg_flow_time, l2_norm_flow_time

def main():
    """Main function to process all data"""
    
    # Configuration
    data_dir = 'data'  # Base directory containing avg_30, freq_*, and softrandom folders
    output_dir = 'SJF_result'  # Output directory for results
    logger.info("="*60)
    logger.info(f"Starting SJF batch processing:")
    logger.info(f"  Data directory: {data_dir}")
    logger.info(f"  Output directory: {output_dir}")
    logger.info("="*60)
    
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process avg30 files
    logger.info("\n" + "="*40)
    logger.info("Processing avg_30 files...")
    logger.info("="*40)
    paf.process_avg_folders(Sjf,'SJF',data_dir, output_dir)
    
    # Process random files
    logger.info("\n" + "="*40)
    logger.info("Processing random files...")
    logger.info("="*40)
    prf.process_random_folders(Sjf,'SJF',data_dir, output_dir)
    
    # Process softrandom files
    logger.info("\n" + "="*40)
    logger.info("Processing softrandom files...")
    logger.info("="*40)
    psf.process_softrandom_folders(Sjf,'SJF',data_dir, output_dir)
    
    logger.info("\n" + "="*60)
    logger.info("SJF batch processing completed successfully!")
    logger.info("="*60)

if __name__ == "__main__":
    main()