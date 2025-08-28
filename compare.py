import pandas as pd

def compare_csv_files(file1, file2):
    try:
        # Load both CSV files into dataframes
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)

        # Check if both files have the same columns
        if list(df1.columns) != list(df2.columns):
            print("The CSV files have different columns.")
            return False

        # Check if the data is identical
        if df1.equals(df2):
            print("The CSV files are identical.")
            return True
        else:
            print("The CSV files have different content.")
            return False

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

# Example usage
file1 = 'srpt_time_slot_log.csv'
file2 = 'dy_srpt_time_slot_log.csv'
compare_csv_files(file1, file2)