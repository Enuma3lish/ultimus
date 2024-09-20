import multiprocessing
import math
import csv
import Read_csv
import RR, SJF, SRPT, SETF, FCFS, MLFQ, RMLFQ, RMLF_bFCFS

def process_scheduler(func, job_list):
    # Execute the function (algorithm) and return its result
    return func(job_list)

def scheduler_algorithm(job_list, algorithms):
    # Run all algorithms and use the one with the best L2 norm flow time in each round
    results = []
    with multiprocessing.Pool(processes=len(algorithms)) as pool:
        results = pool.starmap(process_scheduler, [(algo, job_list) for algo in algorithms.values()])
    # Find the algorithm with the minimum L2 norm flow time
    l2_norms = [result[1] for result in results]  # Get the L2 norm flow times
    best_index = l2_norms.index(min(l2_norms))
    best_algorithm = list(algorithms.keys())[best_index]  # Get the name of the best algorithm
    return results[best_index], best_algorithm  # Return the best algorithm's result and its name

def scheduler(arrival_rates, bp_parameters):
    # CSV file output name for scheduler usage record
    usage_record_file = "scheduler_usage_record.csv"
    
    # Initialize an empty list to store the results for each run
    result_list = []

    # Open the CSV file for writing the scheduler usage
    with open(usage_record_file, mode='w', newline='') as usage_file:
        usage_writer = csv.writer(usage_file)
        usage_writer.writerow(["arrival_rate", "bp_parameter", "chosen_algorithm"])  # Header for usage record CSV

        # Iterate over arrival_rates and bp_parameters
        for bp_param in bp_parameters:
            print(f"Processing Arrival_rate: {arrival_rates}, bp_parameter: {bp_param}")

            job_list = Read_csv.Read_csv('data/' + str((arrival_rates, bp_param["L"])) + ".csv")
            #N = int(math.log2(len(job_list)))
            N = len(job_list)
            remaining_jobs = len(job_list)

            algorithms = {
                "SJF": SJF.Sjf,
                "RR": RR.Rr,
                "MLFQ": MLFQ.Mlfq,
                "RMLFQ": RMLFQ.Rmlfq,
                "SETF": SETF.Setf,
                "FCFS": FCFS.Fcfs,
                "SRPT": SRPT.Srpt,
                "RMLF_bFCFS": RMLF_bFCFS.Rmlf_bFCFS
            }

            while remaining_jobs > 0:
                jobs_to_run = min(N, remaining_jobs)
                job_batch = job_list[:jobs_to_run]
                job_list = job_list[jobs_to_run:]
                remaining_jobs -= jobs_to_run

                # Run all algorithms in parallel on the current batch of jobs
                with multiprocessing.Pool(processes=len(algorithms)) as pool:
                    results = pool.starmap(process_scheduler, [(algo, job_batch) for algo in algorithms.values()])

                # Collect the results: (avg_flow_time, l2_norm_flow_time) tuples for each algorithm
                metrics = {}
                for algo_name, result in zip(algorithms.keys(), results):
                    avg_flow_time, l2_norm_flow_time = result
                    metrics[algo_name] = (avg_flow_time, l2_norm_flow_time)

                # Run the scheduler
                scheduler_result, chosen_algorithm = scheduler_algorithm(job_batch, algorithms)
                scheduler_avg = scheduler_result[0]
                scheduler_l2n = scheduler_result[1]

                # Write the chosen algorithm to the CSV file
                usage_writer.writerow([arrival_rates, str(bp_param), chosen_algorithm])

                # Handle division by zero or null values
                def safe_divide(numerator, denominator):
                    if denominator == 0 or denominator is None or numerator is None:
                        return None  # or some default value like float('inf') or 0
                    return numerator / denominator

                # Calculate ratios
                srpt_avg = metrics["SRPT"][0]
                srpt_l2n = metrics["SRPT"][1]
                fcfs_avg = metrics["FCFS"][0]
                fcfs_l2n = metrics["FCFS"][1]
                rr_avg = metrics["RR"][0]
                rr_l2n = metrics["RR"][1]

                # Build the row of results (no writing to CSV here)
                row = [
                    arrival_rates, str(bp_param),  # Use dynamic arrival_rate and bp_param
                    safe_divide(metrics["SJF"][0], srpt_avg),  # SJF/SRPT
                    safe_divide(rr_avg, srpt_avg),  # RR/SRPT
                    safe_divide(metrics["MLFQ"][0], srpt_avg),  # MLFQ/SRPT
                    safe_divide(metrics["RMLFQ"][0], srpt_avg),  # RMLFQ/SRPT
                    safe_divide(metrics["SETF"][0], srpt_avg),  # SETF/SRPT
                    safe_divide(fcfs_avg, srpt_avg),  # FCFS/SRPT
                    safe_divide(metrics["SJF"][0], fcfs_avg),  # SJF/FCFS
                    safe_divide(rr_avg, fcfs_avg),  # RR/FCFS
                    safe_divide(metrics["MLFQ"][0], fcfs_avg),  # MLFQ/FCFS
                    safe_divide(metrics["RMLFQ"][0], fcfs_avg),  # RMLFQ/FCFS
                    safe_divide(metrics["SETF"][0], fcfs_avg),  # SETF/FCFS
                    safe_divide(srpt_avg, fcfs_avg),  # SPRT/FCFS
                    safe_divide(metrics["SJF"][1], srpt_l2n),  # SJF_L2_Norm/SRPT_L2_Norm
                    safe_divide(rr_l2n, srpt_l2n),  # RR_L2_Norm/SRPT_L2_Norm
                    safe_divide(metrics["MLFQ"][1], srpt_l2n),  # MLFQ_L2_Norm/SRPT_L2_Norm
                    safe_divide(metrics["RMLFQ"][1], srpt_l2n),  # RMLFQ_L2_Norm/SRPT_L2_Norm
                    safe_divide(metrics["SETF"][1], srpt_l2n),  # SETF_L2_Norm/SRPT_L2_Norm
                    safe_divide(fcfs_l2n, srpt_l2n),  # FCFS_L2_Norm/SRPT_L2_Norm
                    safe_divide(metrics["SJF"][1], fcfs_l2n),  # SJF_L2_Norm/FCFS_L2_Norm
                    safe_divide(rr_l2n, fcfs_l2n),  # RR_L2_Norm/FCFS_L2_Norm
                    safe_divide(metrics["MLFQ"][1], fcfs_l2n),  # MLFQ_L2_Norm/FCFS_L2_Norm
                    safe_divide(metrics["RMLFQ"][1], fcfs_l2n),  # RMLFQ_L2_Norm/FCFS_L2_Norm
                    safe_divide(rr_l2n, metrics["SETF"][1]),  # RR_L2_Norm/SETF_L2_Norm
                    safe_divide(scheduler_avg, srpt_avg),  # Scheduler/SRPT
                    safe_divide(scheduler_avg, fcfs_avg),  # Scheduler/FCFS
                    safe_divide(scheduler_l2n, srpt_l2n),  # Scheduler_L2_Norm/SRPT_L2_Norm
                    safe_divide(scheduler_l2n, fcfs_l2n)  # Scheduler_L2_Norm/FCFS_L2_Norm
                ]

                # Append the row to the result list (which is returned)
                result_list.append(row)

    # Return the results (list of calculated metrics)
    return result_list