#create dataset 
import Write_csv
import execute
num_jobs = 10000
results =[]
result = []
def main():
    #Job_init.Save_file(num_jobs)
    Arrival_rate = [i for i in range(20, 41, 2)]
    base_quantum = [i for i in range(15, 30, 2)]
    quantum_multiplier = [1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.0]
    bp_parameter=[{"L":16.772,"H":pow(2,6)},{"L":7.918,"H":pow(2,9)},{"L":5.649,"H":pow(2,12)},{"L":4.639,"H":pow(2,15)},{"L":4.073,"H":pow(2,18)}]
    for i in Arrival_rate:
        for j in base_quantum:
            for k in quantum_multiplier:
                results = execute.execute(i,bp_parameter,j,k) 
                result.extend(results)
                Write_csv.Write("/home/melowu/Work/expri/DataSet/result"+j+"-"+k+".csv",result)
if __name__ == "__main__":
    main()


    