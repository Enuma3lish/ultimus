#ifndef RFDYNAMIC_ALGORITHM_H
#define RFDYNAMIC_ALGORITHM_H

#include <vector>
#include <queue>
#include <set>
#include <cmath>
#include <random>
#include <algorithm>
#include <limits>
#include <iostream>
#include <cassert>
#include "Job.h"
#include "RMLF_algorithm.h"
#include "Optimized_FCFS_algorithm.h"

// Result structure for RFDynamic
struct RFDynamicResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
    std::vector<std::string> algorithm_history;  // Track which algorithm used each round
};

// ============ Job Size Pool Manager ============
class JobSizePool {
private:
    std::vector<int> pool;  // All completed job sizes
    std::mt19937 rng;
    
public:
    JobSizePool() {
        std::random_device rd;
        rng.seed(rd());
    }
    
    // Add a completed job size to pool
    void add_job_size(int size) {
        pool.push_back(size);
    }
    
    // Get most recent N job sizes
    std::vector<int> get_recent(int n) const {
        if (pool.empty()) return {};
        
        int start_idx = std::max(0, static_cast<int>(pool.size()) - n);
        return std::vector<int>(pool.begin() + start_idx, pool.end());
    }
    
    // Sample N job sizes randomly from pool (with replacement)
    std::vector<int> sample_random(int n) {
        if (pool.empty()) return {};
        
        std::vector<int> samples;
        std::uniform_int_distribution<size_t> dist(0, pool.size() - 1);
        
        for (int i = 0; i < n; i++) {
            samples.push_back(pool[dist(rng)]);
        }
        
        return samples;
    }
    
    // Get pool size
    size_t size() const {
        return pool.size();
    }
    
    // Get a simulation set: recent completed jobs + random samples if needed
    std::vector<int> get_simulation_set(int target_size, int completed_this_round) {
        if (pool.empty()) return {};
        
        std::vector<int> result;
        
        // Take the most recent completed jobs
        if (completed_this_round > 0) {
            int take = std::min(completed_this_round, target_size);
            auto recent = get_recent(take);
            result.insert(result.end(), recent.begin(), recent.end());
        }
        
        // If we need more, sample randomly from pool
        int needed = target_size - result.size();
        if (needed > 0) {
            auto samples = sample_random(needed);
            result.insert(result.end(), samples.begin(), samples.end());
        }
        
        return result;
    }
};

// ============ Simulation Helpers ============

// Simulate FCFS on a job pool with known sizes
inline double simulate_fcfs_l2(const std::vector<int>& job_sizes) {
    if (job_sizes.empty()) return 0.0;
    
    // Create Job objects for simulation
    std::vector<Job> sim_jobs;
    for (size_t i = 0; i < job_sizes.size(); i++) {
        Job j;
        j.arrival_time = 0;  // All arrive at same time
        j.job_size = job_sizes[i];
        j.job_index = i;
        j.remaining_time = job_sizes[i];
        sim_jobs.push_back(j);
    }
    
    // Run FCFS
    auto result = Fcfs_Optimized(sim_jobs);
    return result.l2_norm_flow_time;
}

// Simulate RMLF on a job pool with known sizes
inline double simulate_rmlf_l2(const std::vector<int>& job_sizes) {
    if (job_sizes.empty()) return 0.0;
    
    // Create Job objects for simulation
    std::vector<Job> sim_jobs;
    for (size_t i = 0; i < job_sizes.size(); i++) {
        Job j;
        j.arrival_time = 0;  // All arrive at same time
        j.job_size = job_sizes[i];
        j.job_index = i;
        j.remaining_time = job_sizes[i];
        sim_jobs.push_back(j);
    }
    
    // Run RMLF
    auto result = RMLF_algorithm(sim_jobs);
    return result.l2_norm_flow_time;
}

#endif // RFDYNAMIC_ALGORITHM_H