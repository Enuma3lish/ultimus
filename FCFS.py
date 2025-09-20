import math
import csv
from FCFS_Selector import select_next_job
import time
import os
import csv
import re
import glob
import copy
import logging

import process_avg_folders as paf
import process_random_folders as prf
import process_softrandom_folders as psf
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
def Fcfs(jobs):
    current_time = 0
    completed_jobs = []
    waiting_queue = []
    total_jobs = len(jobs)
    jobs_pointer = 0
    current_job = None  # Track the currently executing job
    
    # Assign job indices
    for idx, job in enumerate(jobs):
        job['job_index'] = idx

    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x['arrival_time'])

    while len(completed_jobs) < total_jobs:
        # Add jobs that arrive at or before the current time
        # Note: Using <= to catch any jobs that might have arrived earlier
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] <= current_time:
            job = jobs[jobs_pointer]
            # Copy job to avoid modifying the original
            job_copy = {
                'arrival_time': job['arrival_time'],
                'job_size': job['job_size'],
                'remaining_time': job['job_size'],
                'job_index': job['job_index'],
                'completion_time': None,
                'start_time': None
            }
            waiting_queue.append(job_copy)
            jobs_pointer += 1

        # Select the next job ONLY if no job is currently running
        if current_job is None and waiting_queue:
            current_job = select_next_job(waiting_queue)
            if current_job:
                waiting_queue.remove(current_job)
                # Record start_time if not already set
                if current_job['start_time'] is None:
                    current_job['start_time'] = current_time

        # Process current job (non-preemptive - job runs until completion)
        if current_job:
            current_job['remaining_time'] -= 1

            # Check if job is completed
            if current_job['remaining_time'] == 0:
                current_job['completion_time'] = current_time + 1
                completed_jobs.append(current_job)
                current_job = None  # Free up for next job selection
                # Do NOT add back to waiting_queue - job is done!

        # Increment time
        current_time += 1

    # Calculate metrics
    total_flow_time = sum(job['completion_time'] - job['arrival_time'] for job in completed_jobs)
    if total_jobs > 0:
        avg_flow_time = total_flow_time / total_jobs
        l2_norm_flow_time = (sum((job['completion_time'] - job['arrival_time']) ** 2 for job in completed_jobs)) ** 0.5
    else:
        avg_flow_time = 0
        l2_norm_flow_time = 0

    return avg_flow_time, l2_norm_flow_time

def main():
    """Main function to process all data"""
    
    # Configuration
    data_dir = 'data'  # Base directory containing avg_30, freq_*, and softrandom folders
    output_dir = 'FCFS_result'  # Output directory for results
    
    logger.info("="*60)
    logger.info(f"Starting FCFS batch processing:")
    logger.info(f"  Data directory: {data_dir}")
    logger.info(f"  Output directory: {output_dir}")
    logger.info("="*60)
    
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process avg30 files
    logger.info("\n" + "="*40)
    logger.info("Processing avg_30 files...")
    logger.info("="*40)
    paf.process_avg_folders(Fcfs,'FCFS',data_dir, output_dir)
    
    # Process random files
    logger.info("\n" + "="*40)
    logger.info("Processing random files...")
    logger.info("="*40)
    prf.process_random_folders(Fcfs,'FCFS',data_dir, output_dir)
    
    # Process softrandom files
    logger.info("\n" + "="*40)
    logger.info("Processing softrandom files...")
    logger.info("="*40)
    psf.process_softrandom_folders(Fcfs,'FCFS',data_dir, output_dir)
    
    logger.info("\n" + "="*60)
    logger.info("FCFS batch processing completed successfully!")
    logger.info("="*60)

if __name__ == "__main__":
    main()