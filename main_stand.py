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

# ============== CONFIGURATION SECTION ==============
# Easily modify this section to control which tests to run

# Set to True to enable testing for each parameter set
TEST_AVG_30 = True  # Currently enabled
TEST_AVG_60 = False  # Set to True when needed
TEST_AVG_90 = False  # Set to True when needed
TEST_RANDOM = True  # Currently enabled
TEST_SOFTRANDOM = True  # Currently enabled

# Define frequency folders for random/softrandom testing
FREQ_FOLDERS = ["freq_1", "freq_10", "freq_100", "freq_500", "freq_1000", "freq_10000"]

# Define arrival rates
ARRIVAL_RATES = [i for i in range(20, 42, 2)]

# ============== END CONFIGURATION SECTION ==============

def create_dataset():
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
    
    # Create mapping of avg_status to parameter sets based on configuration
    parameter_map = {}
    if TEST_AVG_30:
        parameter_map["avg_30"] = bp_parameter_30
    if TEST_AVG_60:
        parameter_map["avg_60"] = bp_parameter_60
    if TEST_AVG_90:
        parameter_map["avg_90"] = bp_parameter_90

    # Log system information for parallel processing
    cpu_count = multiprocessing.cpu_count()
    logger.info(f"System has {cpu_count} CPU cores available for parallel processing")
    
    # Log which tests are enabled
    enabled_tests = []
    if TEST_AVG_30:
        enabled_tests.append("avg_30")
    if TEST_AVG_60:
        enabled_tests.append("avg_60")
    if TEST_AVG_90:
        enabled_tests.append("avg_90")
    if TEST_RANDOM:
        enabled_tests.append("random")
    if TEST_SOFTRANDOM:
        enabled_tests.append("softrandom")
    
    logger.info(f"Enabled tests: {', '.join(enabled_tests)}")
    logger.info("Processing with algorithms: RR, SRPT, SETF, FCFS, RMLF, SJF, BAL, RFdynamic")
    logger.info("Testing Dynamic with modes [1,2,3] and nJobsPerRound [10,100,500,1000,5000,10000]")
    logger.info("Testing RFdynamic_C and RFdynamic_NC with modes [1,2,3] and checkpoints [100,500,1000,5000,10000]")

    # Create the log directory if it doesn't exist
    log_dir = "log"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create output directories
    os.makedirs("phase1", exist_ok=True)
    os.makedirs("result", exist_ok=True)  # Changed from freq and softrandom to result
    os.makedirs("Dynamic_analysis", exist_ok=True)
    os.makedirs("RFdynamic_C_analysis", exist_ok=True)
    os.makedirs("RFdynamic_NC_analysis", exist_ok=True)
    
    # Calculate total tasks
    total_tasks = len(parameter_map) * len(ARRIVAL_RATES)
    if TEST_RANDOM:
        total_tasks += 1
    if TEST_SOFTRANDOM:
        total_tasks += 1
    
    completed_tasks = 0
    
    logger.info(f"Starting dataset creation with {total_tasks} total tasks")
    
    # Process phase1 for each enabled avg_status
    for avg_status, bp_parameter in parameter_map.items():
        logger.info(f"Processing {avg_status} data with {len(bp_parameter)} parameter sets...")
        start_time_phase = time.time()
        
        successful_arrivals = 0
        failed_arrivals = 0
        
        # Use tqdm for the arrival rates to show progress
        for i in tqdm.tqdm(ARRIVAL_RATES, desc=f"Processing {avg_status} arrival rates", leave=True):
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
    
    # Process random frequency data if enabled
    if TEST_RANDOM:
        logger.info(f"Processing random frequency data for {len(FREQ_FOLDERS)} frequencies...")
        start_time_random = time.time()
        
        try:
            # Call execute_phase1_random with frequency folders
            execute_standard.execute_phase1_random(FREQ_FOLDERS)
            
            random_duration = time.time() - start_time_random
            completed_tasks += 1
            logger.info(f"Completed random frequency data processing in {random_duration:.2f}s "
                       f"({completed_tasks}/{total_tasks} total tasks)")
        except Exception as e:
            logger.error(f"Error processing random frequency data: {e}")
    
    # Process softrandom frequency data if enabled
    if TEST_SOFTRANDOM:
        logger.info(f"Processing softrandom frequency data for {len(FREQ_FOLDERS)} frequencies...")
        start_time_softrandom = time.time()
        
        try:
            # Call execute_phase1_softrandom with frequency folders
            execute_standard.execute_phase1_softrandom(FREQ_FOLDERS)
            
            softrandom_duration = time.time() - start_time_softrandom
            completed_tasks += 1
            logger.info(f"Completed softrandom frequency data processing in {softrandom_duration:.2f}s "
                       f"({completed_tasks}/{total_tasks} total tasks)")
        except Exception as e:
            logger.error(f"Error processing softrandom frequency data: {e}")

