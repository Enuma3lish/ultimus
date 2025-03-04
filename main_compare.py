import execute_compare
import tqdm
import pandas as pd
import os

def create_dataset():
    Arrival_rate = [i for i in range(20, 42, 2)]
    check = [1, 4, 16,32, 64,128,256,1024,4096,10000]
    jsettings = [1,25,50,100,200,400,1000,2000,4000,10000]
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
    bp_parameter_30 = [
        {"L": 16.772, "H": pow(2, 6)},
        {"L": 7.918, "H": pow(2, 9)},
        {"L": 5.649, "H": pow(2, 12)},
        {"L": 4.639, "H": pow(2, 15)},
        {"L": 4.073, "H": pow(2, 18)}
    ]

    os.makedirs("log", exist_ok=True)

    for c in tqdm.tqdm(check, desc="Processing checkpoints"):
        for i in tqdm.tqdm(Arrival_rate, desc=f"Processing arrival rates for checkpoint {c}", leave=False):
            try:
                execute_compare.execute(i, bp_parameter, c)
                execute_compare.execute_random(i,c,jsettings)
            except Exception:
                continue

if __name__ == "__main__":
    create_dataset()