import execute_standard
import tqdm
import pandas as pd
import logging
import os
import time
import multiprocessing

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_dataset():
    # Define arrival rates
    Arrival_rate = [i for i in range(20, 42, 2)]
    
    # Define parameters for different average statuses
    bp_parameter_30 = [
        {"L": 16.772, "H": pow(2, 6)},
        {"L": 7.918, "H": pow(2, 9)},
        {"L": 5.649, "H": pow(2, 12)},
        {"L": 4.639, "H": pow(2, 15)},
        {"L": 4.073, "H": pow(2, 18)}
    ]
    
    bp_parameter_60 = [
        {"L": 56.300, "H": pow(2, 6)},
        {"L": 18.900, "H": pow(2, 9)},
        {"L": 12.400, "H": pow(2, 12)},
        {"L": 9.800, "H": pow(2, 15)},
        {"L": 8.500, "H": pow(2, 18)}
    ]
    
    bp_parameter_90 = [
        {"L": 32.300, "H": pow(2, 9)},
        {"L": 19.700, "H": pow(2, 12)},
        {"L": 15.300, "H": pow(2, 15)},
        {"L": 13.000, "H": pow(2, 18)}
    ]
    
    # Create mapping of avg_status to parameter sets
    parameter_map = {
        "avg_30": bp_parameter_30,
        "avg_60": bp_parameter_60,
        "avg_90": bp_parameter_90
    }

    # Log system information for parallel processing
    cpu_count = multiprocessing.cpu_count()
    logger.info(f"System has {cpu_count} CPU cores available for parallel processing")
    logger.info("Processing with 8 algorithms: RR, SRPT, SETF, FCFS, RMLF, Dynamic, RFdynamic, BAL")

    # Create the log directory if it doesn't exist
    log_dir = "log"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create output directories
    os.makedirs("phase1", exist_ok=True)
    os.makedirs("freq", exist_ok=True)
    os.makedirs("softrandom", exist_ok=True)
    
    # Track overall progress
    total_tasks = len(parameter_map) * len(Arrival_rate) + 2  # phase1 + random + softrandom
    completed_tasks = 0
    
    logger.info(f"Starting dataset creation with {total_tasks} total tasks")
    
    # Process phase1 for each avg_status
    for avg_status, bp_parameter in parameter_map.items():
        logger.info(f"Processing {avg_status} data with {len(bp_parameter)} parameter sets...")
        start_time_phase = time.time()
        
        successful_arrivals = 0
        failed_arrivals = 0
        
        # Use tqdm for the arrival rates to show progress
        for i in tqdm.tqdm(Arrival_rate, desc=f"Processing {avg_status} arrival rates", leave=True):
            try:
                task_start = time.time()
                
                # Call execute_phase1 with the correct parameter set
                execute_standard.execute_phase1(i, bp_parameter)
                
                task_duration = time.time() - task_start
                successful_arrivals += 1
                completed_tasks += 1
                
                logger.info(f"Completed arrival rate {i} for {avg_status} in {task_duration:.2f}s "
                           f"({completed_tasks}/{total_tasks} total tasks)")
                
                # Small delay to prevent system overload
                time.sleep(0.1)
                
            except Exception as e:
                failed_arrivals += 1
                logger.error(f"Error processing arrival rate {i} for {avg_status}: {e}")
                continue
        
        phase_duration = time.time() - start_time_phase
        logger.info(f"Completed {avg_status}: {successful_arrivals} successful, "
                   f"{failed_arrivals} failed in {phase_duration:.2f}s")
    
    # Process phase1_random for all arrival rates at once
    logger.info("Processing frequency-based random data...")
    start_time_random = time.time()
    
    try:
        # Call execute_phase1_random with all arrival rates
        execute_standard.execute_phase1_random(Arrival_rate)
        
        random_duration = time.time() - start_time_random
        completed_tasks += 1
        logger.info(f"Completed random frequency data processing in {random_duration:.2f}s "
                   f"({completed_tasks}/{total_tasks} total tasks)")
    except Exception as e:
        logger.error(f"Error processing random frequency data: {e}")
    
    # Process softrandom data for all arrival rates at once
    logger.info("Processing softrandom frequency-based data...")
    start_time_softrandom = time.time()
    
    try:
        # Call execute_phase1_softrandom with all arrival rates
        execute_standard.execute_phase1_softrandom(Arrival_rate)
        
        softrandom_duration = time.time() - start_time_softrandom
        completed_tasks += 1
        logger.info(f"Completed softrandom frequency data processing in {softrandom_duration:.2f}s "
                   f"({completed_tasks}/{total_tasks} total tasks)")
    except Exception as e:
        logger.error(f"Error processing softrandom frequency data: {e}")

def validate_results():
    """Validate that results were generated correctly"""
    logger.info("Validating generated results...")
    
    # Check phase1 results
    phase1_files = []
    if os.path.exists("phase1"):
        phase1_files = [f for f in os.listdir("phase1") if f.endswith('.csv')]
        logger.info(f"Generated {len(phase1_files)} phase1 result files")
    
    # Check frequency results
    freq_files = []
    if os.path.exists("freq"):
        freq_files = [f for f in os.listdir("freq") if f.endswith('.csv')]
        logger.info(f"Generated {len(freq_files)} frequency result files")
    
    # Check softrandom results
    softrandom_files = []
    if os.path.exists("softrandom"):
        softrandom_files = [f for f in os.listdir("softrandom") if f.endswith('.csv')]
        logger.info(f"Generated {len(softrandom_files)} softrandom result files")
    
    # Validate column structure for a sample file
    if phase1_files:
        sample_file = os.path.join("phase1", phase1_files[0])
        try:
            df = pd.read_csv(sample_file)
            expected_columns = ['arrival_rate', 'bp_parameter', 'RR_L2_Norm', 'SRPT_L2_Norm', 
                              'SETF_L2_Norm', 'FCFS_L2_Norm', 'RMLF_L2_Norm', 
                              'DYNAMIC_L2_Norm', 'RFdynamic_L2_Norm', 'BAL_L2_Norm']
            
            missing_columns = [col for col in expected_columns if col not in df.columns]
            if missing_columns:
                logger.warning(f"Missing columns in results: {missing_columns}")
            else:
                logger.info("All expected algorithm columns present in results")
                logger.info(f"Sample file has {len(df)} rows")
        except Exception as e:
            logger.error(f"Error validating sample file {sample_file}: {e}")

if __name__ == "__main__":
    # Set start time
    start_time = time.time()
    
    logger.info("="*60)
    logger.info("STARTING DYNAMIC ALGORITHM DATASET CREATION")
    logger.info("="*60)
    
    try:
        # Create dataset
        create_dataset()
        
        # Validate results
        validate_results()
        
        # Calculate and log execution time
        execution_time = time.time() - start_time
        logger.info("="*60)
        logger.info(f"DATASET CREATION COMPLETED SUCCESSFULLY")
        logger.info(f"Total execution time: {execution_time:.2f} seconds ({execution_time/60:.2f} minutes)")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Critical error in main execution: {e}")
        execution_time = time.time() - start_time
        logger.error(f"Failed after {execution_time:.2f} seconds")
        raise