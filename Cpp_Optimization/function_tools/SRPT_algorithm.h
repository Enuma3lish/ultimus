#ifndef SRPT_ALGORITHM_H
#define SRPT_ALGORITHM_H

#include <vector>
#include <cmath>
#include <algorithm>
#include "Job.h"
#include "SRPT_Selector.h"
#include <climits>

// Result struct for SRPT
struct SRPTResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
};

// SRPT algorithm function - can be called from other algorithms
inline SRPTResult SRPT(std::vector<Job> jobs) {
    int total = jobs.size();
    if (total == 0) {
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
    
    while (completed.size() < (size_t)total) {
        // Admit arrivals at time t
        while (i < total && jobs[i].arrival_time <= t) {
            jobs[i].remaining_time = jobs[i].job_size;
            jobs[i].start_time = -1;
            jobs[i].completion_time = -1;
            waiting.push_back(&jobs[i]);
            i++;
        }
        
        // Consider preemption: add current job back to waiting queue
        if (current != nullptr) {
            waiting.push_back(current);
            current = nullptr;
        }
        
        // Pick SRPT job if available
        if (!waiting.empty()) {
            Job* picked = srpt_select_next_job_optimized(waiting);
            
            // Find the selected job in waiting queue using pointer comparison
            int sel_idx = -1;
            for (size_t k = 0; k < waiting.size(); k++) {
                if (waiting[k] == picked) {  // Direct pointer comparison
                    sel_idx = k;
                    break;
                }
            }
            
            // Fallback: if pointer matching fails, use first job
            if (sel_idx == -1) {
                sel_idx = 0;
                picked = waiting[0];
            }
            
            current = waiting[sel_idx];
            waiting.erase(waiting.begin() + sel_idx);
            
            // Set start time if this is the first time the job runs
            if (current->start_time == -1) {
                current->start_time = t;
            }
            
            // Determine next event time (next arrival or job completion)
            long long next_arrival_t = (i < total) ? (long long)jobs[i].arrival_time : LLONG_MAX;
            long long job_finish_t = t + current->remaining_time;
            
            if (job_finish_t <= next_arrival_t) {
                // Job completes before next arrival - run to completion
                t = job_finish_t;
                current->completion_time = t;
                current->remaining_time = 0;
                completed.push_back(current);
                current = nullptr;
            } else {
                // Next arrival comes first - run until next arrival
                long long delta = next_arrival_t - t;
                t = next_arrival_t;
                current->remaining_time -= delta;
                
                // Check if job completed exactly at arrival time
                if (current->remaining_time == 0) {
                    current->completion_time = t;
                    completed.push_back(current);
                    current = nullptr;
                }
                // else: current job continues, will be reconsidered in next iteration
            }
            continue;
        }
        
        // Idle: jump to next arrival
        if (i < total) {
            t = std::max(t, (long long)jobs[i].arrival_time);
        } else {
            // No more arrivals and no current job - should not happen if logic is correct
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
    
    double avg_flow = (double)(sum_flow / total);
    double l2 = std::sqrt((double)sum_sq);
    
    return {avg_flow, l2, static_cast<double>(max_flow)};
}

#endif // SRPT_ALGORITHM_H