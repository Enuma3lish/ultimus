#ifndef RMLF_ALGORITHM_H
#define RMLF_ALGORITHM_H

#include <vector>
#include <queue>
#include <set>
#include <cmath>
#include <random>
#include <algorithm>
#include <limits>
#include "Job.h"
#include <iostream>
#include <map> // <-- Added for the fix
#include <cassert> // <-- Added for assert() support

struct RMLFResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
};

class RMLFJob {
public:
    int id;
    int arrival_time;
    int job_size;  // Only used for completion check
    double beta;
    
    // Dynamic properties
    int executing_time;
    int current_queue;
    int time_in_current_queue;
    long long completion_time;
    
    RMLFJob(int id_, int arrival_, int size_)
        : id(id_), arrival_time(arrival_), job_size(size_), beta(0.0),
          executing_time(0), current_queue(0), time_in_current_queue(0),
          completion_time(-1) {}
    
    int get_remaining_time() const {
        return job_size - executing_time;
    }
    
    bool is_completed() const {
        return executing_time >= job_size;
    }
};

class MLFQueue {
public:
    int level;
    std::vector<RMLFJob*> jobs;
    
    explicit MLFQueue(int lvl) : level(lvl) {}
    
    void enqueue(RMLFJob* job) {
        jobs.push_back(job);
        job->current_queue = level;
    }
    
    RMLFJob* dequeue(RMLFJob* specific_job = nullptr) {
        if (specific_job) {
            auto it = std::find(jobs.begin(), jobs.end(), specific_job);
            if (it != jobs.end()) {
                jobs.erase(it);
                return specific_job;
            }
            return nullptr;
        } else if (!jobs.empty()) {
            RMLFJob* job = jobs.front();
            jobs.erase(jobs.begin());
            return job;
        }
        return nullptr;
    }
    
    bool is_empty() const {
        return jobs.empty();
    }
    
    size_t length() const {
        return jobs.size();
    }
};

class RMLF {
private:
    static constexpr double TAU = 12.0;
    static constexpr int INITIAL_QUEUES = 1;
    
    std::vector<MLFQueue> queues;
    std::set<RMLFJob*> active_jobs;
    std::vector<RMLFJob*> finished_jobs;
    int total_jobs;
    double first_level_quantum;
    std::mt19937 rng;
    
public:
    explicit RMLF(double first_quantum = 2.0) 
        : total_jobs(0), first_level_quantum(first_quantum) {
        queues.reserve(10);
        for (int i = 0; i < INITIAL_QUEUES; i++) {
            queues.emplace_back(i);
        }
        // Seed random number generator
        std::random_device rd;
        rng.seed(rd());
    }
    
    void insert(RMLFJob* job) {
        total_jobs++;
        job->beta = generate_beta(total_jobs);
        job->current_queue = 0;
        job->time_in_current_queue = 0;
        
        queues[0].enqueue(job);
        active_jobs.insert(job);
    }
    
    void remove(RMLFJob* job) {
    if (active_jobs.find(job) != active_jobs.end()) {
        // CRITICAL: Job MUST be completed before removal
        if (!job->is_completed()) {
            std::cerr << "FATAL ERROR: Attempting to remove incomplete job " 
                     << job->id << "!" << std::endl;
            std::cerr << "  Executed: " << job->executing_time 
                     << " / " << job->job_size << std::endl;
            assert(false && "Cannot remove incomplete job");
            return;  // Don't remove
        }
        
        active_jobs.erase(job);
        finished_jobs.push_back(job);
        queues[job->current_queue].dequeue(job);
    }
}
    void increase(RMLFJob* job) {
        if (active_jobs.find(job) == active_jobs.end()) {
            return;
        }
        
        job->executing_time++;
        job->time_in_current_queue++;
        
        // Check if job has used its time quantum
        double target = calculate_target(job);
        if (job->time_in_current_queue >= target) {
            int current_queue = job->current_queue;
            int next_queue = current_queue + 1;
            
            // Add new queue if needed
            if (next_queue >= static_cast<int>(queues.size())) {
                queues.emplace_back(next_queue);
            }
            
            // Move to next lower priority queue (higher number)
            queues[current_queue].dequeue(job);
            queues[next_queue].enqueue(job);
            job->current_queue = next_queue;
            job->time_in_current_queue = 0;
        }
    }
    
