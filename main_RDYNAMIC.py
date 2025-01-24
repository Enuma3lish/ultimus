import execute_comp_RDYNAMIC
import tqdm
import pandas as pd
import os

def create_dataset():
    Arrival_rate = [i for i in range(20, 42, 2)]
    check = [1, 2, 4, 8, 16, 30, 32, 64]
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

    os.makedirs("log", exist_ok=True)

    for c in tqdm.tqdm(check, desc="Processing checkpoints"):
        results = []
        for i in tqdm.tqdm(Arrival_rate, desc=f"Processing arrival rates for checkpoint {c}", leave=False):
            try:
                result = execute_comp_RDYNAMIC.execute(i, bp_parameter, c)
                results.extend(result)
            except Exception:
                continue

        if results:
            try:
                mresults = pd.DataFrame(results)
                output_file = f"log/result{c}.csv"
                mresults.to_csv(output_file, index=False)
            except Exception:
                print(f"Error saving results for checkpoint {c}")

if __name__ == "__main__":
    create_dataset()