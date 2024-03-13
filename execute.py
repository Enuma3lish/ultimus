import multiprocessing
import Read_csv
import RMLFQ,RR,SJF,SRPT,SETF,FCFS,MLFQ,PRMLFQ,algo_checker,Rmlfq_dy
#Arrival_rate=[0.05,0.04545,0.0416,0.0385,0.036,0.033,0.3123,0.029,0.028,0.026,0.025]
def process_scheduler(func, data):
    return func(data)
def execute(Arrival_rate,bp_parameter):
    results = []
    result =[]
    job_list =[]
    sjf_result = 0
    rr_result = 0
    mlfq_result = 0
    rmlfq_result =0
    rmlfq_dy_result =0
    prmlfq_result = 0
    setf_result = 0
    fcfs_result = 0
    sjf_l2n_result = 0
    rr_l2n_result = 0
    mlfq_l2n_result = 0
    rmlfq_l2n_result =0
    rmlfq_dy_l2n_result =0
    prmlfq_l2n_result =0
    setf_l2n_result = 0
    fcfs_l2n_result = 0
    rmlfq_l2n_rr_l2n_result = 0
    for i in bp_parameter:
        job_list = Read_csv.Read_csv('data/'+str((Arrival_rate,i["L"]))+".csv")
        rr_list = job_list.copy()
        sjf_list = job_list.copy()
        srpt_list = job_list.copy()
        setf_list = job_list.copy()
        fcfs_list = job_list.copy()
        rmlfq_list = job_list.copy()
        prmlfq_list = job_list.copy()
        prmlfq_avg=0
        prmlfq_l2n=0
        mlfq_avg = 0
        mlfq_l2n = 0
        rr_avg = 0
        rr_l2n = 0
        sjf_avg = 0
        sjf_l2n = 0
        srpt_avg = 0
        srpt_l2n = 0
        setf_avg = 0
        setf_l2n = 0
        fcfs_avg =0
        fcfs_l2n = 0
        rmlfq_avg = 0
        rmlfq_l2n = 0
        rmlfq_dy_avg = 0
        rmlfq_dy_l2n = 0
        num_processes = 9
        with multiprocessing.Pool(processes=num_processes) as pool:
        # Use starmap to run the functions in parallel
            results = pool.starmap(
                process_scheduler,
                    [(RMLFQ.Rmlfq, job_list),(Rmlfq_dy.Rmlfq, job_list),(MLFQ.Mlfq,rmlfq_list),(RR.Rr, rr_list), (SRPT.Srpt, srpt_list), (SJF.Sjf, sjf_list),(SETF.Setf,setf_list),(FCFS.Fcfs,fcfs_list),(PRMLFQ.Prmlfq,prmlfq_list)]
                )
            rmlfq,rmlfq_dy,mlfq,rr,srpt,sjf,setf,fcfs,prmlfq = results
            rmlfq_avg,rmlfq_l2n,rmlfq_log = rmlfq
            mlfq_avg,mlfq_l2n,mlfq_log = mlfq
            prmlfq_avg,prmlfq_l2n,prmlfq_log = prmlfq
            rmlfq_dy_avg,rmlfq_dy_l2n,rmlfq_dy_log=rmlfq_dy
            rr_avg,rr_l2n,rr_log = rr
            srpt_avg,srpt_l2n,srpt_log = srpt
            sjf_avg,sjf_l2n,sjf_log = sjf
            setf_avg,setf_l2n,setf_log = setf
            fcfs_avg,fcfs_l2n,fcfs_log = fcfs
            collect = {"rmlfq_dy":rmlfq_dy_log,"rmlfq":rmlfq_log,"mlfq":mlfq_log,"prmlfq":prmlfq_log,"rr":rr_log,"srpt":srpt_log,"sjf":sjf_log,"setf":setf_log,"fcfs":fcfs_log}
            for key,value in collect.items():
                r = algo_checker.check_logs(key,value)
                if r != True:
                    #print(str(r))
                    print(str(i)+" "+str(Arrival_rate)+" "+key+" "+str(r))
                    # print()
                    # print(value)
            sjf_result = sjf_avg/srpt_avg 
            rr_result = rr_avg/srpt_avg
            mlfq_result = mlfq_avg/srpt_avg
            rmlfq_result = rmlfq_avg/srpt_avg
            prmlfq_result = prmlfq_avg/srpt_avg
            setf_result = setf_avg/srpt_avg
            fcfs_result = fcfs_avg/srpt_avg
            rmlfq_dy_result = rmlfq_dy_avg/srpt_avg
            
            sjf_fcfs = sjf_avg/fcfs_avg 
            rr_fcfs = rr_avg/fcfs_avg
            mlfq_fcfs = mlfq_avg/fcfs_avg
            rmlfq_fcfs = rmlfq_avg/fcfs_avg
            prmlfq_fcfs = prmlfq_avg/fcfs_avg
            setf_fcfs = setf_avg/fcfs_avg
            srpt_fcfs = srpt_avg/fcfs_avg
            rmlfq_dy_fcfs = rmlfq_dy_avg/fcfs_avg
            
            
            sjf_l2n_result = sjf_l2n/srpt_l2n 
            rr_l2n_result = rr_l2n/srpt_l2n
            mlfq_l2n_result = mlfq_l2n/srpt_l2n
            rmlfq_l2n_result = rmlfq_l2n/srpt_l2n
            prmlfq_l2n_result = prmlfq_l2n/srpt_l2n
            setf_l2n_result = setf_l2n/srpt_l2n
            fcfs_l2n_result = fcfs_l2n/srpt_l2n
            rmlfq_dy_l2n_result = rmlfq_dy_l2n/srpt_l2n
            
            sjf_l2n_fcfs = sjf_l2n/fcfs_l2n 
            rr_l2n_fcfs = rr_l2n/fcfs_l2n
            mlfq_l2n_fcfs = mlfq_l2n/fcfs_l2n
            rmlfq_l2n_fcfs = rmlfq_l2n/fcfs_l2n
            prmlfq_l2n_fcfs = prmlfq_l2n/fcfs_l2n
            setf_l2n_fcfs = setf_l2n/fcfs_l2n
            srpt_l2n_fcfs = srpt_l2n/fcfs_l2n
            rmlfq_dy_l2n_fcfs = rmlfq_dy_l2n/fcfs_l2n
            
            rmlfq_l2n_rr_l2n_result = rmlfq_l2n/rr_l2n
            rmlfq_comp = rmlfq_l2n/rmlfq_dy_l2n
            result.append({
                "arrival_rate":Arrival_rate,
                "bp_parameter":i,
                "SJF/SRPT":sjf_result,
                "RR/SRPT":rr_result,
                "MLFQ/SRPT":mlfq_result,
                "RMLFQ/SRPT":rmlfq_result,
                "RMLFQ_Dy/SRPT":rmlfq_dy_result,
                "PRMLFQ/SRPT":prmlfq_result,
                "SETF/SRPT":setf_result,
                "FCFS/SRPT":fcfs_result,
                "SJF/FCFS":sjf_fcfs,
                "RR/FCFS":rr_fcfs,
                "MLFQ/FCFS":mlfq_fcfs,
                "RMLFQ/FCFS":rmlfq_fcfs,
                "RMLFQ_Dy/FCFS":rmlfq_dy_fcfs,
                "PRMLFQ/FCFS":prmlfq_fcfs,
                "SETF/FCFS":setf_fcfs,
                "SPRT/FCFS":srpt_fcfs,
                "SJF_L2_Norm/SRPT_L2_Norm":sjf_l2n_result,
                "RR_L2_Norm/SRPT_L2_Norm":rr_l2n_result,
                "MLFQ_L2_Norm/SRPT_L2_Norm":mlfq_l2n_result,
                "RMLFQ_L2_Norm/SRPT_L2_Norm":rmlfq_l2n_result,
                "RMLFQ_Dy_L2_Norm/SRPT_L2_Norm":rmlfq_dy_l2n_result,
                "PRMLFQ_L2_Norm/SRPT_L2_Norm":prmlfq_l2n_result,
                "SETF_L2_Norm/SRPT_L2_Norm":setf_l2n_result,
                "FCFS_L2_Norm/SRPT_L2_Norm":fcfs_l2n_result,
                "SJF_L2_Norm/FCFS_L2_Norm":sjf_l2n_fcfs,
                "RR_L2_Norm/FCFS_L2_Norm":rr_l2n_fcfs,
                "MLFQ_L2_Norm/FCFS_L2_Norm":mlfq_l2n_fcfs,
                "RMLFQ_L2_Norm/FCFS_L2_Norm":rmlfq_l2n_fcfs,
                "RMLFQ_Dy_L2_Norm/FCFS_L2_Norm":rmlfq_dy_l2n_fcfs,
                "PRMLFQ_L2_Norm/FCFS_L2_Norm":prmlfq_l2n_fcfs,
                "SETF_L2_Norm/FCFS_L2_Norm":setf_l2n_fcfs,
                "SRPT_L2_Norm/FCFS_L2_Norm":srpt_l2n_fcfs,
                "Rmlfq_L2_Norm/RR_L2_Norm":rmlfq_l2n_rr_l2n_result,
                "Rmlfq_L2_Norm/Rmlfq_Dy_L2_norm":rmlfq_comp,
                "FCFS_average_flow_time":fcfs_avg,
                "SJF_average_flow_time":sjf_avg,
                "SRPT_average_flow_time":srpt_avg,
                "RMLFQ_average_flow_time":rmlfq_avg,
                "RMLFQ_Dy_average_flow_time":rmlfq_dy_avg,
                "PRMLFQ_average_flow_time":prmlfq_avg,
                "MLFQ_average_flow_time":mlfq_avg,
                "SETF_average_flow_time":setf_avg,
                "FCFS_L2N":fcfs_l2n,
                "SJF_L2N":sjf_l2n,
                "SRPT_L2N":srpt_l2n,
                "RMLFQ_L2N":rmlfq_l2n,
                "RMLFQ_Dy_L2N":rmlfq_dy_l2n,
                "PRMLFQ_L2N":prmlfq_l2n,
                "MLFQ_L2N":mlfq_l2n,
                "SETF_L2N":setf_l2n         
            })
        pool.close()
        pool.join()
    return result
        
    