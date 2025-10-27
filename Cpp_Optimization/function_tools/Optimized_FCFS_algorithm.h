#ifndef OPTIMIZED_FCFS_H
#define OPTIMIZED_FCFS_H

#include <vector>
#include <cmath>
#include <algorithm>
#include <deque>
#include <cassert>
#include "Optimized_Selector.h"
#include "Job.h"

// Result struct for FCFS
struct FCFSResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
};

// Optimized FCFS selector integrated into the algorithm
// Uses index-based tracking to avoid pointer issues
class FCFSScheduler {
private:
    std::vector<Job>* jobs_ptr;
    std::deque<int> waiting_indices;  // Use deque for O(1) removal
    int current_job_idx;
    
public:
    FCFSScheduler(std::vector<Job>* jobs) : jobs_ptr(jobs), current_job_idx(-1) {}
    
    // Add job to waiting queue (by index)
    void add_to_waiting(int job_idx) {
        waiting_indices.push_back(job_idx);
    }
    
    // Select next job using FCFS policy
    int select_next_job() {
        if (waiting_indices.empty()) return -1;
        
        // For small queues, use linear scan
        if (waiting_indices.size() <= 8) {
            int best_idx = waiting_indices[0];
            size_t best_pos = 0;
            
            for (size_t i = 1; i < waiting_indices.size(); i++) {
                int idx = waiting_indices[i];
                Job& job = (*jobs_ptr)[idx];
                Job& best = (*jobs_ptr)[best_idx];
                
                // FCFS: First Come First Served (arrival time only)
                if (job.arrival_time < best.arrival_time ||
                    (job.arrival_time == best.arrival_time && job.job_index < best.job_index)) {
                    best_idx = idx;
                    best_pos = i;
                }
            }
            
            // Remove selected job from waiting queue
            waiting_indices.erase(waiting_indices.begin() + best_pos);
            return best_idx;
        }
        
        // For larger queues, find minimum element
        auto min_it = std::min_element(waiting_indices.begin(), waiting_indices.end(),
            [this](int a_idx, int b_idx) {
                Job& a = (*jobs_ptr)[a_idx];
                Job& b = (*jobs_ptr)[b_idx];
                
                // FCFS: First Come First Served (arrival time only)
                if (a.arrival_time != b.arrival_time)
                    return a.arrival_time < b.arrival_time;
                // Tiebreaker: use job_index to maintain deterministic order
                return a.job_index < b.job_index;
            });
        
        int selected = *min_it;
        waiting_indices.erase(min_it);
        return selected;
    }
    
    bool has_waiting_jobs() const {
        return !waiting_indices.empty();
    }
    
    size_t waiting_count() const {
        return waiting_indices.size();
    }
};

// Optimized FCFS algorithm with correctness guarantees
inline FCFSResult Fcfs_Optimized(std::vector<Job>& jobs) {
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
    
    // Sort ONLY by arrival time (FCFS = First Come First Served)
    // Use stable_sort to maintain original order for jobs with same arrival time
    std::stable_sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        if (a.arrival_time != b.arrival_time)
            return a.arrival_time < b.arrival_time;
        // Tiebreaker: use job_index for deterministic behavior
        return a.job_index < b.job_index;
    });
    
    FCFSScheduler scheduler(&jobs);
    long long current_time = 0;
    int next_arrival_idx = 0;
    int current_job_idx = -1;
    int completed_count = 0;
    
    // Main scheduling loop
    while (completed_count < total_jobs) {
        // Admit all jobs that have arrived by current_time
        while (next_arrival_idx < total_jobs && 
               jobs[next_arrival_idx].arrival_time <= current_time) {
            scheduler.add_to_waiting(next_arrival_idx);
            next_arrival_idx++;
        }
        
        // If no current job, select one from waiting queue
        if (current_job_idx == -1 && scheduler.has_waiting_jobs()) {
            current_job_idx = scheduler.select_next_job();
            
            // Validate selection
            assert(current_job_idx >= 0 && current_job_idx < total_jobs);
            assert(jobs[current_job_idx].arrival_time <= current_time);
            assert(jobs[current_job_idx].remaining_time > 0);
            
            // Record start time
            if (jobs[current_job_idx].start_time == -1) {
                jobs[current_job_idx].start_time = current_time;
            }
        }
        
        // Execute current job if we have one
        if (current_job_idx != -1) {
            Job& current_job = jobs[current_job_idx];
            
            // FCFS is non-preemptive: run to completion
            current_time += current_job.remaining_time;
            current_job.remaining_time = 0;
            current_job.completion_time = current_time;
            
            // Validate completion
            assert(current_job.completion_time >= current_job.arrival_time);
            assert(current_job.completion_time >= current_job.start_time + current_job.job_size);
            
            completed_count++;
            current_job_idx = -1;  // Mark as no current job
            
        } else if (next_arrival_idx < total_jobs) {
            // No job to run, jump to next arrival
            current_time = jobs[next_arrival_idx].arrival_time;
            
        } else {
            // No current job and no more arrivals - this shouldn't happen
            assert(false && "Deadlock: no job to run and no arrivals");
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

// Wrapper for backward compatibility
inline FCFSResult Fcfs(std::vector<Job>& jobs) {
    return Fcfs_Optimized(jobs);
}

#endif // OPTIMIZED_FCFS_H