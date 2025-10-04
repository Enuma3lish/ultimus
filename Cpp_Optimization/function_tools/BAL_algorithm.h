#ifndef BAL_ALGORITHM_H
#define BAL_ALGORITHM_H

#include <vector>
#include <algorithm>
#include <cmath>
#include <limits>
#include <queue>
#include "Job.h"
#include "BAL_Selector.h"

struct BALResult {
    double l2_norm_flow_time;
    double max_flow_time;
};

// Event-driven BAL implementation matching the paper
inline BALResult Bal(std::vector<Job> jobs, double starvation_threshold) {
    if (jobs.empty()) {
        return {0.0, 0.0};
    }
    
    // Sort jobs by arrival time
    std::sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        return a.arrival_time < b.arrival_time;
    });
    
    long long current_time = 0;
    std::vector<Job*> active_jobs;
    size_t next_arrival_idx = 0;
    
    double sum_squared_flow_times = 0.0;
    double max_flow_time = 0.0;
    
    // Initialize job states
    for (auto& job : jobs) {
        job.remaining_time = job.job_size;
        job.starving_time = -1;
        job.waiting_time_ratio = 0.0;
    }
    
    // Main scheduling loop - process time slot by time slot
    while (next_arrival_idx < jobs.size() || !active_jobs.empty()) {
        
        // Add newly arrived jobs at current_time
        while (next_arrival_idx < jobs.size() && 
               jobs[next_arrival_idx].arrival_time <= current_time) {
            active_jobs.push_back(&jobs[next_arrival_idx]);
            next_arrival_idx++;
        }
        
        // If no active jobs, jump to next arrival
        if (active_jobs.empty()) {
            if (next_arrival_idx < jobs.size()) {
                current_time = jobs[next_arrival_idx].arrival_time;
            }
            continue;
        }
        
        // Update waiting_time_ratio and check for starvation
        for (Job* job : active_jobs) {
            if (job->remaining_time > 0) {
                job->waiting_time_ratio = (double)(current_time - job->arrival_time) / 
                                          std::max(1, job->remaining_time);
                
                // Mark as starving if threshold reached
                if (job->waiting_time_ratio >= starvation_threshold && 
                    job->starving_time == -1) {
                    job->starving_time = current_time;
                }
            }
        }
        
        // Select job to execute in time slot [current_time]
        Job* selected = bal_select_next_job_optimized(active_jobs, current_time, starvation_threshold);
        
        if (selected == nullptr) break;
        
        // Determine how long to execute this job
        // Execute until: job completes, or next arrival, or time slot ends
        long long next_event_time = current_time + 1; // End of time slot [current_time]
        
        // Check if another job arrives before slot ends
        if (next_arrival_idx < jobs.size()) {
            long long next_arrival = jobs[next_arrival_idx].arrival_time;
            if (next_arrival < next_event_time) {
                next_event_time = next_arrival;
            }
        }
        
        // Check if selected job completes before slot ends
        if (selected->remaining_time < (next_event_time - current_time)) {
            next_event_time = current_time + selected->remaining_time;
        }
        
        // Execute the selected job
        long long execution_time = next_event_time - current_time;
        selected->remaining_time -= execution_time;
        current_time = next_event_time;
        
        // If job completed, record its flow time
        if (selected->remaining_time == 0) {
            long long flow_time = current_time - selected->arrival_time;
            double flow_time_d = static_cast<double>(flow_time);
            
            sum_squared_flow_times += flow_time_d * flow_time_d;
            max_flow_time = std::max(max_flow_time, flow_time_d);
            
            // Remove completed job from active list
            active_jobs.erase(
                std::remove(active_jobs.begin(), active_jobs.end(), selected),
                active_jobs.end()
            );
        }
    }
    
    BALResult result;
    result.l2_norm_flow_time = std::sqrt(sum_squared_flow_times);
    result.max_flow_time = max_flow_time;
    
    return result;
}

#endif // BAL_ALGORITHM_H