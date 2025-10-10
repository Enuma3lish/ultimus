#ifndef OPTIMIZED_SELECTORS_H
#define OPTIMIZED_SELECTORS_H

#include <vector>
#include <algorithm>
#include <limits>
#include "Job.h"

// Optimized SRPT selector using partial sort for small sets
inline Job* srpt_select_next_job_fast(std::vector<Job*>& active_jobs) {
    if (active_jobs.empty()) return nullptr;
    
    // For small sets, use linear scan (better cache locality)
    if (active_jobs.size() <= 8) {
        Job* best = active_jobs[0];
        for (size_t i = 1; i < active_jobs.size(); i++) {
            Job* job = active_jobs[i];
            if (job->remaining_time < best->remaining_time ||
                (job->remaining_time == best->remaining_time && 
                 job->arrival_time < best->arrival_time) ||
                (job->remaining_time == best->remaining_time && 
                 job->arrival_time == best->arrival_time && 
                 job->job_index < best->job_index)) {
                best = job;
            }
        }
        return best;
    }
    
    // For larger sets, use std::min_element with custom comparator
    return *std::min_element(active_jobs.begin(), active_jobs.end(),
        [](const Job* a, const Job* b) {
            if (a->remaining_time != b->remaining_time)
                return a->remaining_time < b->remaining_time;
            if (a->arrival_time != b->arrival_time)
                return a->arrival_time < b->arrival_time;
            return a->job_index < b->job_index;
        });
}

// Optimized FCFS selector
inline Job* fcfs_select_next_job_fast(std::vector<Job*>& active_jobs) {
    if (active_jobs.empty()) return nullptr;
    
    // For small sets, use linear scan
    if (active_jobs.size() <= 8) {
        Job* best = active_jobs[0];
        for (size_t i = 1; i < active_jobs.size(); i++) {
            Job* job = active_jobs[i];
            if (job->arrival_time < best->arrival_time ||
                (job->arrival_time == best->arrival_time && 
                 job->job_size < best->job_size) ||
                (job->arrival_time == best->arrival_time && 
                 job->job_size == best->job_size && 
                 job->job_index < best->job_index)) {
                best = job;
            }
        }
        return best;
    }
    
    // For larger sets, use std::min_element
    return *std::min_element(active_jobs.begin(), active_jobs.end(),
        [](const Job* a, const Job* b) {
            if (a->arrival_time != b->arrival_time)
                return a->arrival_time < b->arrival_time;
            if (a->job_size != b->job_size)
                return a->job_size < b->job_size;
            return a->job_index < b->job_index;
        });
}

// Optimized BAL selector - CORRECTED to match paper's algorithm
// Among starving jobs, select by SRPT (shortest remaining time)
// Among non-starving jobs, select by SRPT
inline Job* bal_select_next_job_fast(std::vector<Job*>& active_jobs, 
                                     long long current_time, 
                                     double starvation_threshold) {
    if (active_jobs.empty()) return nullptr;
    
    Job* best_starving = nullptr;
    Job* best_normal = nullptr;
    
    // Single pass to find both starving and non-starving best candidates
    for (Job* job : active_jobs) {
        if (job->remaining_time <= 0) continue; // Skip completed jobs
        
        // Calculate waiting time ratio
        double waiting_time_ratio = (double)(current_time - job->arrival_time) / 
                                   std::max(1, job->remaining_time);
        
        // Check if starving
        if (waiting_time_ratio >= starvation_threshold) {
            // Among starving jobs: select by SRPT (shortest remaining time)
            if (!best_starving || 
                job->remaining_time < best_starving->remaining_time ||
                (job->remaining_time == best_starving->remaining_time && 
                 job->job_index < best_starving->job_index)) {
                best_starving = job;
            }
        } else {
            // Among non-starving jobs: select by SRPT
            if (!best_normal ||
                job->remaining_time < best_normal->remaining_time ||
                (job->remaining_time == best_normal->remaining_time && 
                 job->job_index < best_normal->job_index)) {
                best_normal = job;
            }
        }
    }
    
    // Prioritize starving jobs
    return best_starving ? best_starving : best_normal;
}

#endif // OPTIMIZED_SELECTORS_H