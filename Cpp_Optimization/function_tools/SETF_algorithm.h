#ifndef SETF_ALGORITHM_H
#define SETF_ALGORITHM_H

#include <vector>
#include <cmath>
#include <algorithm>
#include <queue>
#include <map>
#include <climits>
#include "Job.h"

struct SETFResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
};

// Internal comparator for SETF min-heap
struct SETFJobComparator {
    bool operator()(const std::pair<int, Job*>& a, const std::pair<int, Job*>& b) const {
        // Min-heap based on elapsed time (using int now)
        if (a.first != b.first) {
            return a.first > b.first;
        }
        // Tie-breaker: earlier arrival time
        if (a.second->arrival_time != b.second->arrival_time) {
            return a.second->arrival_time > b.second->arrival_time;
        }
        // Final tie-breaker: job index
        return a.second->job_index > b.second->job_index;
    }
};

inline SETFResult Setf(std::vector<Job> jobs) {
    int n_jobs = jobs.size();
    if (n_jobs == 0) {
        return {0.0, 0.0, 0.0};
    }
    
    // Sort by arrival time
    std::sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        if (a.arrival_time != b.arrival_time)
            return a.arrival_time < b.arrival_time;
        if (a.job_size != b.job_size)
            return a.job_size < b.job_size;
        return a.job_index < b.job_index;
    });
    
    long long current_time = 0;
    int job_pointer = 0;
    std::vector<Job*> completed_jobs;
    
    // SETF selector state - use int for elapsed time to match job_size
    std::priority_queue<std::pair<int, Job*>, 
                       std::vector<std::pair<int, Job*>>, 
                       SETFJobComparator> active_jobs;
    std::map<int, int> job_elapsed;  // Track elapsed time per job (int)
    
    // Initialize jobs
    for (int i = 0; i < n_jobs; i++) {
        jobs[i].remaining_time = jobs[i].job_size;
        jobs[i].start_time = -1;
        jobs[i].completion_time = -1;
    }
    
    while (job_pointer < n_jobs || !active_jobs.empty()) {
        // Add any jobs that have arrived
        while (job_pointer < n_jobs && jobs[job_pointer].arrival_time <= current_time) {
            active_jobs.push({0, &jobs[job_pointer]});
            job_elapsed[jobs[job_pointer].job_index] = 0;
            job_pointer++;
        }
        
        // If no active jobs, jump to next arrival
        if (active_jobs.empty()) {
            if (job_pointer < n_jobs) {
                current_time = jobs[job_pointer].arrival_time;
                continue;
            } else {
                break;
            }
        }
        
        // Get job with shortest elapsed time
        auto [elapsed, job_ptr] = active_jobs.top();
        active_jobs.pop();
        
        if (job_ptr == nullptr) break;
        
        // FIX: Set start time when job first executes
        if (job_ptr->start_time == -1) {
            job_ptr->start_time = current_time;
        }
        
        int remaining = job_ptr->job_size - job_elapsed[job_ptr->job_index];
        
        // Determine next arrival time
        long long next_arrival = (job_pointer < n_jobs) ? 
            jobs[job_pointer].arrival_time : LLONG_MAX;
        
        // Determine how long to run current job
        long long run_time;
        if (next_arrival > current_time) {
            // Run until completion or next arrival
            run_time = std::min((long long)remaining, next_arrival - current_time);
        } else {
            // No more arrivals, run to completion
            run_time = remaining;
        }
        
        // FIX: Ensure at least 1 time unit of progress
        if (run_time <= 0) {
            run_time = 1;
        }
        
        // Update progress and time
        current_time += run_time;
        job_elapsed[job_ptr->job_index] += run_time;
        
        // Check if job completed
        if (job_elapsed[job_ptr->job_index] >= job_ptr->job_size) {
            job_ptr->completion_time = current_time;
            job_ptr->remaining_time = 0;
            completed_jobs.push_back(job_ptr);
        } else {
            // Requeue if not completed
            job_ptr->remaining_time = job_ptr->job_size - job_elapsed[job_ptr->job_index];
            active_jobs.push({job_elapsed[job_ptr->job_index], job_ptr});
        }
    }
    
    if (completed_jobs.empty()) {
        return {0.0, 0.0, 0.0};
    }
    
    // Calculate metrics with high precision
    long long sum_flow = 0;
    long long sum_sq = 0;
    long long max_flow = 0;
    
    for (Job* c : completed_jobs) {
        long long flow = c->completion_time - c->arrival_time;
        sum_flow += flow;
        sum_sq += flow * flow;
        max_flow = std::max(max_flow, flow);
    }
    
    int n = completed_jobs.size();
    double avg_flow = (double)sum_flow / n;
    double l2 = std::sqrt((double)sum_sq);
    
    return {avg_flow, l2, static_cast<double>(max_flow)};
}

#endif // SETF_ALGORITHM_H