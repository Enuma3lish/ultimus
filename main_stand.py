import execute_standard
import tqdm
import pandas as pd
import logging
import os
import time

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

    # Create the log directory if it doesn't exist
    log_dir = "log"
    os.makedirs(log_dir, exist_ok=True)
    
    # Create output directories
    os.makedirs("phase1", exist_ok=True)
    os.makedirs("freq", exist_ok=True)
    
    # Process phase1 for each avg_status
    for avg_status, bp_parameter in parameter_map.items():
        logger.info(f"Processing {avg_status} data...")
        
        # Use tqdm for the arrival rates to show progress
        for i in tqdm.tqdm(Arrival_rate, desc=f"Processing {avg_status} arrival rates", leave=True):
            try:
                # Call execute_phase1 with the correct parameter set
                execute_standard.execute_phase1(i, bp_parameter)
                logger.info(f"Completed processing arrival rate {i} for {avg_status}")
                
                # Small delay to prevent system overload
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error processing arrival rate {i} for {avg_status}: {e}")
                continue
    
    # Process phase1_random for all arrival rates at once
    logger.info("Processing frequency-based random data...")
    
    try:
        # Call execute_phase1_random with all arrival rates
        execute_standard.execute_phase1_random(Arrival_rate)
        logger.info(f"Completed processing random data for all arrival rates")
    except Exception as e:
        logger.error(f"Error processing random frequency data: {e}")

if __name__ == "__main__":
    # Set start time
    start_time = time.time()
    
    # Create dataset
    create_dataset()
    
    # Calculate and log execution time
    execution_time = time.time() - start_time
    logger.info(f"Total execution time: {execution_time:.2f} seconds ({execution_time/60:.2f} minutes)")