    RMLFJob* select_job(long long current_time) {
        for (auto& queue : queues) {
            if (!queue.is_empty()) {
                for (auto* job : queue.jobs) {
                    // Only select jobs that have arrived and are not completed
                    if (job->arrival_time <= current_time && 
                        job->get_remaining_time() > 0) {
                        return job;
                    }
                }
            }
        }
        return nullptr;
    }
    
    const std::vector<RMLFJob*>& get_finished_jobs() const {
        return finished_jobs;
    }
    
    bool has_active_jobs() const {
        return !active_jobs.empty();
    }
    
private:
    double generate_beta(int job_index) {
        if (job_index <= 3) {
            return 2.0;
        }
        std::uniform_real_distribution<double> dist(0.0, 1.0);
        double u = dist(rng);
        // Avoid u = 1.0 which would cause log(0)
        if (u >= 1.0) u = 0.9999999;
        return -std::log(1.0 - u) / (TAU * std::log(job_index));
    }
    
    double calculate_target(RMLFJob* job) {
        double base_target;
        if (job->current_queue == 0) {
            base_target = std::max(1.0, first_level_quantum - job->beta);
        } else {
            base_target = std::max(1.0, 2.0 - job->beta);
        }
        
        // Apply exponential growth for lower priority queues
        if (job->current_queue == 0) {
            return base_target;
        } else {
            return std::pow(2.0, job->current_queue - 1) * base_target * 2.0;
        }
    }
};

