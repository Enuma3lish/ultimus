#ifndef RUN_H
#define RUN_H

#include <vector>
#include <iostream>
#include "Job.h"

// Template function that can work with any algorithm
// Returns only L2 norm flow time
template<typename AlgoFunc>
double run(AlgoFunc algo, std::vector<Job> jobs) {
    // Make a copy of jobs for the algorithm
    std::vector<Job> jobs_copy = jobs;
    
    // Call the algorithm function
    auto result = algo(jobs_copy);
    
    // Extract L2 norm (assuming result is a struct with l2_norm_flow_time)
    double l2_norm_flow_time = result.l2_norm_flow_time;
    
    std::cout << "Algorithm: L2 norm = " << l2_norm_flow_time << std::endl;
    
    return l2_norm_flow_time;
}

#endif // RUN_H