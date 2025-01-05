import multiprocessing
import Read_csv
import RR, SRPT, SETF, FCFS, RDYNAMIC, RMLF
import logging
import time
import pandas as pd
from functools import partial

# Set up logging
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

def execute_phase1(Arrival_rate, bp_parameter):
    """Execute first phase algorithms and save results to CSV"""
    logger.info(f"Starting phase 1 execution with Arrival_rate={Arrival_rate}, bp_parameter={bp_parameter}")
    
    results = []
    for i in bp_parameter:
        logger.info(f"Processing bp_parameter: {i}")
        job_list = Read_csv.Read_csv('data/'+str((Arrival_rate,i["L"]))+".csv")
        logger.debug(f"Read job_list: {job_list[:5]}...")  

        algorithm_results = {}
        
        # Execute algorithms sequentially with proper format for each
        for algo, jobs, needs_index, as_list in [
            (RR.RR, job_list.copy(), False, True),
            (SRPT.Srpt, job_list.copy(), False, False),
            (SETF.Setf, job_list.copy(), False, True),
            (FCFS.Fcfs, job_list.copy(), False, False),
            (RMLF.RMLF, job_list.copy(), True, False)
        ]:
            logger.info(f"Running {algo.__name__}")
            start_time = time.time()
            converted_jobs = convert_jobs(jobs, include_index=needs_index, as_list=as_list)
            algo_result = process_scheduler_with_timeout(algo, (converted_jobs,))
            end_time = time.time()
            logger.info(f"{algo.__name__} completed in {end_time - start_time:.2f} seconds")
            if algo_result is None:
                logger.error(f"{algo.__name__} failed or timed out")
                return []
            algorithm_results[algo.__name__] = algo_result

        # Unpack results
        rr_avg, rr_l2n = algorithm_results['RR']
        srpt_avg, srpt_l2n = algorithm_results['Srpt']
        setf_avg, setf_l2n = algorithm_results['Setf']
        fcfs_avg, fcfs_l2n = algorithm_results['Fcfs']
        rmlf_avg, rmlf_l2n = algorithm_results['RMLF']
        
        results.append({
            "arrival_rate": Arrival_rate,
            "bp_parameter": i,
            "RR_L2_Norm": rr_l2n,
            "SRPT_L2_Norm": srpt_l2n,
            "SETF_L2_Norm": setf_l2n,
            "FCFS_L2_Norm": fcfs_l2n,
            "RMLF_L2_Norm": rmlf_l2n
        })

    # Save results to CSV
    df = pd.DataFrame(results)
    csv_filename = f'phase1_results_{Arrival_rate}.csv'
    df.to_csv(csv_filename, index=False)
    logger.info(f"Phase 1 results saved to {csv_filename}")
    return results

def execute_phase2(Arrival_rate, bp_parameter, c):
    """Execute RDYNAMIC and compare with phase 1 results"""
    logger.info(f"Starting phase 2 execution with Arrival_rate={Arrival_rate}, bp_parameter={bp_parameter}, c={c}")
    
    # Calculate mean inter-arrival time
    mean_inter_arrival_time = Arrival_rate
    
    # Read phase 1 results
    phase1_df = pd.read_csv(f'phase1_results_{Arrival_rate}.csv')
    
    results = []
    for i in bp_parameter:
        logger.info(f"Processing bp_parameter: {i}")
        job_list = Read_csv.Read_csv('data/'+str((Arrival_rate,i["L"]))+".csv")
        
        # Execute RDYNAMIC with additional parameters
        logger.info("Running RDYNAMIC")
        start_time = time.time()
        converted_rdynamic_list = convert_jobs(job_list.copy(), include_index=True)
        rdy = process_scheduler_with_timeout(
            RDYNAMIC.RDYNAMIC,
            (converted_rdynamic_list, c, Arrival_rate, i)
        )
        end_time = time.time()
        logger.info(f"RDYNAMIC completed in {end_time - start_time:.2f} seconds")
        if rdy is None:
            logger.error("RDYNAMIC failed or timed out")
            return []
        
        # Get RDYNAMIC results
        rdy_avg, rdy_l2n = rdy
        
        # Get corresponding phase 1 results
        phase1_row = phase1_df[phase1_df['bp_parameter'].astype(str) == str(i)].iloc[0]
        
        results.append({
            "arrival_rate": Arrival_rate,
            "bp_parameter": i,
            "c": c,
            "RMLF_L2_Norm/FCFS_L2_Norm": phase1_row['RMLF_L2_Norm'] / phase1_row['FCFS_L2_Norm'],
            "RDYNAMIC_L2_Norm/FCFS_L2_Norm": rdy_l2n / phase1_row['FCFS_L2_Norm'],
            "RDYNAMIC_L2_Norm/SETF_L2_Norm": rdy_l2n / phase1_row['SETF_L2_Norm'],
            "RDYNAMIC_L2_Norm/RR_L2_Norm": rdy_l2n / phase1_row['RR_L2_Norm'],
            "RDYNAMIC_L2_Norm/RMLF_L2_Norm": rdy_l2n / phase1_row['RMLF_L2_Norm']
        })

    # Save final results
    df = pd.DataFrame(results)
    csv_filename = f'final_results_{Arrival_rate}.csv'
    df.to_csv(csv_filename, index=False)
    logger.info(f"Final results saved to {csv_filename}")
    return results

def execute(Arrival_rate, bp_parameter, c):
    """Main execution function"""
    # Execute phase 1
    phase1_results = execute_phase1(Arrival_rate, bp_parameter)
    if not phase1_results:
        return []
    
    # Execute phase 2
    return execute_phase2(Arrival_rate, bp_parameter, int(c))