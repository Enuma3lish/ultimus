import execute_standard
import tqdm
import pandas as pd
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_dataset():
    Arrival_rate = [i for i in range(20, 42, 2)]
    #[32,64,128,256,512,1024,2048,4096,8192,16384]
    bp_parameter = [
        {"L": 16.772, "H": pow(2, 6)},
        {"L": 7.918, "H": pow(2, 9)},
        {"L": 5.649, "H": pow(2, 12)},
        {"L": 4.639, "H": pow(2, 15)},
        {"L": 4.073, "H": pow(2, 18)},
        {"L": 56.300, "H": pow(2, 6)},
        {"L": 18.900, "H": pow(2, 9)},
        {"L": 12.400, "H": pow(2, 12)},
        {"L": 9.800, "H": pow(2, 15)},
        {"L": 8.500, "H": pow(2, 18)},
        {"L": 32.300, "H": pow(2, 9)},
        {"L": 19.700, "H": pow(2, 12)},
        {"L": 15.300, "H": pow(2, 15)},
        {"L": 13.000, "H": pow(2, 18)}
    ]

    # Create the log directory if it doesn't exist
    log_dir = "log"
    os.makedirs(log_dir, exist_ok=True)
    jsettings = [1,25,50,100,200,300,400,500,1000,2000,3000,4000,5000,10000]
    # Use tqdm for the outer loop to show overall progress
    for i in tqdm.tqdm(Arrival_rate, desc=f"Processing arrival rates", leave=False):
        try:
            execute_standard.execute_phase1(i, bp_parameter)
        except Exception as e:
                logger.error(f"Error processing arrival rate {i} : {e}")
                continue
    for i in tqdm.tqdm(Arrival_rate, desc=f"Processing arrival rates", leave=False):
        try:
            execute_standard.execute_phase1_random(i,jsettings)
        except Exception as e:
            logger.error(f"Error processing arrival rate {i} : {e}")
            continue

if __name__ == "__main__":
    create_dataset()