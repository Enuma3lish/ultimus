import csv
import math
from SRPT_Selector import select_next_job_optimized as srpt_select_next_job
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
    """
    Optimized preemptive SRPT:
    - Event-driven time advance: run until next arrival or completion (min step).
    - Selection uses srpt_select_next_job (heap-backed) on dict views of waiting queue.
    - Returns (avg_flow_time, l2_norm_flow_time).
    """
    # Normalize & index
    jobs = [{"arrival_time": int(j["arrival_time"]), "job_size": int(j["job_size"]), "job_index": i} 
            for i, j in enumerate(jobs)]
    jobs.sort(key=lambda x: x["arrival_time"])

    total = len(jobs)
    if total == 0:
        return 0.0, 0.0

    t = 0
    i = 0
    waiting = []
    current = None
    completed = []

    while len(completed) < total:
        # Admit arrivals at time t
        while i < total and jobs[i]["arrival_time"] <= t:
            waiting.append({
                "arrival_time": jobs[i]["arrival_time"],
                "job_index": jobs[i]["job_index"],
                "remaining_time": jobs[i]["job_size"],
                "start_time": None,
                "completion_time": None,
            })
            i += 1

        # If there's a current job, consider preemption by pushing it back to waiting
        if current is not None:
            waiting.append(current)
            current = None

        # Pick SRPT job if available
        if waiting:
            picked = srpt_select_next_job([
                {"remaining_time": w["remaining_time"], "arrival_time": w["arrival_time"], "job_index": w["job_index"]}
                for w in waiting
            ])
            # Find the selected in waiting
            sel_idx = min(
                range(len(waiting)),
                key=lambda k: (waiting[k]["remaining_time"], waiting[k]["arrival_time"], waiting[k]["job_index"])
            )
            for k, w in enumerate(waiting):
                if (w["remaining_time"], w["arrival_time"], w["job_index"]) == \
                   (picked["remaining_time"], picked["arrival_time"], picked["job_index"]):
                    sel_idx = k
                    break
            current = waiting.pop(sel_idx)
            if current["start_time"] is None:
                current["start_time"] = t

            # Determine next arrival time
            next_arrival_t = jobs[i]["arrival_time"] if i < total else None

            if next_arrival_t is None:
                # No more arrivals: run to completion
                t += current["remaining_time"]
                current["completion_time"] = t
                current["remaining_time"] = 0
                completed.append(current)
                current = None
                continue
            else:
                # Run until either next arrival or completion
                delta = min(current["remaining_time"], max(1, next_arrival_t - t))
                t += delta
                current["remaining_time"] -= delta
                if current["remaining_time"] == 0:
                    current["completion_time"] = t
                    completed.append(current)
                    current = None
                # Loop; new arrivals will be admitted at the updated t in the next iteration
                continue

        # If nothing waiting, jump to next arrival
        if i < total:
            t = max(t, jobs[i]["arrival_time"])
        else:
            break

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
