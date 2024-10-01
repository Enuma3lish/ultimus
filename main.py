#create dataset 
# import Write_csv
import execute
import tqdm
import pandas as pd
import executer_log2
 
def main():
    #Job_init.Save_file(num_jobs)
    Arrival_rate = [i for i in range(20, 42, 2)]
    # quantum_decrease = [0,1,2,4,8,16,32,64,128,256,512,1024]
    # quantum_multiplier = [1,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.0]
    possibility = [0.8,0.7,0.5,0.3,0.25,0.125]
    bp_parameter=[{"L":16.772,"H":pow(2,6)},{"L":7.918,"H":pow(2,9)},{"L":5.649,"H":pow(2,12)},{"L":4.639,"H":pow(2,15)},{"L":4.073,"H":pow(2,18)}]
    #for i in Arrival_rate:
    # progress = tqdm.tqdm(total=len(possibility))

    # for i in possibility:
    # for p in possibility:
    #     results = []
    #     for j in Arrival_rate:
    #         result = execute.execute(j,bp_parameter,p)
    #         results.extend(result)
    #         mresults = pd.DataFrame(results)
    #     mresults.to_csv(f"/home/melowu/Work/expri/DataSet/result{p}.csv", index=False
    results = []
    logs = []
    for j in Arrival_rate:
          executer_log2.scheduler(j,bp_parameter)
    #     log = executer_log2.scheduler(j,bp_parameter)
    #     #result = execute.execute(j,bp_parameter)
    #     logs.extend(log)
    #     #results.extend(result)
    #     mlogs = pd.DataFrame(logs)
    #     mresults = pd.DataFrame(results)
    # mresults.to_csv(f"/home/melowu/Work/ultimus/DataSet/result_new.csv", index=False)
    # mlogs.to_csv(f"/home/melowu/Work/ultimus/DataSet/result_logs.csv", index=False)
        # progress.update(1)
    # Write_csv.Write("/home/melowu/Work/expri/DataSet/result"+str(i)+".csv",results)
if __name__ == "__main__":
    main()


    