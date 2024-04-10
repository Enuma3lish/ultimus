import multiprocessing
import Read_csv
import SMLFQ,RR,SJF,SRPT,SETF,FCFS,MLFQ,RMLFQ,Mlfq_dy,Mmlfq,algo_checker

def process_scheduler(func, *args):
    if len(args) == 1 and isinstance(args[0], list):
        return func(args[0])
    return func(*args)
def execute(Arrival_rate,bp_parameter,quantum_multiplier,quantum_decrease):
    results = []
    result =[]
    job_list =[]
    sjf_result = 0
    rr_result = 0
    mlfq_result = 0
    mmlfq_result = 0
    rmlfq_result =0
    smlfq_result =0
    prmlfq_result = 0
    setf_result = 0
    fcfs_result = 0
    #bal_result = 0
    srpt_result = 0
    sjf_l2n_result = 0
    bal_l2n_result = 0
    srpt_l2n_result = 0 
    rr_l2n_result = 0
    mlfq_l2n_result = 0
    mmlfq_l2n_result = 0
    smlfq_l2n_result =0
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
        mmlfq_list = job_list.copy()
        rmlfq_list = job_list.copy()
        mlfq_dy_list = job_list.copy()
        rmlfq_avg=0
        rmlfq_l2n=0
        mlfq_avg = 0
        mlfq_l2n = 0
        mmlfq_avg = 0
        mmlfq_l2n = 0
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
        smlfq_avg = 0
        smlfq_l2n = 0
        mlfq_dy_avg = 0
        mlfq_dy_l2n = 0
        num_processes = 9
        with multiprocessing.Pool(processes=num_processes) as pool:
        # Use starmap to run the functions in parallel
            results = pool.starmap(
                process_scheduler,
                    [(SMLFQ.Smlfq,job_list),(RMLFQ.Rmlfq, rmlfq_list),(MLFQ.Mlfq,mlfq_list),(RR.Rr, rr_list), (SRPT.Srpt, srpt_list),
                     (Mlfq_dy.Mlfq_dy,mlfq_dy_list),(Mmlfq.Mmlfq,mmlfq_list,quantum_multiplier,quantum_decrease),
                     (SJF.Sjf, sjf_list),(SETF.Setf,setf_list),(FCFS.Fcfs,fcfs_list)])
            smlfq,rmlfq,mlfq,rr,srpt,mlfq_dy,mmlfq,sjf,setf,fcfs= results
            smlfq_avg,smlfq_l2n,smlfq_log = smlfq
            mlfq_avg,mlfq_l2n,mlfq_log = mlfq
            mmlfq_avg,mmlfq_l2n,mmlfq_log = mmlfq
            rmlfq_avg,rmlfq_l2n,rmlfq_log = rmlfq
            mlfq_dy_avg,mlfq_dy_l2n,mlfq_dy_log=mlfq_dy
            rr_avg,rr_l2n,rr_log = rr
            srpt_avg,srpt_l2n,srpt_log = srpt
            sjf_avg,sjf_l2n,sjf_log = sjf
            setf_avg,setf_l2n,setf_log = setf
            fcfs_avg,fcfs_l2n,fcfs_log = fcfs
            #bal_avg,bal_l2n,bal_log=bal
            collect = {"mlfq_dy":mlfq_dy_log,"rmlfq":rmlfq_log,"mlfq":mlfq_log,"srmlfq":smlfq_log,"rr":rr_log,"srpt":srpt_log,"sjf":sjf_log,"setf":setf_log,"fcfs":fcfs_log,"mmlfq":mmlfq_log}
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
            mmlfq_result = mmlfq_avg/srpt_avg
            smlfq_result = smlfq_avg/srpt_avg
            rmlfq_result = rmlfq_avg/srpt_avg
            setf_result = setf_avg/srpt_avg
            fcfs_result = fcfs_avg/srpt_avg
            mlfq_dy_result = mlfq_dy_avg/srpt_avg
            #bal_result = bal_avg/srpt_avg
            
            sjf_fcfs = sjf_avg/fcfs_avg 
            rr_fcfs = rr_avg/fcfs_avg
            mlfq_fcfs = mlfq_avg/fcfs_avg
            mmlfq_fcfs = mmlfq_avg/fcfs_avg
            smlfq_fcfs = smlfq_avg/fcfs_avg
            rmlfq_fcfs = rmlfq_avg/fcfs_avg
            setf_fcfs = setf_avg/fcfs_avg
            srpt_fcfs = srpt_avg/fcfs_avg
            mlfq_dy_fcfs = mlfq_dy_avg/fcfs_avg
            #bal_fcfs = bal_avg/fcfs_avg
            
            
            sjf_l2n_result = sjf_l2n/srpt_l2n 
            rr_l2n_result = rr_l2n/srpt_l2n
            mlfq_l2n_result = mlfq_l2n/srpt_l2n
            mmlfq_l2n_result = mmlfq_l2n/srpt_l2n
            smlfq_l2n_result = smlfq_l2n/srpt_l2n
            rmlfq_l2n_result = rmlfq_l2n/srpt_l2n
            setf_l2n_result = setf_l2n/srpt_l2n
            fcfs_l2n_result = fcfs_l2n/srpt_l2n
            mlfq_dy_l2n_result = mlfq_dy_l2n/srpt_l2n
            #bal_l2n_result = bal_l2n/srpt_l2n
            
            sjf_l2n_fcfs = sjf_l2n/fcfs_l2n 
            rr_l2n_fcfs = rr_l2n/fcfs_l2n
            mlfq_l2n_fcfs = mlfq_l2n/fcfs_l2n
            mmlfq_l2n_fcfs = mmlfq_l2n/fcfs_l2n
            smlfq_l2n_fcfs = smlfq_l2n/fcfs_l2n
            rmlfq_l2n_fcfs = rmlfq_l2n/fcfs_l2n
            setf_l2n_fcfs = setf_l2n/fcfs_l2n
            srpt_l2n_fcfs = srpt_l2n/fcfs_l2n
            mlfq_dy_l2n_fcfs = mlfq_dy_l2n/fcfs_l2n
            #bal_l2n_fcfs= bal_l2n/fcfs_l2n
            
            smlfq_l2n_rr_l2n_result = smlfq_l2n/rr_l2n
            smlfq_comp_setf = smlfq_l2n/setf_l2n
            smlfq_comp_mmlfq = smlfq_l2n/mmlfq_l2n
            #rmlfq_comp_bal_l2n = rmlfq_l2n/bal_l2n
            #rmlfq_comp_bal_avg = rmlfq_avg/bal_avg
            result.append({
                "arrival_rate":Arrival_rate,
                "quantum_multiplier":quantum_multiplier,
                "quantum_decrease":quantum_decrease,
                "bp_parameter":i,
                "SJF/SRPT":sjf_result,
                "RR/SRPT":rr_result,
                "MLFQ/SRPT":mlfq_result,
                "MMLFQ/SRPT":mmlfq_result,
                "SMLFQ/SRPT":smlfq_result,
                "MLFQ_Dy/SRPT":mlfq_dy_result,
                "RMLFQ/SRPT":rmlfq_result,
                "SETF/SRPT":setf_result,
                "FCFS/SRPT":fcfs_result,
                #"BAL/SRPT":bal_result,
                "SJF/FCFS":sjf_fcfs,
                "RR/FCFS":rr_fcfs,
                "MLFQ/FCFS":mlfq_fcfs,
                "MMLFQ/FCFS":mmlfq_fcfs,
                "SMLFQ/FCFS":smlfq_fcfs,
                "MLFQ_Dy/FCFS":mlfq_dy_fcfs,
                "RMLFQ/FCFS":rmlfq_fcfs,
                "SETF/FCFS":setf_fcfs,
                "SPRT/FCFS":srpt_fcfs,
                #"BAL/FCFS":bal_fcfs,
                "SJF_L2_Norm/SRPT_L2_Norm":sjf_l2n_result,
                "RR_L2_Norm/SRPT_L2_Norm":rr_l2n_result,
                "MLFQ_L2_Norm/SRPT_L2_Norm":mlfq_l2n_result,
                "MMLFQ_L2_Norm/SRPT_L2_Norm":mmlfq_l2n_result,
                "SMLFQ_L2_Norm/SRPT_L2_Norm":smlfq_l2n_result,
                "MLFQ_Dy_L2_Norm/SRPT_L2_Norm":mlfq_dy_l2n_result,
                "RMLFQ_L2_Norm/SRPT_L2_Norm":rmlfq_l2n_result,
                "SETF_L2_Norm/SRPT_L2_Norm":setf_l2n_result,
                "FCFS_L2_Norm/SRPT_L2_Norm":fcfs_l2n_result,
                #"BAL_L2_Norm/SRPT_L2_Norm":bal_l2n_result,
                "SJF_L2_Norm/FCFS_L2_Norm":sjf_l2n_fcfs,
                "RR_L2_Norm/FCFS_L2_Norm":rr_l2n_fcfs,
                "MLFQ_L2_Norm/FCFS_L2_Norm":mlfq_l2n_fcfs,
                "MMLFQ_L2_Norm/FCFS_L2_Norm":mmlfq_l2n_fcfs,
                "SMLFQ_L2_Norm/FCFS_L2_Norm":smlfq_l2n_fcfs,
                "MLFQ_Dy_L2_Norm/FCFS_L2_Norm":mlfq_dy_l2n_fcfs,
                "RMLFQ_L2_Norm/FCFS_L2_Norm":rmlfq_l2n_fcfs,
                "SETF_L2_Norm/FCFS_L2_Norm":setf_l2n_fcfs,
                "SRPT_L2_Norm/FCFS_L2_Norm":srpt_l2n_fcfs,
                #"BAL_L2_Norm/FCFS_L2_Norm":bal_l2n_fcfs,
                "SMLFQ_L2_Norm/RR_L2_Norm":smlfq_l2n_rr_l2n_result,
                "SMLFQ_L2_Norm/SETF_L2_Norm":smlfq_comp_setf,
                "SMLFQ_L2_Nprm/MMLFQ_L2_Norm":smlfq_comp_mmlfq
                #"RMLFQ_L2_avg/BAL_L2_Norm_avg":rmlfq_comp_bal_avg,
                #"RMLFQ_L2_Norm/BAL_L2_Norm":rmlfq_comp_bal_l2n
            })
        pool.close()
        pool.join()
    return result
        
    