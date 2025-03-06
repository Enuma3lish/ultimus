import execute_compare
import tqdm
import pandas as pd
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='execution_log.log', filemode='a')
logger = logging.getLogger(__name__)

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
    jsettings = [2**i for i in range(11)]
    
    # Create log directory
    os.makedirs("log", exist_ok=True)
    
    # Create result directories
    result_dirs = ["result", "compare_avg_30", "compare_avg_60", "compare_avg_90", "freq_comp_result"]
    for directory in result_dirs:
        os.makedirs(directory, exist_ok=True)
    
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
            
        except Exception as e:
            logger.error(f"Error processing arrival rate {i}: {e}")
            continue

if __name__ == "__main__":
    create_dataset()