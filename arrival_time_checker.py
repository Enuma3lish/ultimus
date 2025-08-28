import csv
import numpy as np

def read_arrival_times_from_file(filename):
    """
    Reads arrival times from a CSV file.
    The file is expected to have two columns: 'arrival_time' and 'job_size'.
    """
    arrival_times = []
    
    # Read the CSV file
    with open(filename, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            # Extract arrival_time from each row
            arrival_times.append(float(row['arrival_time']))
    
    return arrival_times

def sum_and_average_arrival_times(arrival_times):
    """
    Sums the arrival times and calculates their average.
    """
    total_sum = np.sum(arrival_times)
    average_time = np.mean(arrival_times)
    return total_sum, average_time

def main():
    filename = 'data/(40, 4.073).csv'  # Specify the path to your file
    
    # Read arrival times from the file
    arrival_times = read_arrival_times_from_file(filename)
    
    if len(arrival_times) == 0:
        print("No arrival times found in the file.")
        return
    
    # Calculate the sum and average of the arrival times
    total_sum, average_time = sum_and_average_arrival_times(arrival_times)
    
    # Output the results
    print(f"Sum of arrival times: {total_sum}")
    print(f"Average arrival time: {average_time}")

if __name__ == "__main__":
    main()