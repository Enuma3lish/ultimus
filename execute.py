import multiprocessing
import Read_csv
import SMLFQ,RR,SJF,SRPT,SETF,FCFS,MLFQ,RMLFQ,Mlfq_dy,RMLFQ_SM,algo_checker

def process_scheduler(func, *args):
    if len(args) == 1 and isinstance(args[0], list):
        return func(args[0])
    return func(*args)
def execute(Arrival_rate,bp_parameter,possibility):
    results = []
    result =[]
    job_list =[]
    sjf_result = 0
    rr_result = 0
    mlfq_result = 0
    mmlfq_result = 0
    rmlfq_result =0
    setf_result = 0
    fcfs_result = 0
    #bal_result = 0
    srpt_result = 0
    sjf_l2n_result = 0
    bal_l2n_result = 0
    srpt_l2n_result = 0 
    rr_l2n_result = 0
    mlfq_l2n_result = 0
    rmlfq_l2n_result =0
    setf_l2n_result = 0
    fcfs_l2n_result = 0
    for i in bp_parameter:
        job_list = Read_csv.Read_csv('data/'+str((Arrival_rate,i["L"]))+".csv")
        rr_list = job_list.copy()
        sjf_list = job_list.copy()
        #bal_list = job_list.copy()
        srpt_list = job_list.copy()
        setf_list = job_list.copy()
        fcfs_list = job_list.copy()
        mlfq_list = job_list.copy()
        rmlfq_sm_list = job_list.copy()
        rmlfq_list = job_list.copy()
        mlfq_dy_list = job_list.copy()
        rmlfq_avg=0
        rmlfq_l2n=0
        mlfq_avg = 0
        mlfq_l2n = 0
        rmlfq_sm_avg = 0
        rmlfq_sm_l2n = 0
        rr_avg = 0
        rr_l2n = 0
        # bal_avg = 0
        # bal_l2n = 0
        sjf_avg = 0
        sjf_l2n = 0
        srpt_avg = 0
        srpt_l2n = 0
        setf_avg = 0
        setf_l2n = 0
        fcfs_avg =0
        fcfs_l2n = 0
        num_processes = 8
        with multiprocessing.Pool(processes=num_processes) as pool:
        # Use starmap to run the functions in parallel
            results = pool.starmap(
                process_scheduler,
                    [(RMLFQ.Rmlfq, rmlfq_list),(MLFQ.Mlfq,mlfq_list),(RR.Rr, rr_list), (SRPT.Srpt, srpt_list),
                     (RMLFQ_SM.Rmlfq_sm,rmlfq_sm_list,possibility),
                     (SJF.Sjf, sjf_list),(SETF.Setf,setf_list),(FCFS.Fcfs,fcfs_list)])
            rmlfq,mlfq,rr,srpt,rmlfq_sm,sjf,setf,fcfs= results
            mlfq_avg,mlfq_l2n = mlfq
            rmlfq_sm_avg,rmlfq_sm_l2n = rmlfq_sm
            rmlfq_avg,rmlfq_l2n = rmlfq
            rr_avg,rr_l2n= rr
            srpt_avg,srpt_l2n= srpt
            sjf_avg,sjf_l2n,= sjf
            setf_avg,setf_l2n= setf
            fcfs_avg,fcfs_l2n= fcfs
            #bal_avg,bal_l2n,bal_log=bal
            # collect = {"mlfq_dy":mlfq_dy_log,"rmlfq":rmlfq_log,"mlfq":mlfq_log,"rr":rr_log,"srpt":srpt_log,"sjf":sjf_log,"setf":setf_log,"fcfs":fcfs_log,"mmlfq":mmlfq_log}
            # for key,value in collect.items():
            #     r = algo_checker.check_logs(key,value)
            #     if r != True:
            #         #print(str(r))
            #         print(str(i)+" "+str(Arrival_rate)+" "+key+" "+str(r))
            #         # print()
            #         # print(value)
            sjf_result = sjf_avg/srpt_avg 
            rr_result = rr_avg/srpt_avg
            mlfq_result = mlfq_avg/srpt_avg
            rmlfq_sm_result = rmlfq_sm_avg/srpt_avg
            rmlfq_result = rmlfq_avg/srpt_avg
            setf_result = setf_avg/srpt_avg
            fcfs_result = fcfs_avg/srpt_avg
            #bal_result = bal_avg/srpt_avg
            
            sjf_fcfs = sjf_avg/fcfs_avg 
            rr_fcfs = rr_avg/fcfs_avg
            mlfq_fcfs = mlfq_avg/fcfs_avg
            rmlfq_fcfs = rmlfq_avg/fcfs_avg
            rmlfq_sm_fcfs = rmlfq_sm_avg/fcfs_avg
            setf_fcfs = setf_avg/fcfs_avg
            srpt_fcfs = srpt_avg/fcfs_avg
            #bal_fcfs = bal_avg/fcfs_avg
            
            
            sjf_l2n_result = sjf_l2n/srpt_l2n 
            rr_l2n_result = rr_l2n/srpt_l2n
            mlfq_l2n_result = mlfq_l2n/srpt_l2n
            rmlfq_sm_l2n_result = rmlfq_sm_l2n/srpt_l2n
            #smlfq_l2n_result = smlfq_l2n/srpt_l2n
            rmlfq_l2n_result = rmlfq_l2n/srpt_l2n
            setf_l2n_result = setf_l2n/srpt_l2n
            fcfs_l2n_result = fcfs_l2n/srpt_l2n
            #bal_l2n_result = bal_l2n/srpt_l2n
            
            sjf_l2n_fcfs = sjf_l2n/fcfs_l2n 
            rr_l2n_fcfs = rr_l2n/fcfs_l2n
            mlfq_l2n_fcfs = mlfq_l2n/fcfs_l2n
            rmlfq_l2n_fcfs = rmlfq_l2n/fcfs_l2n
            rmlfq_sm_comp_fcfs = rmlfq_sm_l2n/fcfs_l2n
            rmlfq_sm_comp_rr = rmlfq_sm_l2n/rr_l2n
            rmlfq_sm_comp_setf = rmlfq_sm_l2n/setf_l2n
            result.append({
                "arrival_rate":Arrival_rate,
                "possibility":possibility,
                "bp_parameter":i,
                "SJF/SRPT":sjf_result,
                "RR/SRPT":rr_result,
                "MLFQ/SRPT":mlfq_result,
                "RMLFQ_SM/SRPT":rmlfq_sm_result,
                "RMLFQ/SRPT":rmlfq_result,
                "SETF/SRPT":setf_result,
                "FCFS/SRPT":fcfs_result,
                #"BAL/SRPT":bal_result,
                "SJF/FCFS":sjf_fcfs,
                "RR/FCFS":rr_fcfs,
                "MLFQ/FCFS":mlfq_fcfs,
                "RMLFQ_sm/FCFS":rmlfq_sm_fcfs,
                "RMLFQ/FCFS":rmlfq_fcfs,
                "SETF/FCFS":setf_fcfs,
                "SPRT/FCFS":srpt_fcfs,
                "SJF_L2_Norm/SRPT_L2_Norm":sjf_l2n_result,
                "RR_L2_Norm/SRPT_L2_Norm":rr_l2n_result,
                "MLFQ_L2_Norm/SRPT_L2_Norm":mlfq_l2n_result,
                "RMLFQ_SM_L2_Norm/SRPT_L2_Norm":rmlfq_sm_l2n_result,
                "RMLFQ_L2_Norm/SRPT_L2_Norm":rmlfq_l2n_result,
                "SETF_L2_Norm/SRPT_L2_Norm":setf_l2n_result,
                "FCFS_L2_Norm/SRPT_L2_Norm":fcfs_l2n_result,
                "SJF_L2_Norm/FCFS_L2_Norm":sjf_l2n_fcfs,
                "RR_L2_Norm/FCFS_L2_Norm":rr_l2n_fcfs,
                "MLFQ_L2_Norm/FCFS_L2_Norm":mlfq_l2n_fcfs,
                "RMLFQ_L2_Norm/FCFS_L2_Norm":rmlfq_l2n_fcfs,
                "RMLFQ_SM_L2_Norm/FCFS_L2_Norm":rmlfq_sm_comp_fcfs,
                "RMLFQ_SM_L2_Norm/RR_L2_Norm":rmlfq_sm_comp_rr,
                "RMLFQ_SM_L2_Norm/SETF_L2_Norm":rmlfq_sm_comp_setf
            })
        pool.close()
        pool.join()
    return result
        
    