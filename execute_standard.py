import multiprocessing
import Read_csv
import RR, SRPT, SETF, FCFS, RMLF, Dynamic, RFdynamic_C, RFdynamic_NC, BAL, SJF
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

def run_algorithm(algo, jobs, needs_index, as_list, **kwargs):
    """Run a single algorithm with optional parameters"""
    if not jobs:
        return None
    try:
        converted_jobs = convert_jobs(jobs.copy(), include_index=needs_index, as_list=as_list)
        _, l2n = algo(converted_jobs, **kwargs)
        return l2n
    except Exception as e:
        print(f"Error running algorithm {algo.__name__}: {str(e)}")
        return None

def run_all_algorithms_parallel(job_list, algorithms):
    """Run all algorithms in parallel"""
    results = {}
    with ProcessPoolExecutor(max_workers=len(algorithms)) as executor:
        future_to_algo = {}
        for algo_info in algorithms:
            if not job_list:
                return None
            algo = algo_info[0]
            jobs = algo_info[1]
            needs_index = algo_info[2]
            as_list = algo_info[3]
            kwargs = algo_info[4] if len(algo_info) > 4 else {}
            
            future = executor.submit(run_algorithm, algo, jobs, needs_index, as_list, **kwargs)
            # Create unique key for algorithms with parameters
            if kwargs:
                algo_key = f"{algo.__name__}"
                if 'mode' in kwargs:
                    algo_key += f"_mode{kwargs['mode']}"
                if 'nJobsPerRound' in kwargs:
                    algo_key += f"_njobs{kwargs['nJobsPerRound']}"
                if 'checkpoint' in kwargs:
                    algo_key += f"_cp{kwargs['checkpoint']}"
            else:
                algo_key = algo.__name__
            future_to_algo[future] = algo_key

        try:
            for future in as_completed(future_to_algo, timeout=30000):
                algo_name = future_to_algo[future]
                l2n = future.result(timeout=1200)
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

                # Test different parameter combinations for Dynamic, RFdynamic_C, RFdynamic_NC
                modes = [1, 2, 3]
                njobs_per_round = [10, 100, 500, 1000, 5000, 10000]
                checkpoints = [100, 500, 1000, 5000, 10000]
                
                # Base algorithms (without parameters)
                base_algorithms = [
                    (RR.RR, job_list.copy(), False, True, {}),
                    (SRPT.Srpt, job_list.copy(), False, False, {}),
                    (SETF.Setf, job_list.copy(), False, True, {}),
                    (FCFS.Fcfs, job_list.copy(), False, False, {}),
                    (RMLF.RMLF, job_list.copy(), True, False, {}),
                    (BAL.Bal, job_list.copy(), False, False, {}),
                    (SJF.Sjf, job_list.copy(), False, True, {})
                ]
                
                # Run base algorithms
                base_results = run_all_algorithms_parallel(job_list, base_algorithms)
                
                if not base_results or not all(v is not None for v in base_results.values()):
                    print(f"Failed to get base results for {file_path}")
                    continue
                
                # Test Dynamic with different parameters
                for mode in modes:
                    for njobs in njobs_per_round:
                        dynamic_algo = [
                            (Dynamic.DYNAMIC, job_list.copy(), False, False, 
                             {'nJobsPerRound': njobs, 'mode': mode, 'input_file_name': file_path})
                        ]
                        dynamic_result = run_all_algorithms_parallel(job_list, dynamic_algo)
                        
                        if dynamic_result:
                            key = f"DYNAMIC_mode{mode}_njobs{njobs}"
                            base_results[key] = list(dynamic_result.values())[0]
                
                # Test RFdynamic_C and RFdynamic_NC with different parameters
                for mode in modes:
                    for checkpoint in checkpoints:
                        # RFdynamic_C
                        rfc_algo = [
                            (RFdynamic_C.RFdynamic_C, job_list.copy(), True, False,
                             {'checkpoint': checkpoint, 'mode': mode, 'input_filename': file_path})
                        ]
                        rfc_result = run_all_algorithms_parallel(job_list, rfc_algo)
                        
                        if rfc_result:
                            key = f"RFdynamic_C_mode{mode}_cp{checkpoint}"
                            base_results[key] = list(rfc_result.values())[0]
                        
                        # RFdynamic_NC
                        rfnc_algo = [
                            (RFdynamic_NC.RFdynamic_NC, job_list.copy(), True, False,
                             {'checkpoint': checkpoint, 'mode': mode, 'input_filename': file_path})
                        ]
                        rfnc_result = run_all_algorithms_parallel(job_list, rfnc_algo)
                        
                        if rfnc_result:
                            key = f"RFdynamic_NC_mode{mode}_cp{checkpoint}"
                            base_results[key] = list(rfnc_result.values())[0]
                
                # Create result dictionary
                result_entry = {
                    "arrival_rate": Arrival_rate,
                    "bp_parameter_L": i["L"],
                    "bp_parameter_H": i["H"]
                }
                result_entry.update(base_results)
                results.append(result_entry)
                
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

