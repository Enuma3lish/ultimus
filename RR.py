from typing import List, Tuple
from collections import deque
from RR_Selector import RR_Selector_optimized as RR_Selector
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
def RR(jobs: List, time_quantum: int = 1) -> Tuple[float, float]:
    """
    Optimized online Round Robin:
    - Event-driven time advance: run slices of size min(quantum, remaining, time_to_next_arrival).
    - O(1) amortized admission using deque for incoming jobs.
    - Returns (average_flow_time, l2_norm).
    """
    if not jobs:
        return 0.0, 0.0

    # Normalize input into list of (arrival, size) and assign original indices
    if isinstance(jobs[0], dict):
        base = [(int(j["arrival_time"]), int(j["job_size"])) for j in jobs]
    else:
        base = [(int(j[0]), int(j[1])) for j in jobs]

    # Sort by arrival and create a deque of (orig_idx, arrival, remaining)
    indexed = [(i, at, sz) for i, (at, sz) in enumerate(base)]
    indexed.sort(key=lambda x: x[1])
    jobs_info = deque(indexed)

    n = len(indexed)
    ready_queue = deque()  # holds (orig_idx, remaining)
    current_time = 0
    completed = 0

    completion_times = [0] * n

    total_flow_sum = 0.0
    l2_sum = 0.0

    while completed < n:
        # Use optimized selector
        orig_idx, execution_time, has_job = RR_Selector(jobs_info, current_time, ready_queue, time_quantum)

        if has_job:
            # Execute the job at the front for 'execution_time'
            orig0, rem0 = ready_queue[0]
            assert orig0 == orig_idx
            # Advance time
            current_time += execution_time
            rem0 -= execution_time

            if rem0 <= 0:
                # Job completed
                ready_queue.popleft()
                completion_times[orig_idx] = current_time
                flow = completion_times[orig_idx] - base[orig_idx][0]
                total_flow_sum += flow
                l2_sum += float(flow) * float(flow)
                completed += 1
            else:
                # Put back at end (Round Robin)
                ready_queue.popleft()
                ready_queue.append((orig_idx, rem0))
        else:
            # No job to run now; jump time to next arrival
            next_t = execution_time  # selector uses this field to return next arrival
            if next_t > current_time:
                current_time = next_t
            else:
                # Safeguard against stalling; move at least 1 unit
                current_time += 1

    avg_flow = total_flow_sum / n
    l2 = (l2_sum) ** 0.5
    return avg_flow, l2

def main():
    """Main function to process all data"""
    
    # Configuration
    data_dir = 'data'  # Base directory containing avg_30, freq_*, and softrandom folders
    output_dir = 'RR_result'  # Output directory for results
    logger.info("="*60)
    logger.info(f"Starting RR batch processing:")
    logger.info(f"  Data directory: {data_dir}")
    logger.info(f"  Output directory: {output_dir}")
    logger.info("="*60)
    
    # Create main output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Process avg30 files
    logger.info("\n" + "="*40)
    logger.info("Processing avg_30 files...")
    logger.info("="*40)
    paf.process_avg_folders(RR,'RR',data_dir, output_dir)
    
    # Process random files
    logger.info("\n" + "="*40)
    logger.info("Processing random files...")
    logger.info("="*40)
    prf.process_random_folders(RR,'RR',data_dir, output_dir)
    
    # Process softrandom files
    logger.info("\n" + "="*40)
    logger.info("Processing softrandom files...")
    logger.info("="*40)
    psf.process_softrandom_folders(RR,'RR',data_dir, output_dir)
    
    logger.info("\n" + "="*60)
    logger.info("RR batch processing completed successfully!")
    logger.info("="*60)

if __name__ == "__main__":
    main()