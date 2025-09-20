import copy

def run(algo,jobs):
    #Create a deep copy to ensure each mode gets fresh job data
    jobs_copy = copy.deepcopy(jobs)
    _, l2_norm_flow_time = algo(jobs_copy)
    
    return l2_norm_flow_time