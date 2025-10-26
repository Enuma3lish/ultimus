import csv
import time

def Checker(input_filename, schedule_filename):
    with open(input_filename, 'r') as file:
        reader = csv.DictReader(file)
        job_id = 0
        for row in reader:
            # Check if the job is feasible using job_id instead of job_index
            if checkIfJobFeasible(schedule_filename, job_id, row["arrival_time"], row["job_size"]) == False:
                return False
            job_id += 1  # Increment job_id after each job
        return True

def checkIfJobFeasible(schedule_filename, job_id, job_arrival_time, job_size) -> bool:
    with open(schedule_filename, 'r') as file:
        reader = csv.DictReader(file)
        has_encountered_first_execution = False
        execution_slot = 0
        for row in reader:
            if row["executed_job_id"] == '':  # Check executed_job_id
                continue
            if job_id == int(row["executed_job_id"]):  # Compare job_id instead of job_index
                if not has_encountered_first_execution:
                    has_encountered_first_execution = True
                    if float(row['time_slot']) < float(job_arrival_time):
                        print(f"Job {job_id} starts too early.")
                        return False
                execution_slot += 1
        
        if execution_slot != int(job_size):
            print(f"Job {job_id} size mismatch: executed {execution_slot}, expected {job_size}.")
            return False
    return True    
# Run the Checker function
# result = Checker('data/(20, 4.073).csv', 'Rdy_time_slot_log.csv')
# print(result)