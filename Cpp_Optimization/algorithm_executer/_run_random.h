#ifndef RUN_RANDOM_H
#define RUN_RANDOM_H

#include <vector>
#include <iostream>
#include <utility>
#include "Job.h"

// Template function that can work with any algorithm
// Returns both L2 norm flow time and maximum flow time
template<typename AlgoFunc>
std::pair<double, double> run_random(AlgoFunc algo, std::vector<Job> jobs) {
    // Make a copy of jobs for the algorithm
    std::vector<Job> jobs_copy = jobs;
    
    // Call the algorithm function
    auto result = algo(jobs_copy);
    
    // Extract L2 norm and max flow time
    double l2_norm_flow_time = result.l2_norm_flow_time;
    double max_flow_time = result.max_flow_time;
    
    std::cout << "Algorithm: L2 norm = " << l2_norm_flow_time 
              << ", maximum flow time = " << max_flow_time << std::endl;
    
    return std::make_pair(l2_norm_flow_time, max_flow_time);
}

#endif // RUN_RANDOM_H