#create dataset 
import Write_csv
import execute
num_jobs = 10000
results =[]
result = []
def main():
    #Job_init.Save_file(num_jobs)
    Arrival_rate = [i for i in range(20, 41, 2)]
    bp_parameter=[{"L":16.772,"H":pow(2,6)},{"L":7.918,"H":pow(2,9)},{"L":5.649,"H":pow(2,12)},{"L":4.639,"H":pow(2,15)},{"L":4.073,"H":pow(2,18)}]
    for i in Arrival_rate:
        results = execute.execute(i,bp_parameter) 
        result.extend(results)
    Write_csv.Write("/home/melowu/Work/expri/100000_data_pow_2.csv",result)
if __name__ == "__main__":
    main()


    