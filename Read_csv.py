import pandas as pd
def Read_csv(filename):
# Read the CSV file into a DataFrame 
    data_frame = pd.read_csv(filename)
# Convert the DataFrame into a list of lists
    data_list = data_frame.values.tolist()
    return data_list

