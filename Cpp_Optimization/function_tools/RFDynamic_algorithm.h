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
    std::vector<std::string> algorithm_history;
};

// ============ Job Size Pool Manager (Round-Based with Fallback) ============
class JobSizePool {
private:
    std::vector<std::vector<int>> rounds_history;  // rounds_history[i] = job sizes completed in round i
    std::mt19937 rng;
    
public:
    JobSizePool() {
        std::random_device rd;
        rng.seed(rd());
        rounds_history.push_back(std::vector<int>());  // Initialize round 0 (empty)
    }
    
    // Start a new round
    void start_new_round() {
        rounds_history.push_back(std::vector<int>());
    }
    
    // Add a completed job size to current round
    void add_job_size(int size) {
        if (rounds_history.empty()) {
            rounds_history.push_back(std::vector<int>());
        }
        rounds_history.back().push_back(size);
    }
    
    // Get total number of job sizes across all rounds
    size_t size() const {
        size_t total = 0;
        for (const auto& round : rounds_history) {
            total += round.size();
        }
        return total;
    }
    
    // Get number of completed rounds
    int get_round_count() const {
        return rounds_history.size();
    }
    
    // Get all job sizes from a specific round
    std::vector<int> get_round(int round_idx) const {
        if (round_idx < 0 || round_idx >= (int)rounds_history.size()) {
            return {};
        }
        return rounds_history[round_idx];
    }
    
    // Sample N job sizes randomly from entire pool (with replacement)
    std::vector<int> sample_random(int n) {
        std::vector<int> all_jobs;
        for (const auto& round : rounds_history) {
            all_jobs.insert(all_jobs.end(), round.begin(), round.end());
        }
        
        if (all_jobs.empty()) return {};
        
        std::vector<int> samples;
        std::uniform_int_distribution<size_t> dist(0, all_jobs.size() - 1);
        
        for (int i = 0; i < n; i++) {
            samples.push_back(all_jobs[dist(rng)]);
        }
        
        return samples;
    }
    
    // **KEY METHOD: Get simulation set based on mode and current round WITH FALLBACK**
    // 
    // Mode behavior with fallback:
    // - Mode 1: Always uses last 1 round
    // - Mode 2: Uses last 2 rounds (but falls back to Mode 1 if current_round < 3)
    // - Mode 3: Uses last 4 rounds (but falls back to Mode 1 if current_round < 5)
    // - Mode 4: Uses last 8 rounds (but falls back to Mode 1 if current_round < 9)
    // - Mode 5: Uses last 16 rounds (but falls back to Mode 1 if current_round < 17)
    // - Mode 6: Uses ALL rounds (always works)
    std::vector<int> get_simulation_set_by_mode(int mode, int current_round) {
        std::vector<int> result;
        
        if (rounds_history.empty() || current_round < 1) {
            return result;
        }
        
        int effective_mode = mode;
        int num_rounds_to_use;
        
        // **CRITICAL FALLBACK LOGIC**
        // Ensure we have enough rounds before using higher modes
        switch(mode) {
            case 1:
                effective_mode = 1;
                num_rounds_to_use = 1;
                break;
                
            case 2:
                if (current_round >= 3) {
                    effective_mode = 2;
                    num_rounds_to_use = 2;
                } else {
                    effective_mode = 1;  // Fallback to Mode 1
                    num_rounds_to_use = 1;
                }
                break;
                
            case 3:
                if (current_round >= 5) {
                    effective_mode = 3;
                    num_rounds_to_use = 4;
                } else {
                    effective_mode = 1;  // Fallback to Mode 1
                    num_rounds_to_use = 1;
                }
                break;
                
            case 4:
                if (current_round >= 9) {
                    effective_mode = 4;
                    num_rounds_to_use = 8;
                } else {
                    effective_mode = 1;  // Fallback to Mode 1
                    num_rounds_to_use = 1;
                }
                break;
                
            case 5:
                if (current_round >= 17) {
                    effective_mode = 5;
                    num_rounds_to_use = 16;
                } else {
                    effective_mode = 1;  // Fallback to Mode 1
                    num_rounds_to_use = 1;
                }
                break;
                
            case 6:
                effective_mode = 6;
                num_rounds_to_use = current_round;  // All available rounds
                break;
                
            default:
                effective_mode = 1;
                num_rounds_to_use = 1;
                break;
        }
        
        // Collect jobs from the last num_rounds_to_use rounds
        int start_round = std::max(0, current_round - num_rounds_to_use);
        
        for (int r = start_round; r < current_round; r++) {
            if (r >= 0 && r < (int)rounds_history.size()) {
                const auto& round_jobs = rounds_history[r];
                result.insert(result.end(), round_jobs.begin(), round_jobs.end());
            }
        }
        
        // If we don't have enough data, sample from entire pool
        int min_samples = 50;
        if ((int)result.size() < min_samples) {
            int needed = min_samples - result.size();
            auto samples = sample_random(needed);
            result.insert(result.end(), samples.begin(), samples.end());
        }
        
        return result;
    }
    
