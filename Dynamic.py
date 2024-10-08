import multiprocessing
import csv
import os
from SRPT import Srpt  # Import your SRPT function
from FCFS import Fcfs  # Import your FCFS function
import re
from collections import defaultdict

# Define the bp_parameter values
bp_parameter_values = [
    {"L": 16.772, "H": pow(2, 6)},
    {"L": 7.918, "H": pow(2, 9)},
    {"L": 5.649, "H": pow(2, 12)},
    {"L": 4.639, "H": pow(2, 15)},
    {"L": 4.073, "H": pow(2, 18)}
]

# List to store the results for sorting and final output
results_list = []

# Track job arrivals for checkpoint
job_arrival_count = 0


def fetch_results(result_queue):
    """Fetch results from the result queue."""
    results = []
    while not result_queue.empty():
        results.append(result_queue.get())
    return results


def simulate_srpt(jobs, result_queue):
    """Simulate SRPT scheduling and send results to the result queue."""
    avg_flow_time, l2_norm_flow_time = Srpt(jobs)
    result_queue.put(('SRPT', avg_flow_time, l2_norm_flow_time))


def simulate_fcfs(jobs, result_queue):
    """Simulate FCFS scheduling and send results to the result queue."""
    avg_flow_time, l2_norm_flow_time = Fcfs(jobs)
    result_queue.put(('FCFS', avg_flow_time, l2_norm_flow_time))


def simulate_dynamic(jobs, dynamic_policy, result_queue):
    """Simulate Dynamic scheduling and send results to the result queue."""
    if dynamic_policy == 'SRPT':
        avg_flow_time, l2_norm_flow_time = Srpt(jobs)
    else:
        avg_flow_time, l2_norm_flow_time = Fcfs(jobs)
    result_queue.put(('DYNAMIC', avg_flow_time, l2_norm_flow_time))


def switch_dynamic_policy(result_queue):
    """Switch the dynamic policy based on the results from SRPT and FCFS."""
    srpt_result = None
    fcfs_result = None

    results = fetch_results(result_queue)
    for policy, avg_flow_time, l2_norm_flow_time in results:
        if policy == 'SRPT':
            srpt_result = (avg_flow_time, l2_norm_flow_time)
        elif policy == 'FCFS':
            fcfs_result = (avg_flow_time, l2_norm_flow_time)

    if srpt_result and fcfs_result:
        fcfs_l2_norm = fcfs_result[1]
        srpt_l2_norm = srpt_result[1]
        # Switch dynamic policy based on the smaller L2 norm
        dynamic_policy = 'FCFS' if fcfs_l2_norm < srpt_l2_norm else 'SRPT'
        return dynamic_policy, srpt_result, fcfs_result
    return None, None, None


def add_to_results_list(inter_arrival_time, bp_param, fcfs_result, srpt_result, dynamic_result):
    """Add the results to a list for sorting later."""
    fcfs_avg_time, fcfs_l2_norm = fcfs_result
    srpt_avg_time, srpt_l2_norm = srpt_result
    dynamic_algo, dynamic_avg_time, dynamic_l2_norm = dynamic_result

    # Ratios for comparison
    fcfs_dynamic_ratio = 1.0 if fcfs_l2_norm == 0 else dynamic_l2_norm / fcfs_l2_norm
    srpt_dynamic_ratio = 1.0 if srpt_l2_norm == 0 else dynamic_l2_norm / srpt_l2_norm

    # Append the result as a tuple (bp_param stays as dict)
    results_list.append((
        inter_arrival_time,
        bp_param,  # Store bp_param as dict for direct comparison
        fcfs_avg_time,
        srpt_avg_time,
        fcfs_l2_norm,
        srpt_l2_norm,
        dynamic_avg_time,
        dynamic_l2_norm,
        fcfs_dynamic_ratio,
        srpt_dynamic_ratio
    ))


