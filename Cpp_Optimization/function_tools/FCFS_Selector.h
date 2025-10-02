#ifndef FCFS_SELECTOR_H
#define FCFS_SELECTOR_H

#include <vector>
#include <algorithm>
#include <queue>
#include "Job.h"

// Comparison for FCFS: (arrival_time, job_size, job_index)
struct FCFSComparator {
    bool operator()(const Job* a, const Job* b) const {
        if (a->arrival_time != b->arrival_time)
            return a->arrival_time > b->arrival_time;
        if (a->job_size != b->job_size)
            return a->job_size > b->job_size;
        return a->job_index > b->job_index;
    }
};

// O(n) linear scan FCFS selector
inline Job* fcfs_select_next_job(const std::vector<Job*>& waiting_queue) {
    if (waiting_queue.empty()) return nullptr;
    
    Job* best = waiting_queue[0];
    for (Job* j : waiting_queue) {
        if (j->arrival_time < best->arrival_time ||
            (j->arrival_time == best->arrival_time && j->job_size < best->job_size) ||
            (j->arrival_time == best->arrival_time && j->job_size == best->job_size && 
             j->job_index < best->job_index)) {
            best = j;
        }
    }
    return best;
}

// O(log n) heap-based FCFS selector with automatic fallback
inline Job* fcfs_select_next_job_optimized(const std::vector<Job*>& waiting_queue) {
    size_t n = waiting_queue.size();
    if (n == 0) return nullptr;
    if (n <= 10) return fcfs_select_next_job(waiting_queue);
    
    std::priority_queue<Job*, std::vector<Job*>, FCFSComparator> pq;
    for (Job* j : waiting_queue) {
        pq.push(j);
    }
    return pq.top();
}

#endif // FCFS_SELECTOR_H