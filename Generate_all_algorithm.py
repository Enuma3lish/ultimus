import Generate_average_flow_time_all_algorithm

algorithmList = ["avg_flow_time_compare_with_fcfs.csv","avg_flow_time_compare_with_srpt.csv","l2norm_compare_with_fcfs.csv","l2norm_compare_with_srpt.csv","Rmlfq_l2norm_compare_with_Rr.csv"]

for name in algorithmList:
    Generate_average_flow_time_all_algorithm.draw(name)