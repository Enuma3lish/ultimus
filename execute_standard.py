import multiprocessing
import Read_csv
import RR, SRPT, SETF, FCFS, RMLF, Dynamic, RFdynamic
import time
import pandas as pd
import numpy as np
import os
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
    except Exception as e:
        print(f"Error running algorithm {algo.__name__}: {str(e)}")
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
            for future in as_completed(future_to_algo, timeout=3000):  # 50 minute timeout
                algo_name = future_to_algo[future]
                l2n = future.result(timeout=120)  # 2 minute timeout per algorithm
                if l2n is None:
                    print(f"Algorithm {algo_name} returned None")
                    return None
                results[algo_name] = l2n
        except (TimeoutError, Exception) as e:
            print(f"Timeout or error in parallel execution: {str(e)}")
            return None
                
    return results if len(results) == len(algorithms) else None

def execute_phase1(Arrival_rate, bp_parameter):
    """Execute phase 1 for normal data with modified path structure"""
    avg_statuses = ["avg_30", "avg_60", "avg_90"]
    
    for avg_status in avg_statuses:
        results = []
        for i in bp_parameter:
            try:
                # Modified file path to include avg_status directory
                file_path = f'data/{avg_status}/({Arrival_rate}, {i["L"]}).csv'
                
                # Read job list
                job_list = Read_csv.Read_csv(file_path)
                if not job_list:
                    continue

                # Set up algorithms including Dynamic and RFdynamic
                algorithms = [
                    (RR.RR, job_list.copy(), False, True),
                    (SRPT.Srpt, job_list.copy(), False, False),
                    (SETF.Setf, job_list.copy(), False, True),
                    (FCFS.Fcfs, job_list.copy(), False, False),
                    (RMLF.RMLF, job_list.copy(), True, False),
                    (Dynamic.DYNAMIC, job_list.copy(), False, False),
                    (RFdynamic.Rdynamic, job_list.copy(), True, False)
                ]
                
                # Run algorithms and collect results
                algorithm_results = run_all_algorithms_parallel(job_list, algorithms)
                if algorithm_results and all(v is not None for v in algorithm_results.values()):
                    results.append({
                        "arrival_rate": Arrival_rate,
                        "bp_parameter": {"L": i["L"], "H": i["H"]},  # Include both L and H values
                        "RR_L2_Norm": algorithm_results['RR'],
                        "SRPT_L2_Norm": algorithm_results['Srpt'],
                        "SETF_L2_Norm": algorithm_results['Setf'],
                        "FCFS_L2_Norm": algorithm_results['Fcfs'],
                        "RMLF_L2_Norm": algorithm_results['RMLF'],
                        "DYNAMIC_L2_Norm": algorithm_results['DYNAMIC'],
                        "Rdynamic_L2_Norm": algorithm_results['Rdynamic']
                    })
                else:
                    print(f"Failed to get results for {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                continue

        # Save results
        if results:
            # Create directory if it doesn't exist
            os.makedirs('phase1', exist_ok=True)
            
            df = pd.DataFrame(results)
            csv_filename = f'phase1/phase1_results_{avg_status}_{Arrival_rate}.csv'
            df.to_csv(csv_filename, index=False)
            print(f"Saved {len(results)} results to {csv_filename}")

def execute_phase1_random(Arrival_rates):
    """
    Execute phase 1 for frequency-based random data, combining results from 
    the same frequency but different arrival times
    
    Args:
        Arrival_rates: List of arrival rates to process
    """
    # Frequency folders from 1 to 10000
    freq_folders = [f"freq_{i}" for i in [1,10,100,500,1000,10000]]
    
    # Dictionary to store results for each frequency
    freq_results = {freq: [] for freq in freq_folders}
    
    # Process each frequency folder
    for freq_folder in freq_folders:
        print(f"Processing {freq_folder}...")
        
        # Process each arrival rate for this frequency
        for Arrival_rate in Arrival_rates:
            try:
                # Modified file path to include freq folder
                file_path = f'data/{freq_folder}/({Arrival_rate}).csv'
                
                # Read job list
                job_list = Read_csv.Read_csv(file_path)
                if not job_list:
                    print(f"No data found for {file_path}")
                    continue
                
                # Set up algorithms including Dynamic and RFdynamic
                algorithms = [
                    (RR.RR, job_list.copy(), False, True),
                    (SRPT.Srpt, job_list.copy(), False, False),
                    (SETF.Setf, job_list.copy(), False, True),
                    (FCFS.Fcfs, job_list.copy(), False, False),
                    (RMLF.RMLF, job_list.copy(), True, False),
                    (Dynamic.DYNAMIC, job_list.copy(), False, False),
                    (RFdynamic.Rdynamic, job_list.copy(), True, False)
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
                        "RMLF_L2_Norm": algorithm_results['RMLF'],
                        "DYNAMIC_L2_Norm": algorithm_results['DYNAMIC'],
                        "Rdynamic_L2_Norm": algorithm_results['Rdynamic']
                    }
                    
                    # Add result to the corresponding frequency list
                    freq_results[freq_folder].append(result_row)
                    print(f"Successfully processed {file_path}")
                else:
                    print(f"Failed to get results for {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                continue
    
    # Save combined results for each frequency
    for freq_folder, results in freq_results.items():
        if results:
            # Create directory if it doesn't exist
            os.makedirs('freq', exist_ok=True)
            
            df = pd.DataFrame(results)
            csv_filename = f'freq/{freq_folder}_combined_results.csv'
            df.to_csv(csv_filename, index=False)
            print(f"Saved combined results for {freq_folder} with {len(results)} arrival rates")

def execute_phase1_softrandom(Arrival_rates):
    """
    Execute phase 1 for softrandom frequency-based data, combining results from 
    the same frequency but different arrival times
    
    Args:
        Arrival_rates: List of arrival rates to process
    """
    # Frequency folders from freq_1 to freq_10000
    freq_folders = [f"freq_{i}" for i in [1,10,100,500,1000,10000]]
    
    # Dictionary to store results for each frequency
    freq_results = {freq: [] for freq in freq_folders}
    
    # Process each frequency folder
    for freq_folder in freq_folders:
        print(f"Processing softrandom/{freq_folder}...")
        
        # Process each arrival rate for this frequency
        for Arrival_rate in Arrival_rates:
            try:
                # Modified file path to include softrandom/freq folder
                file_path = f'data/softrandom/{freq_folder}/({Arrival_rate}).csv'
                
                # Read job list
                job_list = Read_csv.Read_csv(file_path)
                if not job_list:
                    print(f"No data found for {file_path}")
                    continue
                
                # Set up algorithms including Dynamic and RFdynamic
                algorithms = [
                    (RR.RR, job_list.copy(), False, True),
                    (SRPT.Srpt, job_list.copy(), False, False),
                    (SETF.Setf, job_list.copy(), False, True),
                    (FCFS.Fcfs, job_list.copy(), False, False),
                    (RMLF.RMLF, job_list.copy(), True, False),
                    (Dynamic.DYNAMIC, job_list.copy(), False, False),
                    (RFdynamic.Rdynamic, job_list.copy(), True, False)
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
                        "RMLF_L2_Norm": algorithm_results['RMLF'],
                        "DYNAMIC_L2_Norm": algorithm_results['DYNAMIC'],
                        "Rdynamic_L2_Norm": algorithm_results['Rdynamic']
                    }
                    
                    # Add result to the corresponding frequency list
                    freq_results[freq_folder].append(result_row)
                    print(f"Successfully processed {file_path}")
                else:
                    print(f"Failed to get results for {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                continue
    
    # Save combined results for each frequency
    for freq_folder, results in freq_results.items():
        if results:
            # Create directory if it doesn't exist
            os.makedirs('softrandom', exist_ok=True)
            
            df = pd.DataFrame(results)
            csv_filename = f'softrandom/{freq_folder}_combined_results.csv'
            df.to_csv(csv_filename, index=False)
            print(f"Saved combined results for softrandom/{freq_folder} with {len(results)} arrival rates")