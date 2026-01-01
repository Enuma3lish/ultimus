#ifndef RUN_RANDOM_H
#define RUN_RANDOM_H

#include <vector>
#include <iostream>
#include <utility>
#include <tuple>
#include <cmath>
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

// Extended version that also calculates longest H L2 norm
// Returns: (total_l2_norm, max_flow_time, longest_H_l2_norm)
template<typename AlgoFunc>
std::tuple<double, double, double> run_random_with_longest_H(
    AlgoFunc algo,
    std::vector<Job>& jobs,  // Pass by reference to preserve completion_time
    int start_job_index,
    int end_job_index) {

    // Call the algorithm function (it will set completion_time on jobs)
    auto result = algo(jobs);

    // Extract L2 norm and max flow time
    double l2_norm_flow_time = result.l2_norm_flow_time;
    double max_flow_time = result.max_flow_time;

    // Calculate longest H L2 norm
    double longest_H_l2_norm = 0.0;
    if (start_job_index >= 0 && end_job_index >= start_job_index) {
        long double sum_sq = 0.0;
        for (int i = start_job_index; i <= end_job_index && i < (int)jobs.size(); i++) {
            // Find job with this job_index
            for (const auto& job : jobs) {
                if (job.job_index == i && job.completion_time > 0) {
                    long long flow_time = job.completion_time - job.arrival_time;
                    sum_sq += static_cast<long double>(flow_time) * flow_time;
                    break;
                }
            }
        }
        longest_H_l2_norm = std::sqrt(static_cast<double>(sum_sq));
    }

    std::cout << "Algorithm: L2 norm = " << l2_norm_flow_time
              << ", maximum flow time = " << max_flow_time
              << ", longest_H L2 norm = " << longest_H_l2_norm << std::endl;

    return std::make_tuple(l2_norm_flow_time, max_flow_time, longest_H_l2_norm);
}

#endif // RUN_RANDOM_H