import multiprocessing
import Read_csv
import RR, SJF, SETF, FCFS, Dynamic, SRPT
import logging
import time
from functools import partial

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_jobs(jobs):
    if jobs and isinstance(jobs[0], (list, tuple)):
        return [{'arrival_time': float(job[0]), 'job_size': float(job[1])} for job in jobs]
    return jobs

def process_scheduler_with_timeout(func, args, timeout=3000):  # 5 minutes timeout
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

def execute(Arrival_rate, bp_parameter, c):
    logger.info(f"Starting execution with Arrival_rate={Arrival_rate}, bp_parameter={bp_parameter}, c={c}")
    
    # Ensure c is an integer
    c = int(c)
    
    results = []
    for i in bp_parameter:
        logger.info(f"Processing bp_parameter: {i}")
        job_list = Read_csv.Read_csv('data/'+str((Arrival_rate,i["L"]))+".csv")
        logger.debug(f"Read job_list: {job_list[:5]}...")  # Log first 5 jobs

        algorithm_results = {}
        
        # Execute algorithms sequentially
        for algo, jobs in [
            (RR.Rr, job_list.copy()),
            (SRPT.Srpt, convert_jobs(job_list.copy())),
            (SJF.Sjf, job_list.copy()),
            (SETF.Setf, job_list.copy()),
            (FCFS.Fcfs, convert_jobs(job_list.copy()))
        ]:
            logger.info(f"Running {algo.__name__}")
            start_time = time.time()
            algo_result = process_scheduler_with_timeout(algo, (jobs,))
            end_time = time.time()
            logger.info(f"{algo.__name__} completed in {end_time - start_time:.2f} seconds")
            if algo_result is None:
                logger.error(f"{algo.__name__} failed or timed out")
                return []  # or handle the error as appropriate
            algorithm_results[algo.__name__] = algo_result

        # Execute DYNAMIC algorithm last
        logger.info("Running DYNAMIC")
        start_time = time.time()
        converted_dynamic_list = convert_jobs(job_list.copy())
        dy = process_scheduler_with_timeout(Dynamic.DYNAMIC, (converted_dynamic_list, c))
        end_time = time.time()
        logger.info(f"DYNAMIC completed in {end_time - start_time:.2f} seconds")
        if dy is None:
            logger.error("DYNAMIC failed or timed out")
            return []  # or handle the error as appropriate
        
        rr_avg, rr_l2n = algorithm_results['Rr']
        srpt_avg, srpt_l2n = algorithm_results['Srpt']
        sjf_avg, sjf_l2n = algorithm_results['Sjf']
        setf_avg, setf_l2n = algorithm_results['Setf']
        fcfs_avg, fcfs_l2n = algorithm_results['Fcfs']
        dy_avg, dy_l2n = dy

        # Calculate ratios
        sjf_result = sjf_avg / srpt_avg 
        rr_result = rr_avg / srpt_avg
        setf_result = setf_avg / srpt_avg
        fcfs_result = fcfs_avg / srpt_avg
        dynamic_result = dy_avg / srpt_avg

        sjf_fcfs = sjf_avg / fcfs_avg 
        rr_fcfs = rr_avg / fcfs_avg
        setf_fcfs = setf_avg / fcfs_avg
        srpt_fcfs = srpt_avg / fcfs_avg

        sjf_l2n_result = sjf_l2n / srpt_l2n 
        rr_l2n_result = rr_l2n / srpt_l2n
        setf_l2n_result = setf_l2n / srpt_l2n
        fcfs_l2n_result = fcfs_l2n / srpt_l2n
        dy_l2n_result = dy_l2n/ srpt_l2n

        sjf_l2n_fcfs = sjf_l2n / fcfs_l2n 
        rr_l2n_fcfs = rr_l2n / fcfs_l2n
        rr_l2n_setf = rr_l2n / setf_l2n
        dy_l2n_fcfs = dy_l2n / fcfs_l2n
        dy_comp_rr = dy_l2n / rr_l2n
        dy_comp_setf = dy_l2n / setf_l2n

        results.append({
            "arrival_rate": Arrival_rate,
            "bp_parameter": i,
            "c": c,
            "SJF/SRPT": sjf_result,
            "RR/SRPT": rr_result,
            "SETF/SRPT": setf_result,
            "FCFS/SRPT": fcfs_result,
            "SJF/FCFS": sjf_fcfs,
            "RR/FCFS": rr_fcfs,
            "SETF/FCFS": setf_fcfs,
            "SPRT/FCFS": srpt_fcfs,
            "SJF_L2_Norm/SRPT_L2_Norm": sjf_l2n_result,
            "RR_L2_Norm/SRPT_L2_Norm": rr_l2n_result,
            "SETF_L2_Norm/SRPT_L2_Norm": setf_l2n_result,
            "FCFS_L2_Norm/SRPT_L2_Norm": fcfs_l2n_result,
            "SJF_L2_Norm/FCFS_L2_Norm": sjf_l2n_fcfs,
            "RR_L2_Norm/FCFS_L2_Norm": rr_l2n_fcfs,
            "RR_L2_Norm/SETF_L2_Norm": rr_l2n_setf,
            "DYNAMIC_L2_Norm/SRPT_L2_Norm": dy_l2n_result,
            "DYNAMIC_L2_Norm/FCFS_L2_Norm": dy_l2n_fcfs,
            "DYNAMIC_L2_Norm/RR_L2_Norm": dy_comp_rr,
            "DYNAMIC_L2_Norm/SETF_L2_Norm": dy_comp_setf
        })

    logger.info("Execution completed successfully")
    return results

# Example usage
# if __name__ == "__main__":
#     # These are example values. Replace with your actual values.
#     example_arrival_rate = 20
#     example_bp_parameter = [{"L":16.772,"H":pow(2,6)},{"L":7.918,"H":pow(2,9)},{"L":5.649,"H":pow(2,12)},{"L":4.639,"H":pow(2,15)},{"L":4.073,"H":pow(2,18)}]
#     example_c = 40  # Example c value as an integer

#     try:
#         results = execute(example_arrival_rate, example_bp_parameter, example_c)
#         if results:
#             logger.info(f"Results: {results}")
#         else:
#             logger.warning("No results were produced")
#     except Exception as e:
#         logger.error(f"Error in main execution: {e}", exc_info=True)