#ifndef OPTIMIZED_SRPT_H
#define OPTIMIZED_SRPT_H

#include <vector>
#include <cmath>
#include <algorithm>
#include <cassert>
#include <limits>
#include <set>
#include "Job.h"
#include <climits>
#include <queue>
#include "Optimized_Selector.h"

// Result struct for SRPT
struct SRPTResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
};

// Optimized SRPT implementation with better preemption handling
inline SRPTResult SRPT_Optimized(std::vector<Job> jobs) {
    const int total_jobs = jobs.size();
    if (total_jobs == 0) {
        return {0.0, 0.0, 0.0};
    }
    
    // Initialize all jobs
    for (auto& job : jobs) {
        job.remaining_time = job.job_size;
        job.start_time = -1;
        job.completion_time = -1;
        job.starving_time = -1;
        job.waiting_time_ratio = 0.0;
    }
    
    // Sort by arrival time (stable sort for deterministic behavior)
    std::stable_sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        if (a.arrival_time != b.arrival_time)
            return a.arrival_time < b.arrival_time;
        if (a.job_size != b.job_size)
            return a.job_size < b.job_size;
        return a.job_index < b.job_index;
    });
    
    long long current_time = 0;
    int next_arrival_idx = 0;
    std::vector<Job*> active_jobs;  // All jobs ready to run
    active_jobs.reserve(total_jobs);
    Job* current_job = nullptr;
    int completed_count = 0;
    
    // Main scheduling loop
    while (completed_count < total_jobs) {
        // Admit new arrivals
        bool new_arrivals = false;
        while (next_arrival_idx < total_jobs && 
               jobs[next_arrival_idx].arrival_time <= current_time) {
            active_jobs.push_back(&jobs[next_arrival_idx]);
            next_arrival_idx++;
            new_arrivals = true;
        }
        
        // SRPT preemption check: only reconsider if new jobs arrived
        if (new_arrivals && current_job != nullptr) {
            // Add current job back to active set for comparison
            active_jobs.push_back(current_job);
            current_job = nullptr;
        }
        
        // Select job with shortest remaining time
        if (current_job == nullptr && !active_jobs.empty()) {
            current_job = srpt_select_next_job_fast(active_jobs);
            
            // Remove selected job from active list
            active_jobs.erase(
                std::remove(active_jobs.begin(), active_jobs.end(), current_job),
                active_jobs.end()
            );
            
            // Validate selection
            assert(current_job != nullptr);
            assert(current_job->arrival_time <= current_time);
            assert(current_job->remaining_time > 0);
            
            // Record start time on first execution
            if (current_job->start_time == -1) {
                current_job->start_time = current_time;
            }
        }
        
        // Execute current job if we have one
        if (current_job != nullptr) {
            // Calculate execution duration until next event
            long long next_arrival_time = (next_arrival_idx < total_jobs) ? 
                jobs[next_arrival_idx].arrival_time : LLONG_MAX;
            
            // Run until: job completes OR next arrival (for potential preemption)
            long long delta = std::min(
                (long long)current_job->remaining_time,
                next_arrival_time - current_time
            );
            
            // Ensure we make progress
            if (delta <= 0) {
                if (next_arrival_time > current_time) {
                    delta = current_job->remaining_time;  // No arrival coming, run to completion
                } else {
                    delta = 1;  // Minimal progress
                }
            }
            
            // Execute the job
            current_time += delta;
            current_job->remaining_time -= delta;
            
            // Check if job completed
            if (current_job->remaining_time == 0) {
                current_job->completion_time = current_time;
                
                // Validate completion
                assert(current_job->completion_time >= current_job->arrival_time);
                assert(current_job->completion_time >= current_job->start_time + current_job->job_size);
                
                completed_count++;
                current_job = nullptr;  // Job done, need to select new one
            }
            // If not complete, job may be preempted when new arrivals come
            
        } else if (next_arrival_idx < total_jobs) {
            // No job to run, advance to next arrival
            current_time = jobs[next_arrival_idx].arrival_time;
            
        } else {
            // No jobs and no arrivals - shouldn't happen
            assert(false && "Deadlock detected in SRPT");
            break;
        }
    }
    
    // Validate all jobs completed
    assert(completed_count == total_jobs);
    for (const auto& job : jobs) {
        assert(job.completion_time > 0 && "All jobs must complete");
        assert(job.remaining_time == 0 && "All jobs must have zero remaining time");
    }
    
    // Calculate metrics with high precision
    long double sum_flow = 0.0;
    long double sum_sq = 0.0;
    long long max_flow = 0;
    
    for (const auto& job : jobs) {
        long long flow_time = job.completion_time - job.arrival_time;
        
        // Validate flow time
        assert(flow_time >= job.job_size && "Flow time must be at least job size");
        
        sum_flow += flow_time;
        sum_sq += static_cast<long double>(flow_time) * flow_time;
        max_flow = std::max(max_flow, flow_time);
    }
    
    const double avg_flow = static_cast<double>(sum_flow / total_jobs);
    const double l2_norm = std::sqrt(static_cast<double>(sum_sq));
    
    return {avg_flow, l2_norm, static_cast<double>(max_flow)};
}

