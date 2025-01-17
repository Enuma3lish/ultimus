import multiprocessing
import Read_csv
import RR, SRPT, SETF, FCFS, RMLF
import time
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed

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

def run_algorithm(algo, jobs, needs_index, as_list):
    """Run an algorithm and return its L2 norm"""
    try:
        converted_jobs = convert_jobs(jobs.copy(), include_index=needs_index, as_list=as_list)
        _, l2n = algo(converted_jobs)
        return l2n
    except Exception:
        return None

def run_all_algorithms_parallel(job_list, algorithms):
    """Run all algorithms in parallel"""
    results = {}
    with ProcessPoolExecutor(max_workers=len(algorithms)) as executor:
        future_to_algo = {}
        for algo, jobs, needs_index, as_list in algorithms:
            future = executor.submit(run_algorithm, algo, jobs, needs_index, as_list)
            future_to_algo[future] = algo.__name__

        for future in as_completed(future_to_algo):
            algo_name = future_to_algo[future]
            try:
                l2n = future.result()
                if l2n is None:
                    return None
                results[algo_name] = l2n
            except Exception:
                return None
                
    return results

def execute_phase1(Arrival_rate, bp_parameter):
    """Execute first phase algorithms in parallel and save results to CSV"""
    results = []
    for i in bp_parameter:
        job_list = Read_csv.Read_csv('data/'+str((Arrival_rate,i["L"]))+".csv")

        algorithms = [
            (RR.RR, job_list.copy(), False, True),
            (SRPT.Srpt, job_list.copy(), False, False),
            (SETF.Setf, job_list.copy(), False, True),
            (FCFS.Fcfs, job_list.copy(), False, False),
            (RMLF.RMLF, job_list.copy(), True, False)
        ]
        
        algorithm_results = run_all_algorithms_parallel(job_list, algorithms)
        
        if algorithm_results is None:
            return []

        results.append({
            "arrival_rate": Arrival_rate,
            "bp_parameter": i,
            "RR_L2_Norm": algorithm_results['RR'],
            "SRPT_L2_Norm": algorithm_results['Srpt'],
            "SETF_L2_Norm": algorithm_results['Setf'],
            "FCFS_L2_Norm": algorithm_results['Fcfs'],
            "RMLF_L2_Norm": algorithm_results['RMLF']
        })

    # Save results to CSV
    df = pd.DataFrame(results)
    csv_filename = f'phase1_results_{Arrival_rate}.csv'
    df.to_csv(csv_filename, index=False)
    
    return job_list