def execute_phase1_random(freq_folders):
    """
    Execute phase 1 for frequency-based random data
    
    Args:
        freq_folders: List of frequency folders to process
    """
    all_results = []
    
    # Process each frequency folder
    for freq_folder in freq_folders:
        print(f"Processing random {freq_folder}...")
        
        try:
            # Modified file path for random frequency data
            file_path = f'data/{freq_folder}/random_{freq_folder}.csv'
            
            # Read job list
            job_list = Read_csv.Read_csv(file_path)
            if not job_list:
                print(f"No data found for {file_path}")
                continue
            
            # Test different parameter combinations
            modes = [1, 2, 3]
            njobs_per_round = [10, 100, 500, 1000, 5000, 10000]
            checkpoints = [100, 500, 1000, 5000, 10000]
            
            # Base algorithms
            base_algorithms = [
                (RR.RR, job_list.copy(), False, True, {}),
                (SRPT.Srpt, job_list.copy(), False, False, {}),
                (SETF.Setf, job_list.copy(), False, True, {}),
                (FCFS.Fcfs, job_list.copy(), False, False, {}),
                (RMLF.RMLF, job_list.copy(), True, False, {}),
                (BAL.Bal, job_list.copy(), False, False, {}),
                (SJF.Sjf, job_list.copy(), False, True, {})
            ]
            
            # Run base algorithms
            base_results = run_all_algorithms_parallel(job_list, base_algorithms)
            
            if not base_results or not all(v is not None for v in base_results.values()):
                print(f"Failed to get base results for {file_path}")
                continue
            
            # Test Dynamic with different parameters
            for mode in modes:
                for njobs in njobs_per_round:
                    dynamic_algo = [
                        (Dynamic.DYNAMIC, job_list.copy(), False, False, 
                         {'nJobsPerRound': njobs, 'mode': mode, 'input_file_name': file_path})
                    ]
                    dynamic_result = run_all_algorithms_parallel(job_list, dynamic_algo)
                    
                    if dynamic_result:
                        key = f"DYNAMIC_mode{mode}_njobs{njobs}"
                        base_results[key] = list(dynamic_result.values())[0]
            
            # Test RFdynamic_C and RFdynamic_NC with different parameters
            for mode in modes:
                for checkpoint in checkpoints:
                    # RFdynamic_C
                    rfc_algo = [
                        (RFdynamic_C.RFdynamic_C, job_list.copy(), True, False,
                         {'checkpoint': checkpoint, 'mode': mode, 'input_filename': file_path})
                    ]
                    rfc_result = run_all_algorithms_parallel(job_list, rfc_algo)
                    
                    if rfc_result:
                        key = f"RFdynamic_C_mode{mode}_cp{checkpoint}"
                        base_results[key] = list(rfc_result.values())[0]
                    
                    # RFdynamic_NC
                    rfnc_algo = [
                        (RFdynamic_NC.RFdynamic_NC, job_list.copy(), True, False,
                         {'checkpoint': checkpoint, 'mode': mode, 'input_filename': file_path})
                    ]
                    rfnc_result = run_all_algorithms_parallel(job_list, rfnc_algo)
                    
                    if rfnc_result:
                        key = f"RFdynamic_NC_mode{mode}_cp{checkpoint}"
                        base_results[key] = list(rfnc_result.values())[0]
            
            # Create result entry
            result_entry = {"frequency": freq_folder}
            result_entry.update(base_results)
            all_results.append(result_entry)
            
            print(f"Successfully processed random {freq_folder}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            continue
    
    # Save merged results for all random frequencies
    if all_results:
        # Create directory if it doesn't exist
        os.makedirs('result', exist_ok=True)
        
        df = pd.DataFrame(all_results)
        csv_filename = 'result/random_result.csv'
        df.to_csv(csv_filename, index=False)
        print(f"Saved merged random results to {csv_filename} with {len(all_results)} frequency configurations")

def execute_phase1_softrandom(freq_folders):
    """
    Execute phase 1 for softrandom frequency-based data
    
    Args:
        freq_folders: List of frequency folders to process
    """
    all_results = []
    
    # Process each frequency folder
    for freq_folder in freq_folders:
        print(f"Processing softrandom {freq_folder}...")
        
        try:
            # Modified file path for softrandom frequency data
            file_path = f'data/softrandom/{freq_folder}/softrandom_{freq_folder}.csv'
            
            # Read job list
            job_list = Read_csv.Read_csv(file_path)
            if not job_list:
                print(f"No data found for {file_path}")
                continue
            
            # Test different parameter combinations
            modes = [1, 2, 3]
            njobs_per_round = [10, 100, 500, 1000, 5000, 10000]
            checkpoints = [100, 500, 1000, 5000, 10000]
            
            # Base algorithms
            base_algorithms = [
                (RR.RR, job_list.copy(), False, True, {}),
                (SRPT.Srpt, job_list.copy(), False, False, {}),
                (SETF.Setf, job_list.copy(), False, True, {}),
                (FCFS.Fcfs, job_list.copy(), False, False, {}),
                (RMLF.RMLF, job_list.copy(), True, False, {}),
                (BAL.Bal, job_list.copy(), False, False, {}),
                (SJF.Sjf, job_list.copy(), False, True, {})
            ]
            
            # Run base algorithms
            base_results = run_all_algorithms_parallel(job_list, base_algorithms)
            
            if not base_results or not all(v is not None for v in base_results.values()):
                print(f"Failed to get base results for {file_path}")
                continue
            
            # Test Dynamic with different parameters
            for mode in modes:
                for njobs in njobs_per_round:
                    dynamic_algo = [
                        (Dynamic.DYNAMIC, job_list.copy(), False, False, 
                         {'nJobsPerRound': njobs, 'mode': mode, 'input_file_name': file_path})
                    ]
                    dynamic_result = run_all_algorithms_parallel(job_list, dynamic_algo)
                    
                    if dynamic_result:
                        key = f"DYNAMIC_mode{mode}_njobs{njobs}"
                        base_results[key] = list(dynamic_result.values())[0]
            
            # Test RFdynamic_C and RFdynamic_NC with different parameters
            for mode in modes:
                for checkpoint in checkpoints:
                    # RFdynamic_C
                    rfc_algo = [
                        (RFdynamic_C.RFdynamic_C, job_list.copy(), True, False,
                         {'checkpoint': checkpoint, 'mode': mode, 'input_filename': file_path})
                    ]
                    rfc_result = run_all_algorithms_parallel(job_list, rfc_algo)
                    
                    if rfc_result:
                        key = f"RFdynamic_C_mode{mode}_cp{checkpoint}"
                        base_results[key] = list(rfc_result.values())[0]
                    
                    # RFdynamic_NC
                    rfnc_algo = [
                        (RFdynamic_NC.RFdynamic_NC, job_list.copy(), True, False,
                         {'checkpoint': checkpoint, 'mode': mode, 'input_filename': file_path})
                    ]
                    rfnc_result = run_all_algorithms_parallel(job_list, rfnc_algo)
                    
                    if rfnc_result:
                        key = f"RFdynamic_NC_mode{mode}_cp{checkpoint}"
                        base_results[key] = list(rfnc_result.values())[0]
            
            # Create result entry
            result_entry = {"frequency": freq_folder}
            result_entry.update(base_results)
            all_results.append(result_entry)
            
            print(f"Successfully processed softrandom {freq_folder}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            continue
    
    # Save merged results for all softrandom frequencies
    if all_results:
        # Create directory if it doesn't exist
        os.makedirs('result', exist_ok=True)
        
        df = pd.DataFrame(all_results)
        csv_filename = 'result/softrandom_result.csv'
        df.to_csv(csv_filename, index=False)
        print(f"Saved merged softrandom results to {csv_filename} with {len(all_results)} frequency configurations")
