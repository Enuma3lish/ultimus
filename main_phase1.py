import execute_phase1
import tqdm
import pandas as pd
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_dataset():
    Arrival_rate = [i for i in range(20, 42, 2)]
    check = [32,64] 
    #[32,64,128,256,512,1024,2048,4096,8192,16384]
    bp_parameter = [
        {"L": 16.772, "H": pow(2, 6)},
        {"L": 7.918, "H": pow(2, 9)},
        {"L": 5.649, "H": pow(2, 12)},
        {"L": 4.639, "H": pow(2, 15)},
        {"L": 4.073, "H": pow(2, 18)}
    ]

    # Create the log directory if it doesn't exist
    log_dir = "/Users/melowu/Desktop/ultimus/log/"
    os.makedirs(log_dir, exist_ok=True)
    # Use tqdm for the outer loop to show overall progress
    for c in tqdm.tqdm(check, desc="Processing checkpoints"):
        results = []
        for i in tqdm.tqdm(Arrival_rate, desc=f"Processing arrival rates for checkpoint {c}", leave=False):
            try:
                execute_phase1.execute_phase1(i, bp_parameter)
            except Exception as e:
                    logger.error(f"Error processing arrival rate {i} for checkpoint {c}: {e}")
                    continue

if __name__ == "__main__":
    create_dataset()