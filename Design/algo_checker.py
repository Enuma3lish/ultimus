def check_schedule(jobs, job_schedules):
    """Checks the job schedules for the following conditions:
    1. The first executed time for each job is >= its arrival time.
    2. Each job is finished in the record.
    3. The system is not idle when there are jobs available.

    Args:
        jobs: List of [arrival_time, job_size] pairs.
        job_schedules: A dictionary with each job's index as the key and a list of (start_time, end_time) tuples as the value.

    Returns:
        bool: True if all conditions are met, False otherwise.
    """
    for i, (arrival_time, job_size) in enumerate(jobs):
        schedule = job_schedules[i]
        if not schedule:
            return False

        # Check the first executed time is >= arrival time
        if schedule[0][0] < arrival_time:
            print(f"Job {i}: first execution time {schedule[0][0]} is less than arrival time {arrival_time}")
            return False

        # Check the job is finished in the record
        total_executed_time = sum(end - start for start, end in schedule)
        if total_executed_time != job_size:
            print(f"Job {i}: total executed time {total_executed_time} does not match job size {job_size}")
            return False

    # Check system not idle when jobs are available
    current_time = 0
    for job_index, schedule in job_schedules.items():
        for start_time, end_time in schedule:
            if start_time > current_time and any(arrival_time <= current_time for arrival_time, _ in jobs):
                print(f"System is idle at time {current_time} while jobs are available")
                return False
            current_time = end_time

    return True