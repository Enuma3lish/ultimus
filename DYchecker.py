import csv

def validate_job_logs(file_path):
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        all_correct = True
        for row in reader:
            job_id = row['job_id']
            arrival_time = float(row['arrival_time'])
            start_time = float(row['start_time'])
            completion_time = float(row['completion_time'])
            job_size = float(row['job_size'])
            execution_time = completion_time - start_time
            is_execution_time_correct = row['is_execution_time_correct'].lower() == 'true'

            # Check if execution time is correct
            if not is_execution_time_correct or execution_time != job_size:
                print(f"Job {job_id}: Execution time incorrect. Expected {job_size}, got {execution_time}")
                all_correct = False

            # Check if start_time is >= arrival_time
            if start_time < arrival_time:
                print(f"Job {job_id}: Start time ({start_time}) is before arrival time ({arrival_time})")
                all_correct = False

            # Check if completion_time is >= arrival_time
            if completion_time < arrival_time:
                print(f"Job {job_id}: Completion time ({completion_time}) is before arrival time ({arrival_time})")
                all_correct = False

    if all_correct:
        print("All jobs passed the validation checks.")
    else:
        print("Some jobs failed the validation checks.")

# Usage
file_path = 'job_logs.csv'  # Replace with your CSV file path
validate_job_logs(file_path)