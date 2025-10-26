#ifndef MLFQ_H
#define MLFQ_H

#include <vector>
#include <queue>
#include <deque>
#include <algorithm>
#include <cmath>
#include <iostream>
#include "Job.h"

// Structure to hold MLFQ algorithm results
struct MLFQResult {
    double l2_norm_flow_time;
    double max_flow_time;
    std::vector<long long> flow_times;
};

// Structure to represent a job in the MLFQ queue
struct MLFQJobEntry {
    Job job;                      // The job itself
    long long first_executed_time; // When job first started execution (-1 if not yet executed)
    int current_queue_level;      // Current queue level (1-indexed)
    
    MLFQJobEntry(const Job& j, int queue_level) 
        : job(j), first_executed_time(-1), current_queue_level(queue_level) {}
};

// Non-clairvoyant Multi-Level Feedback Queue Scheduler
// Queue numbering starts at 1
// Queue i has time quantum 2^(i-1): Queue 1 = 1, Queue 2 = 2, Queue 3 = 4, etc.
MLFQResult MLFQ(std::vector<Job> jobs, int num_queues = 100) {
    // Initialize queues (indexed 1 to num_queues)
    std::vector<std::deque<MLFQJobEntry>> queues(num_queues + 1);
    
    // Time quantum for each queue: queue i has quantum 2^(i-1)
    std::vector<int> time_quanta(num_queues + 1);
    for (int i = 1; i <= num_queues; i++) {
        time_quanta[i] = (1 << (i - 1)); // 2^(i-1)
    }
    
    // Sort jobs by arrival time
    std::sort(jobs.begin(), jobs.end(), 
              [](const Job& a, const Job& b) { return a.arrival_time < b.arrival_time; });
    
    long long current_time = 0;
    std::vector<long long> flow_times;
    int jobs_in_system = jobs.size();
    size_t job_index = 0;
    
    // Initialize remaining_time for all jobs
    for (auto& job : jobs) {
        job.remaining_time = job.job_size;
    }
    
    while (jobs_in_system > 0) {
        // Add newly arrived jobs to queue 1 (highest priority)
        while (job_index < jobs.size() && jobs[job_index].arrival_time <= current_time) {
            queues[1].push_back(MLFQJobEntry(jobs[job_index], 1));
            job_index++;
        }
        
        // Find the highest priority non-empty queue
        bool job_executed = false;
        for (int i = 1; i <= num_queues; i++) {
            if (!queues[i].empty()) {
                // Get job from front of queue
                MLFQJobEntry entry = queues[i].front();
                queues[i].pop_front();
                
                // BUG CHECK: Ensure job doesn't execute before arrival
                if (current_time < entry.job.arrival_time) {
                    std::cerr << "ERROR: Attempting to execute job " << entry.job.job_index 
                              << " at time " << current_time 
                              << " before arrival time " << entry.job.arrival_time << std::endl;
                    current_time = entry.job.arrival_time;
                }
                
                // Record first execution time
                if (entry.first_executed_time == -1) {
                    entry.first_executed_time = current_time;
                    
                    // BUG CHECK: First execution time should be >= arrival time
                    if (entry.first_executed_time < entry.job.arrival_time) {
                        std::cerr << "ERROR: Job " << entry.job.job_index 
                                  << " first executed at " << entry.first_executed_time
                                  << " before arrival at " << entry.job.arrival_time << std::endl;
                    }
                }
                
                // Execute for quantum time or until job completes (non-clairvoyant)
                int quantum = std::min(time_quanta[i], entry.job.remaining_time);
                entry.job.remaining_time -= quantum;
                current_time += quantum;
                
                // Check if job is complete
                if (entry.job.remaining_time == 0) {
                    // Job finished
                    long long flow_time = current_time - entry.job.arrival_time;
                    flow_times.push_back(flow_time);
                    jobs_in_system--;
                    job_executed = true;
                } else {
                    // Job not finished - move to next queue or stay in last queue
                    // BUG CHECK: Job should remain in system
                    if (i < num_queues) {
                        // Move to next lower priority queue
                        entry.current_queue_level = i + 1;
                        queues[i + 1].push_back(entry);
                    } else {
                        // Stay in the lowest priority queue
                        queues[i].push_back(entry);
                    }
                    job_executed = true;
                }
                
                break; // Process only one job per time step
            }
        }
        
        // If no job was available to execute, advance time
        if (!job_executed) {
            if (job_index < jobs.size()) {
                // Jump to next arrival time
                current_time = jobs[job_index].arrival_time;
            } else {
                // No more jobs arriving - this shouldn't happen if jobs_in_system > 0
                std::cerr << "ERROR: No jobs in queues but jobs_in_system = " 
                          << jobs_in_system << std::endl;
                break;
            }
        }
    }
    
    // Calculate results
    MLFQResult result;
    result.flow_times = flow_times;
    
    if (flow_times.empty()) {
        result.l2_norm_flow_time = 0.0;
        result.max_flow_time = 0.0;
    } else {
        // Calculate L2 norm
        double sum_squares = 0.0;
        long long max_ft = 0;
        for (long long ft : flow_times) {
            sum_squares += static_cast<double>(ft) * static_cast<double>(ft);
            max_ft = std::max(max_ft, ft);
        }
        result.l2_norm_flow_time = std::sqrt(sum_squares);
        result.max_flow_time = static_cast<double>(max_ft);
    }
    
    return result;
}

#endif // MLFQ_H