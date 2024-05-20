#create dataset 
# import Write_csv
import execute
import tqdm

import pandas as pd
 
num_jobs = 10000
def main():
    #Job_init.Save_file(num_jobs)
    Arrival_rate = [i for i in range(20, 42, 2)]
    # quantum_decrease = [0,1,2,4,8,16,32,64,128,256,512,1024]
    # quantum_multiplier = [1,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.0]
    possibility = [0.5,0.25,0.125,0.00625]
    bp_parameter=[{"L":16.772,"H":pow(2,6)},{"L":7.918,"H":pow(2,9)},{"L":5.649,"H":pow(2,12)},{"L":4.639,"H":pow(2,15)},{"L":4.073,"H":pow(2,18)}]
    #for i in Arrival_rate:
    results = []
    progress = tqdm.tqdm(total=len(Arrival_rate)*len(possibility))

    for i in Arrival_rate:
        for j in possibility:
            # print(i,j,k)
            result = execute.execute(i,bp_parameter,j)
            results.extend(result)
            progress.update(1)
    results = pd.DataFrame(results)
    results.to_csv(f"/home/melowu/Work/expri/DataSet/result3.csv", index=False)

    # Write_csv.Write("/home/melowu/Work/expri/DataSet/result"+str(i)+".csv",results)
if __name__ == "__main__":
    main()


    