def validate_results():
    """Validate that results were generated correctly"""
    logger.info("Validating generated results...")
    
    # Check phase1 results if any avg tests were enabled
    if TEST_AVG_30 or TEST_AVG_60 or TEST_AVG_90:
        phase1_files = []
        if os.path.exists("phase1"):
            phase1_files = [f for f in os.listdir("phase1") if f.endswith('.csv')]
            logger.info(f"Generated {len(phase1_files)} phase1 result files")
            
            # Validate column structure for a sample file
            if phase1_files:
                sample_file = os.path.join("phase1", phase1_files[0])
                try:
                    df = pd.read_csv(sample_file)
                    
                    # Check for base algorithm columns
                    base_columns = ['arrival_rate', 'bp_parameter_L', 'bp_parameter_H', 
                                  'RR', 'Srpt', 'Setf', 'Fcfs', 'RMLF', 'RFdynamic', 'Bal', 'Sjf']
                    
                    # Check for Dynamic parameter columns (should have mode x njobs combinations)
                    dynamic_columns = []
                    for mode in [1, 2, 3]:
                        for njobs in [10, 100, 500, 1000, 5000, 10000]:
                            dynamic_columns.append(f"DYNAMIC_mode{mode}_njobs{njobs}")
                    
                    # Check for RFdynamic_C and RFdynamic_NC columns
                    rf_columns = []
                    for mode in [1, 2, 3]:
                        for checkpoint in [100, 500, 1000, 5000, 10000]:
                            rf_columns.append(f"RFdynamic_C_mode{mode}_cp{checkpoint}")
                            rf_columns.append(f"RFdynamic_NC_mode{mode}_cp{checkpoint}")
                    
                    missing_base = [col for col in base_columns if col not in df.columns]
                    if missing_base:
                        logger.warning(f"Missing base columns: {missing_base}")
                    
                    logger.info(f"Found {sum(1 for col in dynamic_columns if col in df.columns)}/18 Dynamic configurations")
                    logger.info(f"Found {sum(1 for col in rf_columns[:15] if col in df.columns)}/15 RFdynamic_C configurations")
                    logger.info(f"Found {sum(1 for col in rf_columns[15:] if col in df.columns)}/15 RFdynamic_NC configurations")
                    logger.info(f"Sample file has {len(df)} rows")
                    
                except Exception as e:
                    logger.error(f"Error validating sample file {sample_file}: {e}")
    
    # Check merged random results if enabled
    if TEST_RANDOM:
        random_result_file = "result/random_result.csv"
        if os.path.exists(random_result_file):
            try:
                df = pd.read_csv(random_result_file)
                logger.info(f"Random result file has {len(df)} frequency configurations")
                logger.info(f"Random result file has {len(df.columns)} columns")
            except Exception as e:
                logger.error(f"Error validating random result file: {e}")
        else:
            logger.warning("Random result file not found at result/random_result.csv")
    
    # Check merged softrandom results if enabled
    if TEST_SOFTRANDOM:
        softrandom_result_file = "result/softrandom_result.csv"
        if os.path.exists(softrandom_result_file):
            try:
                df = pd.read_csv(softrandom_result_file)
                logger.info(f"Softrandom result file has {len(df)} frequency configurations")
                logger.info(f"Softrandom result file has {len(df.columns)} columns")
            except Exception as e:
                logger.error(f"Error validating softrandom result file: {e}")
        else:
            logger.warning("Softrandom result file not found at result/softrandom_result.csv")
    
    # Check for algorithm-specific analysis directories
    analysis_dirs = ["Dynamic_analysis", "RFdynamic_C_analysis", "RFdynamic_NC_analysis"]
    for dir_name in analysis_dirs:
        if os.path.exists(dir_name):
            subdirs = [d for d in os.listdir(dir_name) if os.path.isdir(os.path.join(dir_name, d))]
            logger.info(f"{dir_name} contains {len(subdirs)} subdirectories")

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