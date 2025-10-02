#ifndef SJF_ALGORITHM_H
#define SJF_ALGORITHM_H

#include <vector>
#include <queue>
#include <algorithm>
#include <cmath>
#include "Job.h"

// Result structure to match your existing interface
struct SchedulingResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
    
    SchedulingResult() : avg_flow_time(0.0), l2_norm_flow_time(0.0), max_flow_time(0.0) {}
    SchedulingResult(double avg, double l2, double max_f) 
        : avg_flow_time(avg), l2_norm_flow_time(l2), max_flow_time(max_f) {}
};

// Comparator for priority queue - sorts by job size (shortest first)
// FIX: Use Job* pointers instead of Job copies
struct SJFComparator {
    bool operator()(const Job* a, const Job* b) const {
        // Return true if a has LONGER job size (for min-heap based on job_size)
        if (a->job_size != b->job_size) {
            return a->job_size > b->job_size;
        }
        // Tie-breaker: earlier arrival time has priority
        if (a->arrival_time != b->arrival_time) {
            return a->arrival_time > b->arrival_time;
        }
        // Final tie-breaker: job index
        return a->job_index > b->job_index;
    }
};

// Shortest Job First (SJF) Algorithm - Non-preemptive
class ShortestJobFirst {
public:
    SchedulingResult schedule(std::vector<Job>& jobs) {
        if (jobs.empty()) {
            return SchedulingResult();
        }
        
        int n = jobs.size();
        
        // Sort jobs by arrival time
        std::sort(jobs.begin(), jobs.end(), 
                 [](const Job& a, const Job& b) {
                     if (a.arrival_time != b.arrival_time)
                         return a.arrival_time < b.arrival_time;
                     if (a.job_size != b.job_size)
                         return a.job_size < b.job_size;
                     return a.job_index < b.job_index;
                 });
        
        // Initialize jobs
        for (int i = 0; i < n; i++) {
            jobs[i].remaining_time = jobs[i].job_size;
            jobs[i].start_time = -1;
            jobs[i].completion_time = -1;
        }
        
        // FIX: Priority queue for ready jobs using pointers
        std::priority_queue<Job*, std::vector<Job*>, SJFComparator> jobs_queue;
        
        long long current_time = 0;
        int job_index = 0;  // Index for iterating through sorted jobs
        
        long long total_flow_time = 0;
        long long l2_sum = 0;
        long long max_flow = 0;
        
        // Process all jobs
        while (job_index < n || !jobs_queue.empty()) {
            // Add all jobs that have arrived by current_time to the queue
            while (job_index < n && jobs[job_index].arrival_time <= current_time) {
                jobs_queue.push(&jobs[job_index]);
                job_index++;
            }
            
            if (!jobs_queue.empty()) {
                // FIX: Get pointer to the shortest job from the queue
                Job* current_job = jobs_queue.top();
                jobs_queue.pop();
                
                // Record start time
                current_job->start_time = current_time;
                
                // Execute the job (non-preemptive - run to completion)
                current_time += current_job->job_size;
                current_job->completion_time = current_time;
                current_job->remaining_time = 0;
                
                // Calculate flow time (completion_time - arrival_time)
                long long flow_time = current_job->completion_time - current_job->arrival_time;
                
                total_flow_time += flow_time;
                l2_sum += flow_time * flow_time;
                max_flow = std::max(max_flow, flow_time);
                
            } else {
                // No jobs ready - advance time to next arrival
                if (job_index < n) {
                    current_time = jobs[job_index].arrival_time;
                }
            }
        }
        
        // Calculate metrics
        double avg_flow = (double)total_flow_time / n;
        double l2_norm = std::sqrt((double)l2_sum);
        
        return SchedulingResult(avg_flow, l2_norm, (double)max_flow);
    }
};

// Wrapper function for process_avg_folders and process_random_folders
inline SchedulingResult SJF(std::vector<Job>& jobs) {
    ShortestJobFirst scheduler;
    return scheduler.schedule(jobs);
}

#endif // SJF_ALGORITHM_H