import copy

def run_random(algo,jobs):
    #Create a deep copy to ensure each mode gets fresh job data
    jobs_copy = copy.deepcopy(jobs)
    _, l2_norm_flow_time, max_flow = algo(jobs_copy)
    
    return l2_norm_flow_time,max_flow