def process_file(file_path, inter_arrival_time, bp_param, checkpoint_job_count):
    """Processes a single CSV file and adds the results to the list, stopping at checkpoint."""
    jobs = read_jobs_from_csv(file_path)

    if jobs:
        # Monitor job arrivals for the checkpoint
        global job_arrival_count
        job_arrival_count = 0

        def monitor_arrivals():
            """Monitor job arrivals and stop when checkpoint is reached."""
            global job_arrival_count
            for job in jobs:
                job_arrival_count += 1
                if job_arrival_count >= checkpoint_job_count:
                    print(f"Checkpoint reached: {checkpoint_job_count} jobs have arrived.")
                    break

        monitor_arrivals()

        # After the checkpoint is reached, we run both SRPT and FCFS
        result_queue = multiprocessing.Queue()

        # Run SRPT and FCFS simulations in parallel
        srpt_process = multiprocessing.Process(target=simulate_srpt, args=(jobs[:checkpoint_job_count], result_queue))
        fcfs_process = multiprocessing.Process(target=simulate_fcfs, args=(jobs[:checkpoint_job_count], result_queue))

        srpt_process.start()
        fcfs_process.start()

        srpt_process.join()
        fcfs_process.join()

        # Switch dynamic policy based on results and write first round results
        dynamic_policy, srpt_result, fcfs_result = switch_dynamic_policy(result_queue)
        if dynamic_policy:
            # First round: Run SRPT as Dynamic (explicitly label as 'DYNAMIC')
            dynamic_result_first_round = ('DYNAMIC', srpt_result[0], srpt_result[1])
            add_to_results_list(inter_arrival_time, bp_param, fcfs_result, srpt_result, dynamic_result_first_round)

            # Second round: Dynamic chooses between FCFS or SRPT based on smaller L2 norm
            dynamic_process = multiprocessing.Process(target=simulate_dynamic, args=(jobs[:checkpoint_job_count], dynamic_policy, result_queue))
            dynamic_process.start()
            dynamic_process.join()

            # Fetch the dynamic results
            dynamic_results = fetch_results(result_queue)
            dynamic_algo, dynamic_avg_time, dynamic_l2_norm = next(
                (res for res in dynamic_results if res[0] == 'DYNAMIC'), (None, None, None)
            )

            if dynamic_algo:
                # Prepare the dynamic result tuple
                dynamic_result = (dynamic_algo, dynamic_avg_time, dynamic_l2_norm)
                # Add the second round results to the list
                add_to_results_list(inter_arrival_time, bp_param, fcfs_result, srpt_result, dynamic_result)


def read_jobs_from_csv(filename):
    """Reads job data from a CSV file."""
    jobs = []
    with open(filename, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            arrival_time = float(row['arrival_time'])
            job_size = float(row['job_size'])
            jobs.append({'arrival_time': arrival_time, 'job_size': job_size})
    return jobs


def parse_filename(filename):
    """Extracts inter-arrival time from the filename."""
    match = re.match(r"\((\d+),\s*([\d\.]+)\)\.csv", filename)
    if match:
        inter_arrival_time = int(match.group(1))
        return inter_arrival_time
    return None


def process_directory(directory, checkpoint_job_count):
    """Processes all CSV files in a given directory, using the correct bp_parameter."""
    for index, filename in enumerate(sorted(os.listdir(directory))):  # Ensure files are processed in order
        if filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)

            # Parse inter-arrival time from the filename
            inter_arrival_time = parse_filename(filename)

            if inter_arrival_time is not None:
                # Use the corresponding bp_parameter for this file
                bp_param = bp_parameter_values[index % len(bp_parameter_values)]
                process_file(file_path, inter_arrival_time, bp_param, checkpoint_job_count)


def compute_average_for_duplicates():
    """Compute the average of duplicate rows with the same arrival time and bp_parameter."""
    # Dict to hold aggregated sums and counts
    combined_results = defaultdict(lambda: [0.0] * (len(results_list[0]) - 2) + [0])

    for result in results_list:
        key = (result[0], tuple(sorted(result[1].items())))  # (arrival_rate, bp_parameter as tuple for immutability)
        for i in range(2, len(result)):
            combined_results[key][i - 2] += result[i]  # Sum the numeric columns
        combined_results[key][-1] += 1  # Count occurrences

    # Compute the averages
    averaged_results = []
    for key, values in combined_results.items():
        count = values[-1]
        averaged_values = [v / count for v in values[:-1]]  # Calculate the average for numeric values
        bp_param = dict(key[1])  # Convert bp_parameter back from tuple to dict
        averaged_results.append((key[0], bp_param, *averaged_values))

    return averaged_results


def write_sorted_results_to_csv(checkpoint):
    """Sort the results by arrival time and bp_parameter['L'], and write them to the CSV."""
    # Compute averages for duplicates
    averaged_results = compute_average_for_duplicates()

    # Sort the results by arrival time and then by bp_param['L']
    sorted_results = sorted(averaged_results, key=lambda x: (x[0], x[1]['L']))

    # Ensure the 'log' directory exists
    os.makedirs('log', exist_ok=True)

    # Write the sorted results to a combined CSV file
    combined_file = os.path.join('log', f"{checkpoint}_combined_results.csv")
    with open(combined_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow([
            'arrival_rate', 'bp_parameter', 'FCFS_Avg_Flow_Time', 'SRPT_Avg_Flow_Time',
            'FCFS_L2_Norm', 'SRPT_L2_Norm', 'Dynamic_Avg_Flow_Time',
            'Dynamic_L2_Norm', 'Dynamic_L2_Norm_vs_FCFS', 'Dynamic_L2_Norm_vs_SRPT'
        ])
        # Write the sorted results
        for result in sorted_results:
            writer.writerow([
                result[0],  # arrival_rate
                f"{{'L': {result[1]['L']:.3f}, 'H': {result[1]['H']}}}",  # bp_parameter
                *result[2:]  # All remaining columns
            ])


def main():
    directory = "data"  # Replace with your directory containing CSV files
    # checkpoint_job_count = int(input("Enter the number of jobs to arrive before checkpoint: "))
    check = [2 ** i for i in range(4, 12, 1)]
    print(check)
    for c in check:
        process_directory(directory, c)
        # After processing all files, sort and write the results to CSV
        write_sorted_results_to_csv(c)


if __name__ == "__main__":
    main()