// Main RMLF algorithm function
inline RMLFResult RMLF_algorithm(std::vector<Job>& jobs) {
    if (jobs.empty()) {
        return {0.0, 0.0, 0.0};
    }
    
    // Sort jobs by arrival time
    std::sort(jobs.begin(), jobs.end(), 
              [](const Job& a, const Job& b) {
                  return a.arrival_time < b.arrival_time;
              });
    
    RMLF scheduler(2.0);  // first_level_quantum = 2.0
    std::vector<RMLFJob*> all_rmlf_jobs;
    all_rmlf_jobs.reserve(jobs.size());
    
    // Create RMLF jobs
    for (size_t i = 0; i < jobs.size(); i++) {
        all_rmlf_jobs.push_back(new RMLFJob(
            jobs[i].job_index,
            jobs[i].arrival_time,
            jobs[i].job_size
        ));
    }
    
    size_t jobs_pointer = 0;
    long long current_time = 0;
    size_t n_completed_jobs = 0;
    size_t n_jobs = jobs.size();
    
    // Calculate maximum possible time (for safety check)
    long long max_possible_time = 0;
    for (const auto* job : all_rmlf_jobs) {
        max_possible_time += job->job_size;
    }
    max_possible_time += all_rmlf_jobs.back()->arrival_time + 1000000; // Add buffer
    
    // Start at first job arrival time
    if (!all_rmlf_jobs.empty()) {
        current_time = all_rmlf_jobs[0]->arrival_time;
    }
    
    // Main simulation loop
    while (n_completed_jobs < n_jobs) {
        // Insert new jobs that have arrived
        while (jobs_pointer < jobs.size() && 
               all_rmlf_jobs[jobs_pointer]->arrival_time <= current_time) {
            scheduler.insert(all_rmlf_jobs[jobs_pointer]);
            jobs_pointer++;
        }
        
        // Select and process job
        RMLFJob* selected_job = scheduler.select_job(current_time);
        if (selected_job) {
            // Verify job has arrived (should always be true, but safety check)
            if (selected_job->arrival_time <= current_time) {
                // Process the job (non-clairvoyant - don't look at remaining time)
                scheduler.increase(selected_job);
                
                // Check if completed
                if (selected_job->is_completed()) {
                    selected_job->completion_time = current_time + 1;
                    scheduler.remove(selected_job);
                    n_completed_jobs++;
                }
            } else {
                std::cerr << "ERROR: Job " << selected_job->id 
                         << " executing before arrival time!" << std::endl;
            }
            current_time++;
        } else {
            // No active jobs - skip to next arrival time
            if (jobs_pointer < jobs.size()) {
                current_time = all_rmlf_jobs[jobs_pointer]->arrival_time;
            } else {
                // This should not happen - all jobs arrived but none active
                std::cerr << "Warning: No active jobs but not all completed" << std::endl;
                break;
            }
        }
        
        // Safety check with dynamic limit
        if (current_time > max_possible_time) {
            std::cerr << "ERROR: Simulation exceeded maximum possible time" << std::endl;
            std::cerr << "Current time: " << current_time 
                     << ", Max: " << max_possible_time << std::endl;
            std::cerr << "Completed: " << n_completed_jobs 
                     << " / " << n_jobs << " jobs" << std::endl;
            break;
        }
    }
    
    // =================================================================
    // >>> START FIX
    // Copy completion times from internal RMLFJob list back to the original Job vector
    // This allows RFDynamic to see the completions.
    
    // Map job_index (id) to completion time
    std::map<int, long long> completion_times;
    for (auto* rmlf_job : all_rmlf_jobs) {
        if (rmlf_job->completion_time > 0) {
            completion_times[rmlf_job->id] = rmlf_job->completion_time;
        }
    }
    
    // Update the original input vector
    for (auto& job : jobs) {
        if (completion_times.count(job.job_index)) {
            job.completion_time = completion_times[job.job_index];
        }
    }
    // <<< END FIX
    // =================================================================
    
    // Calculate metrics
    std::vector<long long> flow_times;
    flow_times.reserve(all_rmlf_jobs.size());
    
    double max_flow_time = 0.0;
    int incomplete_jobs = 0;
    
    for (auto* rmlf_job : all_rmlf_jobs) {
        if (rmlf_job->completion_time > 0) {
            // Verify completion time is after arrival time
            if (rmlf_job->completion_time <= rmlf_job->arrival_time) {
                std::cerr << "ERROR: Job " << rmlf_job->id 
                         << " completion_time (" << rmlf_job->completion_time 
                         << ") <= arrival_time (" << rmlf_job->arrival_time << ")" << std::endl;
            }
            
            // Verify job is actually completed
            if (!rmlf_job->is_completed()) {
                std::cerr << "ERROR: Job " << rmlf_job->id 
                         << " has completion_time but is not completed. Remaining: " 
                         << rmlf_job->get_remaining_time() << std::endl;
            }
            
            long long flow_time = rmlf_job->completion_time - rmlf_job->arrival_time;
            
            // Verify flow time is at least job size
            if (flow_time < rmlf_job->job_size) {
                std::cerr << "ERROR: Job " << rmlf_job->id 
                         << " flow_time (" << flow_time 
                         << ") < job_size (" << rmlf_job->job_size << ")" << std::endl;
            }
            
            flow_times.push_back(flow_time);
            max_flow_time = std::max(max_flow_time, static_cast<double>(flow_time));
        } else {
            incomplete_jobs++;
            std::cerr << "WARNING: Job " << rmlf_job->id 
                     << " did not complete. Executed: " << rmlf_job->executing_time 
                     << " / " << rmlf_job->job_size << std::endl;
        }
    }
    
    if (incomplete_jobs > 0) {
        std::cerr << "WARNING: " << incomplete_jobs << " / " << all_rmlf_jobs.size() 
                 << " jobs did not complete!" << std::endl;
    }
    
    double avg_flow_time = 0.0;
    double l2_norm = 0.0;
    
    if (!flow_times.empty()) {
        long long sum = 0;
        for (long long ft : flow_times) {
            sum += ft;
        }
        avg_flow_time = static_cast<double>(sum) / flow_times.size();
        
        double sum_squares = 0.0;
        for (long long ft : flow_times) {
            sum_squares += static_cast<double>(ft) * static_cast<double>(ft);
        }
        l2_norm = std::sqrt(sum_squares);
    }
    
    // Clean up
    for (auto* job : all_rmlf_jobs) {
        delete job;
    }
    
    return {avg_flow_time, l2_norm, max_flow_time};
}

#endif // RMLF_ALGORITHM_H