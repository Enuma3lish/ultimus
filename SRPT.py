import csv
import math
from SRPT_Selector import select_next_job as srpt_select_next_job
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
def Srpt(jobs):
    current_time = 0
    completed_jobs = []
    job_queue = []
    total_jobs = len(jobs)
    jobs_pointer = 0

    # Assign job indices
    for idx, job in enumerate(jobs):
        job['job_index'] = idx

    # Sort jobs by arrival time
    jobs.sort(key=lambda x: x['arrival_time'])

    while len(completed_jobs) < total_jobs:
        # Add jobs that arrive at the current time
        while jobs_pointer < total_jobs and jobs[jobs_pointer]['arrival_time'] <= current_time:
            job = jobs[jobs_pointer]
            job_copy = {
                'arrival_time': job['arrival_time'],
                'job_size': job['job_size'],
                'remaining_time': job['job_size'],
                'job_index': job['job_index'],
                'completion_time': None,
                'start_time': None
            }
            job_queue.append(job_copy)
            jobs_pointer += 1

        # Select the next job
        selected_job = srpt_select_next_job(job_queue) if job_queue else None

        # Process selected job
        if selected_job:
            job_queue.remove(selected_job)

            # Record start_time if not already set
            if selected_job['start_time'] is None:
                selected_job['start_time'] = current_time

            selected_job['remaining_time'] -= 1

            # Check if job is completed
            if selected_job['remaining_time'] == 0:
                selected_job['completion_time'] = current_time + 1  # Adjusted here
                completed_jobs.append(selected_job)
            else:
                # Re-add the job to the queue
                job_queue.append(selected_job)

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
    output_dir = 'SRPT_result'  # Output directory for results
    logger.info("="*60)
    logger.info(f"Starting SRPT batch processing:")
    logger.info(f"  Data directory: {data_dir}")
    logger.info(f"  Output directory: {output_dir}")
    logger.info("="*60)
    
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process avg30 files
    logger.info("\n" + "="*40)
    logger.info("Processing avg_30 files...")
    logger.info("="*40)
    paf.process_avg_folders(Srpt,'SRPT',data_dir, output_dir)
    
    # Process random files
    logger.info("\n" + "="*40)
    logger.info("Processing random files...")
    logger.info("="*40)
    prf.process_random_folders(Srpt,'SRPT',data_dir, output_dir)
    
    # Process softrandom files
    logger.info("\n" + "="*40)
    logger.info("Processing softrandom files...")
    logger.info("="*40)
    psf.process_softrandom_folders(Srpt,'SRPT',data_dir, output_dir)
    
    logger.info("\n" + "="*60)
    logger.info("SRPT batch processing completed successfully!")
    logger.info("="*60)

if __name__ == "__main__":
    main()