// Alternative implementation using a priority queue for active jobs
inline SRPTResult SRPT_PriorityQueue(std::vector<Job> jobs) {
    const int total_jobs = jobs.size();
    if (total_jobs == 0) {
        return {0.0, 0.0, 0.0};
    }
    
    // Initialize and sort
    for (auto& job : jobs) {
        job.remaining_time = job.job_size;
        job.start_time = -1;
        job.completion_time = -1;
    }
    
    std::stable_sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        return a.arrival_time < b.arrival_time;
    });
    
    // Custom comparator for the priority queue (min-heap by remaining time)
    auto cmp = [](Job* a, Job* b) {
        if (a->remaining_time != b->remaining_time)
            return a->remaining_time > b->remaining_time;  // Min-heap
        if (a->arrival_time != b->arrival_time)
            return a->arrival_time > b->arrival_time;
        return a->job_index > b->job_index;
    };
    
    std::priority_queue<Job*, std::vector<Job*>, decltype(cmp)> ready_queue(cmp);
    
    long long current_time = 0;
    int next_arrival_idx = 0;
    int completed_count = 0;
    
    while (completed_count < total_jobs || !ready_queue.empty()) {
        // Admit all jobs that have arrived by current_time
        while (next_arrival_idx < total_jobs && 
               jobs[next_arrival_idx].arrival_time <= current_time) {
            ready_queue.push(&jobs[next_arrival_idx]);
            next_arrival_idx++;
        }
        
        if (!ready_queue.empty()) {
            // Get job with minimum remaining time
            Job* current = ready_queue.top();
            ready_queue.pop();
            
            // Set start time if first execution
            if (current->start_time == -1) {
                current->start_time = current_time;
            }
            
            // Calculate execution duration
            long long next_arrival = (next_arrival_idx < total_jobs) ?
                jobs[next_arrival_idx].arrival_time : LLONG_MAX;
            
            if (next_arrival > current_time + current->remaining_time) {
                // Job completes before next arrival
                current_time += current->remaining_time;
                current->remaining_time = 0;
                current->completion_time = current_time;
                completed_count++;
            } else {
                // Preemption at next arrival
                long long delta = next_arrival - current_time;
                current_time = next_arrival;
                current->remaining_time -= delta;
                
                if (current->remaining_time > 0) {
                    ready_queue.push(current);  // Re-add for later
                } else {
                    current->completion_time = current_time;
                    completed_count++;
                }
            }
        } else if (next_arrival_idx < total_jobs) {
            // Jump to next arrival
            current_time = jobs[next_arrival_idx].arrival_time;
        } else {
            break;  // All done
        }
    }
    
    // Calculate metrics
    long double sum_flow = 0.0, sum_sq = 0.0;
    long long max_flow = 0;
    
    for (const auto& job : jobs) {
        long long flow = job.completion_time - job.arrival_time;
        sum_flow += flow;
        sum_sq += static_cast<long double>(flow) * flow;
        max_flow = std::max(max_flow, flow);
    }
    
    return {
        static_cast<double>(sum_flow / total_jobs),
        std::sqrt(static_cast<double>(sum_sq)),
        static_cast<double>(max_flow)
    };
}

// Wrapper for backward compatibility
inline SRPTResult SRPT(std::vector<Job> jobs) {
    return SRPT_Optimized(jobs);
}

#endif // OPTIMIZED_SRPT_H