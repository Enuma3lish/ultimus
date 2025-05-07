import sys
import multiprocessing as mp

# For macOS, force the 'fork' start method to avoid issues with standard streams.
if sys.platform == 'darwin':
    try:
        mp.set_start_method('fork', force=True)
    except RuntimeError:
        # If the start method is already set, we can ignore the error.
        pass

# Before importing any modules that use multiprocessing, reassign sys streams.
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
sys.stdin = sys.__stdin__

# Now import modules that create multiprocessing Pools (like execute_compare)
import execute_compare
import tqdm
import pandas as pd
import os
import logging

# Set up logging for main_compare.py
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='execution_log.log',
                    filemode='a')
logger = logging.getLogger(__name__)

# Fixed checkpoint values for Rdynamic algorithms
checkpoints = {
    "RDYNAMIC_SQRT_2": 100,
    "RDYNAMIC_SQRT_6": 100,
    "RDYNAMIC_SQRT_8": 100,
    "RDYNAMIC_SQRT_10": 100,
    "Dynamic": 100
}

def create_dataset():
    # Arrival rates to process
    arrival_rates = list(range(20, 42, 2))
    
    # BP parameters for different settings
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
    
    # Random job settings
    jsettings = [1, 10, 100, 500, 1000, 10000]
    
    # Create log directory
    os.makedirs("log", exist_ok=True)
    
    # Create result directories (including one for softrandom)
    result_dirs = ["result", "compare_avg_30", "compare_avg_60", "compare_avg_90", 
                   "freq_comp_result", "softrandom_comp_result"]
    for directory in result_dirs:
        os.makedirs(directory, exist_ok=True)
    
    # Update the CHECKPOINTS dictionary in execute_compare module
    execute_compare.CHECKPOINTS = checkpoints.copy()
    
    logger.info(f"Using checkpoints: {checkpoints}")
    
    # Process each arrival rate
    for i in tqdm.tqdm(arrival_rates, desc="Processing arrival rates"):
        try:
            # Process regular data with all three BP parameter sets
            logger.info(f"Processing regular data with bp_parameter_30 for arrival rate {i}")
            execute_compare.execute(i, bp_parameter_30)
            
            logger.info(f"Processing regular data with bp_parameter_60 for arrival rate {i}")
            execute_compare.execute(i, bp_parameter_60)
            
            logger.info(f"Processing regular data with bp_parameter_90 for arrival rate {i}")
            execute_compare.execute(i, bp_parameter_90)
            
            # Process random settings
            if jsettings:
                logger.info(f"Processing random data for arrival rate {i}")
                execute_compare.execute_random(i, jsettings)
            
            # Process comparison data (avg_30, avg_60, avg_90, freq)
            logger.info(f"Processing comparison data for arrival rate {i}")
            execute_compare.execute_compare(i, ["avg_30", "avg_60", "avg_90", "freq"])
            
            # Process softrandom data
            if jsettings:
                logger.info(f"Processing softrandom data for arrival rate {i}")
                execute_compare.execute_softrandom(i, jsettings)
            
        except Exception as e:
            logger.error(f"Error processing arrival rate {i}: {e}")
            continue

if __name__ == "__main__":
    mp.freeze_support()
    create_dataset()