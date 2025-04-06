import execute_compare
import tqdm
import pandas as pd
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='execution_log.log', filemode='a')
logger = logging.getLogger(__name__)

# Checkpoint values for Rdynamic algorithms to test
checkpoints = {
    "RDYNAMIC_SQRT_2": [80],  # Add checkpoint for Rdynamic_sqrt_2
    "RDYNAMIC_SQRT_6": [30],
    "RDYNAMIC_SQRT_8": [60],  # default value
    "RDYNAMIC_SQRT_10": [100],  # default value
    "Dynamic": [100]  # default value
}

def create_dataset():
    # Arrival rates to process
    arrival_rates = [i for i in range(20, 42, 2)]
    
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
    
    # Create result directories (including new one for softrandom)
    result_dirs = ["result", "compare_avg_30", "compare_avg_60", "compare_avg_90", 
                   "freq_comp_result", "softrandom_comp_result"]
    for directory in result_dirs:
        os.makedirs(directory, exist_ok=True)
    
    # Update the CHECKPOINTS dictionary in execute_compare module
    execute_compare.CHECKPOINTS = {
        "RDYNAMIC_SQRT_2": checkpoints["RDYNAMIC_SQRT_2"][0],  # Add Rdynamic_sqrt_2 checkpoint
        "RDYNAMIC_SQRT_6": checkpoints["RDYNAMIC_SQRT_6"][0],  # Start with first checkpoint
        "RDYNAMIC_SQRT_8": checkpoints["RDYNAMIC_SQRT_8"][0],
        "RDYNAMIC_SQRT_10": checkpoints["RDYNAMIC_SQRT_10"][0],
        "Dynamic": checkpoints["Dynamic"][0]
    }
    
    logger.info(f"Testing checkpoints: {checkpoints}")
    
    # Process each arrival rate
    for i in tqdm.tqdm(arrival_rates, desc="Processing arrival rates"):
        try:
            # Process with different RDYNAMIC_SQRT_6 checkpoint values
            for checkpoint_6 in checkpoints["RDYNAMIC_SQRT_6"]:
                # Update the checkpoint value
                execute_compare.CHECKPOINTS["RDYNAMIC_SQRT_6"] = checkpoint_6
                logger.info(f"Using RDYNAMIC_SQRT_6 checkpoint: {checkpoint_6}")
                
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
                
                # Process softrandom data (new addition)
                if jsettings:
                    logger.info(f"Processing softrandom data for arrival rate {i}")
                    execute_compare.execute_softrandom(i, jsettings)
            
        except Exception as e:
            logger.error(f"Error processing arrival rate {i}: {e}")
            continue

if __name__ == "__main__":
    create_dataset()