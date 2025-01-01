import multiprocessing
import Read_csv
import RR, SJF, SETF, FCFS, Dynamic, SRPT, RDYNAMIC, RMLF
import logging
import time
from functools import partial

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_jobs(jobs, include_index=False, as_list=False):
    """
    Convert jobs to appropriate format based on algorithm requirements
    as_list: True returns [[arrival_time, job_size], ...] format for RR, SJF, SETF
    include_index: True includes job_index for RMLF and RDYNAMIC
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

def execute(Arrival_rate, bp_parameter, c):
    logger.info(f"Starting execution with Arrival_rate={Arrival_rate}, bp_parameter={bp_parameter}, c={c}")
    
    c = int(c)
    
    results = []
    for i in bp_parameter:
        logger.info(f"Processing bp_parameter: {i}")
        job_list = Read_csv.Read_csv('data/'+str((Arrival_rate,i["L"]))+".csv")
        logger.debug(f"Read job_list: {job_list[:5]}...")  

        algorithm_results = {}
        
        # Execute algorithms sequentially with proper format for each
        for algo, jobs, needs_index, as_list in [
            (RR.RR, job_list.copy(), False, True),
            # (SRPT.Srpt, job_list.copy(), False, False),
            # (SJF.Sjf, job_list.copy(), False, True),
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

        # Execute DYNAMIC algorithm
        # logger.info("Running DYNAMIC")
        # start_time = time.time()
        # converted_dynamic_list = convert_jobs(job_list.copy())
        # dy = process_scheduler_with_timeout(Dynamic.DYNAMIC, (converted_dynamic_list, c))
        # end_time = time.time()
        # logger.info(f"DYNAMIC completed in {end_time - start_time:.2f} seconds")
        # if dy is None:
        #     logger.error("DYNAMIC failed or timed out")
        #     return []

        # Execute RDYNAMIC algorithm
        logger.info("Running RDYNAMIC")
        start_time = time.time()
        converted_rdynamic_list = convert_jobs(job_list.copy(), include_index=True)
        rdy = process_scheduler_with_timeout(RDYNAMIC.RDYNAMIC, (converted_rdynamic_list,c))
        end_time = time.time()
        logger.info(f"RDYNAMIC completed in {end_time - start_time:.2f} seconds")
        if rdy is None:
            logger.error("RDYNAMIC failed or timed out")
            return []
        
        # Unpack results
        rr_avg, rr_l2n = algorithm_results['RR']
        #srpt_avg, srpt_l2n = algorithm_results['Srpt']
        #sjf_avg, sjf_l2n = algorithm_results['Sjf']
        setf_avg, setf_l2n = algorithm_results['Setf']
        fcfs_avg, fcfs_l2n = algorithm_results['Fcfs']
        rmlf_avg, rmlf_l2n = algorithm_results['RMLF']
        #dy_avg, dy_l2n = dy
        rdy_avg, rdy_l2n = rdy
        #sjf_avg_srpt = sjf_avg / srpt_avg 
        #r_avg_srpt = rr_avg / srpt_avg
        # setf_avg_srpt = setf_avg / srpt_avg
        # fcfs_avg_srpt = fcfs_avg / srpt_avg
       # dynamic_avg_srpt = dy_avg / srpt_avg
       # rmlf_avg_srpt = rmlf_avg / srpt_avg
        
        # L2 norm ratios
        # sjf_l2n_srpt = sjf_l2n / srpt_l2n 
        # rr_l2n_srpt = rr_l2n / srpt_l2n
        # setf_l2n_srpt = setf_l2n / srpt_l2n
        setf_l2n_fcfs = setf_l2n/fcfs_l2n
        # fcfs_l2n_srpt = fcfs_l2n / srpt_l2n
        # dy_l2n_result = dy_l2n / srpt_l2n
        # rmlf_l2n_srpt = rmlf_l2n / srpt_l2n
        rmlf_l2n_rr = rmlf_l2n/ rr_l2n
        rmlf_l2n_fcfs = rmlf_l2n/fcfs_l2n
        rmlf_l2n_setf = rmlf_l2n/setf_l2n
        # rdy_l2n_srpt = rdy_l2n / srpt_l2n
        rdy_l2n_fcfs = rdy_l2n / fcfs_l2n
        rdy_l2n_rr  = rdy_l2n / rr_l2n
        rdy_l2n_rmlf = rdy_l2n / rmlf_l2n
        rdy_l2n_setf = rdy_l2n / setf_l2n
        results.append({
            "arrival_rate": Arrival_rate,
            "bp_parameter": i,
            "c":c,
            # "RDYNAMIC_L2_Norm/SRPT_L2_Norm":rdy_l2n_srpt,
            "RMLF_L2_Norm/FCFS_L2_Norm": rmlf_l2n/fcfs_l2n,
            "RDYNAMIC_L2_Norm/FCFS_L2_Norm": rdy_l2n_fcfs,
            "RDYNAMIC_L2_Norm/SETF_L2_Norm": rdy_l2n_setf,
            "RDYNAMIC_L2_Norm/RR_L2_Norm":  rdy_l2n_rr,
            "RDYNAMIC_L2_Norm/RMLF_L2_Norm": rdy_l2n_rmlf
        })

    logger.info("Execution completed successfully")
    return results