import pandas as pd
import numpy as np

def calculate_averages(file_pattern, num_files, output_file):
    # List to store DataFrames
    dfs = []
    
    # Read all CSV files matching the pattern
    for i in range(num_files):
        filename = f"log/{i}result{file_pattern}.csv"
        df = pd.read_csv(filename)
        dfs.append(df)
    
    # Create a new DataFrame with the same structure as input
    # Use the first DataFrame as template for non-numeric columns
    result_df = dfs[0].copy()
    
    # Get numeric columns (excluding 'arrival_rate', 'bp_parameter', and 'c')
    numeric_cols = [col for col in result_df.columns 
                   if col not in ['arrival_rate', 'bp_parameter', 'c']]
    
    # Calculate averages only for numeric columns
    for col in numeric_cols:
        values = np.array([df[col].values for df in dfs])
        result_df[col] = np.mean(values, axis=0)
    
    # Save to CSV
    result_df.to_csv(output_file, index=False)
    print(f"Saved averages to {output_file}")

def main():
    # Process files for both patterns
    calculate_averages("64", 5, "result64.csv")
    calculate_averages("128", 5, "result128.csv")
    calculate_averages("256", 5, "result256.csv")
    calculate_averages("512", 5, "result512.csv")
    calculate_averages("1024", 5, "result1024.csv")
    calculate_averages("2048", 5, "result2048.csv")
    calculate_averages("4096", 5, "result4096.csv")
    calculate_averages("8192", 5, "result8192.csv")
    calculate_averages("16384", 5, "result16384.csv")

if __name__ == "__main__":
    main()