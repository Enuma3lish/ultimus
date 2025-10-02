#ifndef SRPT_SELECTOR_H
#define SRPT_SELECTOR_H

#include <vector>
#include <algorithm>
#include <queue>
#include "Job.h"

// Comparison for SRPT: (remaining_time, arrival_time, job_index)
struct SRPTComparator {
    bool operator()(const Job* a, const Job* b) const {
        if (a->remaining_time != b->remaining_time)
            return a->remaining_time > b->remaining_time;
        if (a->arrival_time != b->arrival_time)
            return a->arrival_time > b->arrival_time;
        return a->job_index > b->job_index;
    }
};

// O(n) linear scan SRPT selector
inline Job* srpt_select_next_job(const std::vector<Job*>& job_queue) {
    if (job_queue.empty()) return nullptr;
    
    Job* best = job_queue[0];
    for (Job* j : job_queue) {
        if (j->remaining_time < best->remaining_time ||
            (j->remaining_time == best->remaining_time && 
             j->arrival_time < best->arrival_time) ||
            (j->remaining_time == best->remaining_time && 
             j->arrival_time == best->arrival_time && 
             j->job_index < best->job_index)) {
            best = j;
        }
    }
    return best;
}

// O(log n) heap-based SRPT selector with automatic fallback
inline Job* srpt_select_next_job_optimized(const std::vector<Job*>& job_queue) {
    size_t n = job_queue.size();
    if (n == 0) return nullptr;
    if (n <= 10) return srpt_select_next_job(job_queue);
    
    std::priority_queue<Job*, std::vector<Job*>, SRPTComparator> pq;
    for (Job* j : job_queue) {
        pq.push(j);
    }
    return pq.top();
}

#endif // SRPT_SELECTOR_H