    // Get the effective mode being used (after fallback logic)
    int get_effective_mode(int mode, int current_round) const {
        switch(mode) {
            case 1: return 1;
            case 2: return (current_round >= 3) ? 2 : 1;
            case 3: return (current_round >= 5) ? 3 : 1;
            case 4: return (current_round >= 9) ? 4 : 1;
            case 5: return (current_round >= 17) ? 5 : 1;
            case 6: return 6;
            default: return 1;
        }
    }
    
    // Get all job sizes from all rounds
    std::vector<int> get_all() const {
        std::vector<int> all_jobs;
        for (const auto& round : rounds_history) {
            all_jobs.insert(all_jobs.end(), round.begin(), round.end());
        }
        return all_jobs;
    }
    
    // Clear all history
    void clear() {
        rounds_history.clear();
        rounds_history.push_back(std::vector<int>());
    }
    
    // Debug: Print round statistics
    void print_stats() const {
        std::cout << "JobSizePool Statistics:" << std::endl;
        std::cout << "  Total rounds: " << rounds_history.size() << std::endl;
        std::cout << "  Total jobs: " << size() << std::endl;
        for (size_t i = 0; i < rounds_history.size() && i < 5; i++) {
            std::cout << "  Round " << i << ": " << rounds_history[i].size() << " jobs" << std::endl;
        }
        if (rounds_history.size() > 5) {
            std::cout << "  ..." << std::endl;
        }
    }
};

// ============ Simulation Helpers ============

// Simulate FCFS on a job pool with known sizes
inline double simulate_fcfs_l2(const std::vector<int>& job_sizes) {
    if (job_sizes.empty()) return 0.0;
    
    std::vector<Job> sim_jobs;
    sim_jobs.reserve(job_sizes.size());
    
    for (size_t i = 0; i < job_sizes.size(); i++) {
        Job j;
        j.arrival_time = 0;
        j.job_size = job_sizes[i];
        j.job_index = i;
        j.remaining_time = job_sizes[i];
        sim_jobs.push_back(j);
    }
    
    auto result = Fcfs_Optimized(sim_jobs);
    return result.l2_norm_flow_time;
}

// Simulate RMLF on a job pool with known sizes
inline double simulate_rmlf_l2(const std::vector<int>& job_sizes) {
    if (job_sizes.empty()) return 0.0;
    
    std::vector<Job> sim_jobs;
    sim_jobs.reserve(job_sizes.size());
    
    for (size_t i = 0; i < job_sizes.size(); i++) {
        Job j;
        j.arrival_time = 0;
        j.job_size = job_sizes[i];
        j.job_index = i;
        j.remaining_time = job_sizes[i];
        sim_jobs.push_back(j);
    }
    
    auto result = RMLF_algorithm(sim_jobs);
    return result.l2_norm_flow_time;
}

#endif // RFDYNAMIC_ALGORITHM_H