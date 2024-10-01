import csv

def read_csv_file(filepath):
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        # Read all rows into a list
        data = list(reader)
    return data

def sort_csv_data(data):
    # Sort data based on rows
    return sorted(data)

def csv_files_are_equal(file1, file2):
    data1 = read_csv_file(file1)
    data2 = read_csv_file(file2)

    return data1 == data2

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python compare_csv.py file1.csv file2.csv")
        sys.exit(1)

    file1 = sys.argv[1]
    file2 = sys.argv[2]

    if csv_files_are_equal(file1, file2):
        print("The CSV files have the same content.")
    else:
        print("The CSV files do not have the same content.")
