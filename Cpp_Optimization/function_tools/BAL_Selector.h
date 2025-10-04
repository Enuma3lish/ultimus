#ifndef BAL_SELECTOR_H
#define BAL_SELECTOR_H

#include <vector>
#include <algorithm>
#include <queue>
#include <cmath>
#include "Job.h"
#include "SRPT_Selector.h"

// Comparator for BAL starving jobs: (starving_time, -waiting_time_ratio, job_index)
// We want SMALLEST starving_time first (min-heap)
struct BALComparator {
    bool operator()(const Job* a, const Job* b) const {
        if (a->starving_time != b->starving_time)
            return a->starving_time > b->starving_time;  // Min-heap: smaller starving_time has higher priority
        if (std::abs(a->waiting_time_ratio - b->waiting_time_ratio) > 1e-9)
            return a->waiting_time_ratio < b->waiting_time_ratio;  // Larger ratio = higher priority
        return a->job_index > b->job_index;  // Smaller index = higher priority
    }
};

// O(n) linear scan BAL selector for starving jobs
inline Job* select_starving_job(const std::vector<Job*>& starving_jobs) {
    if (starving_jobs.empty()) return nullptr;
    
    Job* best = starving_jobs[0];
    for (Job* job : starving_jobs) {
        // Want SMALLEST starving_time (became starving first)
        if (job->starving_time < best->starving_time ||
            (job->starving_time == best->starving_time && 
             job->waiting_time_ratio > best->waiting_time_ratio) ||
            (job->starving_time == best->starving_time && 
             std::abs(job->waiting_time_ratio - best->waiting_time_ratio) < 1e-9 &&
             job->job_index < best->job_index)) {
            best = job;
        }
    }
    return best;
}

// O(log n) heap-based BAL selector with automatic fallback
inline Job* select_starving_job_optimized(const std::vector<Job*>& starving_jobs) {
    size_t n = starving_jobs.size();
    if (n == 0) return nullptr;
    if (n <= 10) return select_starving_job(starving_jobs);
    
    std::priority_queue<Job*, std::vector<Job*>, BALComparator> pq;
    for (Job* j : starving_jobs) {
        pq.push(j);
    }
    return pq.top();
}

// Dynamic BAL selector - automatically handles starving vs non-starving cases
// This is the function you should use in Dynamic_BAL algorithm
inline Job* bal_select_next_job_optimized(const std::vector<Job*>& active_jobs, 
                                          long long current_time, 
                                          double starvation_threshold) {
    if (active_jobs.empty()) return nullptr;
    
    // Update waiting_time_ratio and identify starving jobs
    std::vector<Job*> starving_jobs;
    
    for (Job* job : active_jobs) {
        if (job->remaining_time > 0) {
            job->waiting_time_ratio = (double)(current_time - job->arrival_time) / 
                                      std::max(1, job->remaining_time);
            
            if (job->waiting_time_ratio >= starvation_threshold) {
                if (job->starving_time == -1) {
                    job->starving_time = current_time;
                }
                starving_jobs.push_back(job);
            }
        }
    }
    
    // If there are starving jobs, prioritize them
    if (!starving_jobs.empty()) {
        return select_starving_job_optimized(starving_jobs);
    }
    
    // Otherwise, use SRPT for non-starving jobs
    return srpt_select_next_job_optimized(active_jobs);
}

#endif // BAL_SELECTOR_H