#ifndef NC_RR_H
#define NC_RR_H

#include <vector>
#include <queue>
#include <deque>
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

// Non-Clairvoyant Round Robin Algorithm
class NonClairvoyantRR {
private:
    int time_quantum;
    
    // Result struct for selector
    struct SelectResult {
        int job_idx;
        int exec_time;
        bool has_job;
    };
    
    // Admit newly arrived jobs to ready queue
    void admitArrivedJobs(const std::vector<Job>& jobs,
                         int& next_arrival_idx,
                         std::deque<int>& ready_queue,
                         int current_time,
                         int total_jobs) {
        while (next_arrival_idx < total_jobs && 
               jobs[next_arrival_idx].arrival_time <= current_time) {
            ready_queue.push_back(next_arrival_idx);
            next_arrival_idx++;
        }
    }
    
    // Non-clairvoyant selector: picks next job without knowing remaining time
    SelectResult selectNextJob(const std::vector<Job>& jobs,
                               int next_arrival_idx,
                               std::deque<int>& ready_queue,
                               int current_time,
                               int total_jobs) {
        SelectResult result;
        result.has_job = false;
        result.job_idx = -1;
        result.exec_time = 0;
        
        if (!ready_queue.empty()) {
            int job_idx = ready_queue.front();
            int remaining = jobs[job_idx].remaining_time;
            int exec_time = std::min(time_quantum, remaining);
            
            // Event-driven: consider next arrival
            if (next_arrival_idx < total_jobs) {
                int next_arrival = jobs[next_arrival_idx].arrival_time;
                if (current_time + exec_time > next_arrival) {
                    exec_time = next_arrival - current_time;
                }
            }
            
            result.job_idx = job_idx;
            result.exec_time = exec_time;
            result.has_job = true;
            return result;
        }
        
        // No job ready - return next arrival time
        if (next_arrival_idx < total_jobs) {
            result.exec_time = jobs[next_arrival_idx].arrival_time;
        }
        
        return result;
    }
    
public:
    NonClairvoyantRR(int quantum = 1) : time_quantum(quantum) {}
    
    // Main scheduling algorithm - returns SchedulingResult
    SchedulingResult schedule(std::vector<Job>& jobs) {
        if (jobs.empty()) {
            return SchedulingResult();
        }
        
        int n = jobs.size();
        
        // Sort jobs by arrival time
        std::sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
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
        
        std::deque<int> ready_queue;
        int current_time = 0;
        int completed_jobs = 0;
        int next_arrival_idx = 0;
        
        long long total_flow = 0;
        long long l2_sum = 0;
        long long max_flow = 0;
        
        // Main scheduling loop
        while (completed_jobs < n) {
            // Admit all jobs that have arrived by current_time
            admitArrivedJobs(jobs, next_arrival_idx, ready_queue, current_time, n);
            
            SelectResult result = selectNextJob(jobs, next_arrival_idx, ready_queue, current_time, n);
            
            if (result.has_job) {
                int job_idx = result.job_idx;
                int exec_time = result.exec_time;
                
                // Record start time if first execution
                if (jobs[job_idx].start_time == -1) {
                    jobs[job_idx].start_time = current_time;
                }
                
                // Execute the job
                current_time += exec_time;
                jobs[job_idx].remaining_time -= exec_time;
                
                // Remove from front of queue
                ready_queue.pop_front();
                
                if (jobs[job_idx].remaining_time <= 0) {
                    // Job completed
                    jobs[job_idx].completion_time = current_time;
                    
                    long long flow = jobs[job_idx].completion_time - jobs[job_idx].arrival_time;
                    total_flow += flow;
                    l2_sum += flow * flow;
                    max_flow = std::max(max_flow, flow);
                    completed_jobs++;
                } else {
                    // Round robin: move to back of queue (only if not completed)
                    ready_queue.push_back(job_idx);
                }
            } else {
                // No job ready, jump to next arrival
                if (next_arrival_idx < n) {
                    current_time = jobs[next_arrival_idx].arrival_time;
                } else {
                    // Should not happen if logic is correct
                    break;
                }
            }
        }
        
        double avg_flow = (double)total_flow / n;
        double l2_norm = std::sqrt((double)l2_sum);
        
        return SchedulingResult(avg_flow, l2_norm, (double)max_flow);
    }
};

// Main NC_RR function that matches your interface
inline SchedulingResult NC_RR(std::vector<Job>& jobs, int time_quantum = 1) {
    NonClairvoyantRR scheduler(time_quantum);
    return scheduler.schedule(jobs);
}

#endif // NC_RR_H