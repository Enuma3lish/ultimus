import multiprocessing
import Read_csv
import RR, SRPT, SETF, FCFS, RMLF
import time
import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from concurrent.futures import TimeoutError

def convert_jobs(jobs, include_index=False, as_list=False):
    """Convert jobs to appropriate format"""
    if not jobs:
        return []
    
    if isinstance(jobs[0], (list, tuple)):
        if as_list:
            return [[float(job[0]), float(job[1])] for job in jobs]
        return [{'arrival_time': float(job[0]), 
                'job_size': float(job[1]), 
                'job_index': i} for i, job in enumerate(jobs)] if include_index else [
                {'arrival_time': float(job[0]), 
                 'job_size': float(job[1])} for job in jobs]
    return jobs

def run_algorithm(algo, jobs, needs_index, as_list):
    """Run a single algorithm"""
    if not jobs:
        return None
    try:
        converted_jobs = convert_jobs(jobs.copy(), include_index=needs_index, as_list=as_list)
        _, l2n = algo(converted_jobs)
        return l2n
    except:
        return None

def run_all_algorithms_parallel(job_list, algorithms):
    """Run all algorithms in parallel"""
    results = {}
    with ProcessPoolExecutor(max_workers=len(algorithms)) as executor:
        future_to_algo = {}
        for algo, jobs, needs_index, as_list in algorithms:
            if not jobs:
                return None
            future = executor.submit(run_algorithm, algo, jobs, needs_index, as_list)
            future_to_algo[future] = algo.__name__

        try:
            for future in as_completed(future_to_algo, timeout=3000):  # 5 minute timeout
                algo_name = future_to_algo[future]
                l2n = future.result(timeout=60)  # 1 minute timeout per algorithm
                if l2n is None:
                    return None
                results[algo_name] = l2n
        except (TimeoutError, Exception):
            return None
                
    return results if len(results) == len(algorithms) else None

def execute_phase1(Arrival_rate, bp_parameter):
    """Execute phase 1 for normal data"""
    results = []
    for i in bp_parameter:
        try:
            # Read job list
            job_list = Read_csv.Read_csv('data/'+str((Arrival_rate,i["L"]))+".csv")
            if not job_list:
                continue

            # Set up algorithms
            algorithms = [
                (RR.RR, job_list.copy(), False, True),
                (SRPT.Srpt, job_list.copy(), False, False),
                (SETF.Setf, job_list.copy(), False, True),
                (FCFS.Fcfs, job_list.copy(), False, False),
                (RMLF.RMLF, job_list.copy(), True, False)
            ]
            
            # Run algorithms and collect results
            algorithm_results = run_all_algorithms_parallel(job_list, algorithms)
            if algorithm_results and all(v is not None for v in algorithm_results.values()):
                results.append({
                    "arrival_rate": Arrival_rate,
                    "bp_parameter": i,
                    "RR_L2_Norm": algorithm_results['RR'],
                    "SRPT_L2_Norm": algorithm_results['Srpt'],
                    "SETF_L2_Norm": algorithm_results['Setf'],
                    "FCFS_L2_Norm": algorithm_results['Fcfs'],
                    "RMLF_L2_Norm": algorithm_results['RMLF']
                })
        except:
            continue

    # Save results
    if results:
        df = pd.DataFrame(results)
        csv_filename = f'phase1_results_{Arrival_rate}.csv'
        df.to_csv(csv_filename, index=False)

def execute_phase1_random(Arrival_rate, random_list):
    """Execute phase 1 for random data"""
    for i in random_list:
        # Reset results for each random list item
        results = []
        
        # Read job list
        job_list = Read_csv.Read_csv(f'{i}_random_data/inter_arrival_{Arrival_rate}.csv')
        
        # Set up algorithms
        algorithms = [
            (RR.RR, job_list.copy(), False, True),
            (SRPT.Srpt, job_list.copy(), False, False),
            (SETF.Setf, job_list.copy(), False, True),
            (FCFS.Fcfs, job_list.copy(), False, False),
            (RMLF.RMLF, job_list.copy(), True, False)
        ]
        
        # Run algorithms and collect results
        algorithm_results = run_all_algorithms_parallel(job_list, algorithms)
        if algorithm_results and all(v is not None for v in algorithm_results.values()):
            result_row = {
                "arrival_rate": Arrival_rate,
                "RR_L2_Norm": algorithm_results['RR'],
                "SRPT_L2_Norm": algorithm_results['Srpt'],
                "SETF_L2_Norm": algorithm_results['Setf'],
                "FCFS_L2_Norm": algorithm_results['Fcfs'],
                "RMLF_L2_Norm": algorithm_results['RMLF']
            }
            results.append(result_row)
            
            # Create and save DataFrame immediately after getting results
            if results:
                df = pd.DataFrame(results)
                csv_filename = f'{i}_random_phase1_results_{Arrival_rate}.csv'
                df.to_csv(csv_filename, index=False)