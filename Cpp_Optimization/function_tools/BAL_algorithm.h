#ifndef BAL_ALGORITHM_H
#define BAL_ALGORITHM_H

#include <vector>
#include <algorithm>
#include <cmath>
#include <limits>
#include <cassert>
#include "Job.h"
#include "Optimized_Selector.h"

struct BALResult {
    double l2_norm_flow_time;
    double max_flow_time;
};

// Corrected BAL implementation with proper validation
inline BALResult Bal(std::vector<Job> jobs, double starvation_threshold) {
    if (jobs.empty()) {
        return {0.0, 0.0};
    }
    
    // Initialize all job states
    for (auto& job : jobs) {
        job.remaining_time = job.job_size;
        job.start_time = -1;
        job.completion_time = -1;
        job.starving_time = -1;
        job.waiting_time_ratio = 0.0;
    }
    
    // Sort jobs by arrival time
    std::stable_sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        if (a.arrival_time != b.arrival_time)
            return a.arrival_time < b.arrival_time;
        if (a.job_size != b.job_size)
            return a.job_size < b.job_size;
        return a.job_index < b.job_index;
    });
    
    long long current_time = 0;
    std::vector<Job*> active_jobs;
    size_t next_arrival_idx = 0;
    int completed_count = 0;
    const int total_jobs = jobs.size();
    
    double sum_squared_flow_times = 0.0;
    double max_flow_time = 0.0;
    
    // Main scheduling loop
    while (completed_count < total_jobs) {
        long long prev_time = current_time;  // For progress assertion
        
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
        
        // Select job using optimized selector (which handles ratio updates internally)
        Job* selected = bal_select_next_job_fast(active_jobs, current_time, starvation_threshold);
        
        if (selected == nullptr) {
            // No valid job found - shouldn't happen if active_jobs not empty
            std::cerr << "ERROR: No job selected but active_jobs not empty at time " 
                      << current_time << std::endl;
            break;
        }
        
        // Validate selection
        assert(selected->arrival_time <= current_time && 
               "Job cannot execute before arrival");
        assert(selected->remaining_time > 0 && 
               "Selected job must have remaining work");
        
        // Record start time on first execution
        if (selected->start_time == -1) {
            selected->start_time = current_time;
        }
        
        // Determine execution duration
        // Execute until: job completes, or next arrival
        long long next_event_time = current_time + selected->remaining_time; // Job completion
        
        // Check if another job arrives before completion
        if (next_arrival_idx < jobs.size()) {
            long long next_arrival = jobs[next_arrival_idx].arrival_time;
            if (next_arrival < next_event_time) {
                next_event_time = next_arrival;
            }
        }
        
        // Calculate execution time
        long long execution_time = next_event_time - current_time;
        
        // Validate execution time
        assert(execution_time > 0 && "Execution time must be positive");
        assert(execution_time <= selected->remaining_time && 
               "Cannot execute more than remaining time");
        
        // Execute the selected job
        selected->remaining_time -= execution_time;
        current_time = next_event_time;
        
        assert(selected->remaining_time >= 0 && "Remaining time cannot be negative");
        
        // If job completed, record metrics and remove from active list
        if (selected->remaining_time == 0) {
            selected->completion_time = current_time;
            
            // Validate completion
            assert(selected->completion_time >= selected->arrival_time &&
                   "Completion must be after arrival");
            assert(selected->completion_time >= selected->start_time + selected->job_size &&
                   "Completion must account for full job size");
            
            long long flow_time = current_time - selected->arrival_time;
            double flow_time_d = static_cast<double>(flow_time);
            
            sum_squared_flow_times += flow_time_d * flow_time_d;
            max_flow_time = std::max(max_flow_time, flow_time_d);
            
            // Remove completed job from active list
            active_jobs.erase(
                std::remove(active_jobs.begin(), active_jobs.end(), selected),
                active_jobs.end()
            );
            
            completed_count++;
        }
        
        // Assert progress is being made
        assert(current_time > prev_time && "Time must advance each iteration");
    }
    
    // Validate all jobs completed
    assert(completed_count == total_jobs && "All jobs must complete");
    assert(active_jobs.empty() && "Active jobs queue must be empty");
    
    // Validate metrics
    assert(!std::isnan(sum_squared_flow_times) && !std::isinf(sum_squared_flow_times));
    assert(!std::isnan(max_flow_time) && !std::isinf(max_flow_time));
    
    BALResult result;
    result.l2_norm_flow_time = std::sqrt(sum_squared_flow_times);
    result.max_flow_time = max_flow_time;
    
    return result;
}

#endif // BAL_ALGORITHM_H