#ifndef FCFS_ALGORITHM_H
#define FCFS_ALGORITHM_H

#include <vector>
#include <cmath>
#include <algorithm>
#include "Job.h"
#include "FCFS_Selector.h"

// Result struct for FCFS
struct FCFSResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
};

// FCFS algorithm function - can be called from other algorithms
inline FCFSResult Fcfs(std::vector<Job> jobs) {
    int total_jobs = jobs.size();
    if (total_jobs == 0) {
        return {0.0, 0.0, 0.0};
    }
    
    // Sort by arrival time
    std::sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        return a.arrival_time < b.arrival_time;
    });
    
    long long t = 0;  // Use long long to prevent overflow
    int i = 0;
    std::vector<Job*> waiting;
    Job* current = nullptr;
    std::vector<Job*> completed;
    
    while (completed.size() < (size_t)total_jobs) {
        // Add arrivals up to current time
        while (i < total_jobs && jobs[i].arrival_time <= t) {
            jobs[i].remaining_time = jobs[i].job_size;
            jobs[i].start_time = -1;
            jobs[i].completion_time = -1;
            waiting.push_back(&jobs[i]);
            i++;
        }
        
        // Pick next job if idle
        if (current == nullptr && !waiting.empty()) {
            Job* picked = fcfs_select_next_job_optimized(waiting);
            
            // FIX: Use pointer comparison instead of field comparison
            int sel_idx = -1;
            for (size_t k = 0; k < waiting.size(); k++) {
                if (waiting[k] == picked) {  // Direct pointer comparison
                    sel_idx = k;
                    break;
                }
            }
            
            // FIX: Add fallback if pointer matching fails
            if (sel_idx == -1) {
                sel_idx = 0;
                picked = waiting[0];
            }
            
            current = waiting[sel_idx];
            waiting.erase(waiting.begin() + sel_idx);
            
            if (current->start_time == -1) {
                current->start_time = t;
            }
        }
        
        if (current != nullptr) {
            // Non-preemptive: run to completion
            t += current->remaining_time;
            current->completion_time = t;
            current->remaining_time = 0;
            completed.push_back(current);
            current = nullptr;
            continue;
        }
        
        // If idle, jump to next arrival
        if (i < total_jobs) {
            t = std::max(t, (long long)jobs[i].arrival_time);
        } else {
            // No more arrivals and no current job - should not happen
            break;
        }
    }
    
    // Calculate metrics with double precision
    long double sum_flow = 0.0;
    long double sum_sq = 0.0;
    long long max_flow = 0;
    
    for (Job* c : completed) {
        long long flow = c->completion_time - c->arrival_time;
        sum_flow += flow;
        sum_sq += (long double)flow * flow;
        max_flow = std::max(max_flow, flow);
    }
    
    double avg_flow = (double)(sum_flow / total_jobs);
    double l2 = std::sqrt((double)sum_sq);
    
    return {avg_flow, l2, static_cast<double>(max_flow)};
}

#endif // FCFS_ALGORITHM_H