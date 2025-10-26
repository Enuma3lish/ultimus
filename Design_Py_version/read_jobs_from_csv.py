import csv
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def read_jobs_from_csv(filepath):
    """Read jobs from CSV file"""
    jobs = []
    try:
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                job = {
                    'arrival_time': int(row['arrival_time']),
                    'job_size': int(row['job_size'])
                }
                jobs.append(job)
        logger.info(f"Successfully read {len(jobs)} jobs from {filepath}")
        return jobs
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return None