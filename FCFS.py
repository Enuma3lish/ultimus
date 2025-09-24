import math
import csv
from FCFS_Selector import select_next_job_optimized as fcfs_select
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
    """
    Optimized non-preemptive FCFS:
    - Event-driven time advance (jump to next arrival or completion).
    - Heap-based pick via fcfs_select (O(log n)) for large queues, linear for small queues.
    - Returns (avg_flow_time, l2_norm_flow_time).
    """
    # Normalize & index
    jobs = [{"arrival_time": int(j["arrival_time"]), "job_size": int(j["job_size"]), "job_index": i} 
            for i, j in enumerate(jobs)]
    # Sort by arrival time once
    jobs.sort(key=lambda x: x["arrival_time"])

    total_jobs = len(jobs)
    if total_jobs == 0:
        return 0.0, 0.0

    t = 0
    i = 0
    waiting = []
    current = None
    completed = []

    while len(completed) < total_jobs:
        # Add arrivals up to current time
        while i < total_jobs and jobs[i]["arrival_time"] <= t:
            waiting.append({
                "arrival_time": jobs[i]["arrival_time"],
                "job_size": jobs[i]["job_size"],
                "job_index": jobs[i]["job_index"],
                "remaining_time": jobs[i]["job_size"],
                "start_time": None,
                "completion_time": None,
            })
            i += 1

        if current is None and waiting:
            picked = fcfs_select(waiting)  # dict
            # locate same dict (by identity keys)
            sel_idx = min(
                range(len(waiting)),
                key=lambda k: (waiting[k]["arrival_time"], waiting[k].get("job_size", 0), waiting[k].get("job_index", 0))
            )
            # Better: match exact picked
            for k, w in enumerate(waiting):
                if (w["arrival_time"], w.get("job_size", 0), w.get("job_index", 0)) == \
                   (picked["arrival_time"], picked.get("job_size", 0), picked.get("job_index", 0)):
                    sel_idx = k
                    break
            current = waiting.pop(sel_idx)
            if current["start_time"] is None:
                current["start_time"] = t

        if current is not None:
            # Non-preemptive: run to completion
            t += current["remaining_time"]
            current["completion_time"] = t
            current["remaining_time"] = 0
            completed.append(current)
            current = None
            continue  # loop to admit more arrivals or pick next

        # If idle, jump to next arrival (no 1-tick loops)
        if i < total_jobs:
            t = max(t, jobs[i]["arrival_time"])
            continue
        else:
            break  # no jobs left

    # Metrics
    flows = [c["completion_time"] - c["arrival_time"] for c in completed]
    n = len(flows)
    if n == 0:
        return 0.0, 0.0
    avg_flow = sum(flows) / n
    l2 = (sum(f * f for f in flows)) ** 0.5
    return avg_flow, l2

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