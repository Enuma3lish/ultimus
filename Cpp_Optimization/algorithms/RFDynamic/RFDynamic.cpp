#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <random>
#include <cassert>
#include <string>
#include <map>
#include <thread>
#include <mutex>
#include "RFDynamic_algorithm.h"
#include "Job.h"
#include "utils.h"
#include "process_avg_folders.h"
#include "process_random_folders.h"
#include "process_softrandom_folders.h"

std::mutex cout_mutex;

// Safe console output
void safe_cout(const std::string& message) {
    std::lock_guard<std::mutex> lock(cout_mutex);
    std::cout << message << std::flush;
}

// Main RFDynamic algorithm - Handles all arrival/completion timing scenarios
inline RFDynamicResult RFDynamic_NC(std::vector<Job> jobs, int checkpoint, int mode) {
    if (jobs.empty()) {
        return {0.0, 0.0, 0.0, {}};
    }
    
    const size_t INITIAL_FCFS_COUNT = 100;  // Run FCFS for first 100 completions
    
    // Sort jobs by arrival time
    std::stable_sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        return a.arrival_time < b.arrival_time;
    });
    
    // Create wrapper jobs with necessary metadata
    std::vector<Job> job_pool_tracking = jobs;  // For tracking completion times
    
    // Job size pool - tracks all completed job sizes
    JobSizePool job_pool;
    
    // Tracking variables
    size_t next_job_idx = 0;  // Index of next job to process (by arrival order)
    size_t completion_count = 0;
    int current_round = 0;
    std::vector<int> completed_sizes_this_round;
    bool use_fcfs = true;  // Start with FCFS
    
    // History tracking
    std::vector<std::string> algorithm_history;
    
    std::cout << "Starting RFDynamic_NC with mode " << mode << ", checkpoint " << checkpoint << std::endl;
    std::cout << "Phase 1: Running FCFS for first " << INITIAL_FCFS_COUNT << " completions..." << std::endl;
    
    // ========== PHASE 1: FCFS for first 100 completions ==========
    {
        // KEY INSIGHT: We collect ALL jobs that might be needed for FCFS to complete 100 jobs.
        // Even if jobs arrive later in "real time", FCFS algorithm handles arrival times correctly.
        // The FCFS algorithm will naturally wait for jobs to arrive based on their arrival_time.
        
        std::vector<Job> phase1_jobs;
        
        // Strategy: Give FCFS enough jobs to ensure 100 completions
        // If we have 1000 jobs total, give it enough to get 100 completions
        // FCFS will respect arrival times internally
        size_t phase1_count = std::min(jobs.size(), INITIAL_FCFS_COUNT * 3);
        
        for (size_t i = 0; i < phase1_count; i++) {
            phase1_jobs.push_back(jobs[i]);
        }
        
        // Run FCFS - it will respect arrival times and complete jobs in FCFS order
        auto fcfs_result = Fcfs_Optimized(phase1_jobs);
        
        // Extract the first 100 completed jobs and add to pool
        // Note: These jobs are now sorted by completion_time after FCFS
        std::vector<std::pair<long long, Job*>> completed_with_time;
        for (auto& job : phase1_jobs) {
            if (job.completion_time > 0) {
                completed_with_time.push_back({job.completion_time, &job});
            }
        }
        
        // Sort by completion time to get first 100 completions
        std::sort(completed_with_time.begin(), completed_with_time.end(),
                  [](const auto& a, const auto& b) { return a.first < b.first; });
        
        // Take first 100 completions
        long long phase1_end_time = 0;
        for (size_t i = 0; i < std::min(INITIAL_FCFS_COUNT, completed_with_time.size()); i++) {
            auto& job = *completed_with_time[i].second;
            job_pool_tracking[job.job_index] = job;
            job_pool.add_job_size(job.job_size);
            completion_count++;
            phase1_end_time = job.completion_time;
        }
        
        // Mark where Phase 1 ended: which jobs have we "processed" by arrival order?
        // All jobs that arrived by phase1_end_time have been considered by FCFS
        // Find the index of the last job that arrived by phase1_end_time
        for (size_t i = 0; i < jobs.size(); i++) {
            if (jobs[i].arrival_time <= phase1_end_time) {
                next_job_idx = i + 1;
            } else {
                break;
            }
        }
        
        algorithm_history.push_back("FCFS");
        std::cout << "Phase 1 complete: " << completion_count << " jobs finished at time " 
                 << phase1_end_time << std::endl;
        std::cout << "  Jobs processed up to index " << next_job_idx 
                 << " (by arrival time)" << std::endl;
        std::cout << "  Pool size: " << job_pool.size() << std::endl;
        
        // IMPORTANT: At this point, jobs[0] to jobs[next_job_idx-1] have been "seen" by Phase 1
        // Some may not have completed yet (if they arrived late), but they've been scheduled
        // Remaining jobs jobs[next_job_idx] onwards are "new" for Phase 2
    }
    
    // ========== PHASE 2: Dynamic switching every 'checkpoint' arrivals ==========
    std::cout << "Phase 2: Dynamic switching every " << checkpoint << " jobs by arrival order..." << std::endl;
    
    current_round = 1;
    completed_sizes_this_round.clear();
    
    // Process remaining jobs in batches of 'checkpoint' by arrival order
    while (next_job_idx < jobs.size()) {
        current_round++;
        
        // Collect next 'checkpoint' jobs by arrival order
        // KEY: Even if all these jobs have already arrived in real-time,
        // we still group them by their arrival order for decision-making
        size_t batch_end = std::min(next_job_idx + checkpoint, jobs.size());
        size_t batch_size = batch_end - next_job_idx;
        
        std::cout << "\n  [Round " << current_round << "] Processing jobs " 
                 << next_job_idx << " to " << (batch_end - 1) 
                 << " (batch size: " << batch_size << ")" << std::endl;
        
        // Prepare simulation set for decision making
        // Use completed jobs from last round + random samples if needed
        std::vector<int> simulation_set = job_pool.get_simulation_set(
            checkpoint, completed_sizes_this_round.size()
        );
        
        std::cout << "    Simulation set: " << simulation_set.size() << " job sizes"
                 << " (" << completed_sizes_this_round.size() << " from last round, "
                 << (simulation_set.size() - completed_sizes_this_round.size()) 
                 << " sampled from pool)" << std::endl;
        
        // Simulate both algorithms and decide
        if (!simulation_set.empty()) {
            double fcfs_l2 = simulate_fcfs_l2(simulation_set);
            double rmlf_l2 = simulate_rmlf_l2(simulation_set);
            
            use_fcfs = (fcfs_l2 <= rmlf_l2);
            
            std::cout << "    Simulation results: FCFS L2=" << fcfs_l2 
                     << ", RMLF L2=" << rmlf_l2 
                     << " -> Chose " << (use_fcfs ? "FCFS" : "RMLF") << std::endl;
            
            algorithm_history.push_back(use_fcfs ? "FCFS" : "RMLF");
        } else {
            // Should not happen after Phase 1, but safety check
            use_fcfs = true;
            algorithm_history.push_back("FCFS");
            std::cout << "    No simulation data, defaulting to FCFS" << std::endl;
        }
        
        // Clear tracking for this round
        completed_sizes_this_round.clear();
        
        // Collect jobs for this round
        std::vector<Job> round_jobs;
        for (size_t i = next_job_idx; i < batch_end; i++) {
            round_jobs.push_back(jobs[i]);
        }
        
        // Run the selected algorithm on this batch
        if (use_fcfs) {
            auto result = Fcfs_Optimized(round_jobs);
            
            // Update completion times and add to pool
            for (auto& job : round_jobs) {
                if (job.completion_time > 0) {
                    job_pool_tracking[job.job_index] = job;
                    job_pool.add_job_size(job.job_size);
                    completed_sizes_this_round.push_back(job.job_size);
                    completion_count++;
                }
            }
        } else {
            auto result = RMLF_algorithm(round_jobs);
            
            // Update completion times and add to pool
            for (auto& job : round_jobs) {
                if (job.completion_time > 0) {
                    job_pool_tracking[job.job_index] = job;
                    job_pool.add_job_size(job.job_size);
                    completed_sizes_this_round.push_back(job.job_size);
                    completion_count++;
                }
            }
        }
        
        std::cout << "    Completed " << completed_sizes_this_round.size() 
                 << " jobs in this round" << std::endl;
        std::cout << "    Total completed: " << completion_count << "/" << jobs.size()
                 << ", Pool size: " << job_pool.size() << std::endl;
        
        // Move to next batch
        next_job_idx = batch_end;
    }
    
    std::cout << "\nSimulation complete!" << std::endl;
    std::cout << "  Total completions: " << completion_count << std::endl;
    std::cout << "  Total rounds: " << current_round << std::endl;
    std::cout << "  Final pool size: " << job_pool.size() << std::endl;
    
    // Calculate metrics from job_pool_tracking
    double sum_flow = 0.0;
    double sum_sq = 0.0;
    double max_flow = 0.0;
    int valid_jobs = 0;
    
    for (const auto& job : job_pool_tracking) {
        if (job.completion_time > 0) {
            long long flow = job.completion_time - job.arrival_time;
            
            if (flow >= job.job_size) {  // Valid flow time
                sum_flow += flow;
                sum_sq += static_cast<double>(flow) * flow;
                max_flow = std::max(max_flow, static_cast<double>(flow));
                valid_jobs++;
            }
        }
    }
    
    double avg_flow = valid_jobs > 0 ? sum_flow / valid_jobs : 0.0;
    double l2_norm = std::sqrt(sum_sq);
    
    std::cout << "Results: avg_flow=" << avg_flow << ", L2=" << l2_norm 
             << ", max_flow=" << max_flow << " (from " << valid_jobs << " jobs)" << std::endl;
    
    return {avg_flow, l2_norm, max_flow, algorithm_history};
}

// Wrapper for multi-mode execution
std::pair<std::map<int, double>, std::map<int, double>> 
RFDynamic_NC_MultiMode(std::vector<Job> jobs, int checkpoint, 
                       const std::vector<int>& modes_to_run) {
    
    std::map<int, double> l2_results;
    std::map<int, double> max_flow_results;
    
    for (int mode : modes_to_run) {
        std::vector<Job> jobs_copy = jobs;  // Make a copy for each mode
        auto result = RFDynamic_NC(jobs_copy, checkpoint, mode);
        l2_results[mode] = result.l2_norm_flow_time;
        max_flow_results[mode] = result.max_flow_time;
        
        std::cout << "Mode " << mode << ": L2=" << result.l2_norm_flow_time 
                  << ", MaxFlow=" << result.max_flow_time << std::endl;
    }
    
    return {l2_results, max_flow_results};
}

int main(int argc, char* argv[]) {
    std::cout << "=== RFDynamic Non-Clairvoyant Scheduler ===" << std::endl;
    std::cout << "Combines RMLF and FCFS with dynamic switching" << std::endl;
    std::cout << std::endl;
    
    std::cout << "Algorithm Flow:" << std::endl;
    std::cout << "  1. Run FCFS for first 100 job completions (build job size pool)" << std::endl;
    std::cout << "  2. Every 100 job arrivals, simulate both algorithms on pool" << std::endl;
    std::cout << "  3. Choose algorithm with lower L2 norm for next round" << std::endl;
    std::cout << "  4. Job size pool continuously grows with completed jobs" << std::endl;
    std::cout << std::endl;
    
    std::cout << "Available Modes:" << std::endl;
    std::cout << "  Mode 1: Use last 1 round of data\n";
    std::cout << "  Mode 2: Use last 2 rounds of data\n";
    std::cout << "  Mode 3: Use last 4 rounds of data\n";
    std::cout << "  Mode 4: Use last 8 rounds of data\n";
    std::cout << "  Mode 5: Use last 16 rounds of data\n";
    std::cout << "  Mode 6: Use all history\n";
    std::cout << std::endl;
    
    // Default parameters
    std::string data_dir = "/home/melowu/Work/ultimus/data";
    std::string output_dir = "/home/melowu/Work/ultimus/RFDynamic_result";
    int checkpoint = 100;  // Default checkpoint
    std::vector<int> modes_to_run = {1, 2, 3, 4, 5, 6};
    std::cout << "Data directory: " << data_dir << std::endl;
    std::cout << "Output directory: " << output_dir << std::endl;
    std::cout << "Checkpoint: " << checkpoint << " jobs" << std::endl;
    std::cout << std::endl;
    
    std::mutex cout_mutex;
    
    // Process different types of data
    std::cout << "Processing data..." << std::endl;
    std::cout << std::endl;
    
    // Check what types of data exist and process accordingly
    auto folders = list_directory(data_dir);
    
    bool has_avg = false;
    bool has_random = false;
    bool has_softrandom = false;
    
    for (const auto& folder : folders) {
        std::string basename = folder.substr(folder.find_last_of('/') + 1);
        if (basename.find("avg_") != std::string::npos) {
            has_avg = true;
        }
        if (basename.find("freq_") != std::string::npos && 
            basename.find("softrandom_") == std::string::npos) {
            has_random = true;
        }
        if (basename.find("softrandom_") != std::string::npos) {
            has_softrandom = true;
        }
    }
    // Process average data if exists
    if (has_avg) {
        std::cout << ">>> Processing average data folders..." << std::endl;
        try {
            process_avg_folders_multimode_RF(
                RFDynamic_NC_MultiMode,
                data_dir,
                output_dir,
                checkpoint,
                modes_to_run,
                cout_mutex
            );
            std::cout << "Average data processing completed." << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "Error processing average data: " << e.what() << std::endl;
        }
        std::cout << std::endl;
    }
    // Process random data
    if (has_random) {
        std::cout << ">>> Processing random data folders..." << std::endl;
        try {
            process_random_folders_multimode_RF(
                RFDynamic_NC_MultiMode,
                data_dir,
                output_dir,
                checkpoint,
                modes_to_run,
                cout_mutex
            );
            std::cout << "Random data processing completed." << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "Error processing random data: " << e.what() << std::endl;
        }
        std::cout << std::endl;
    }
    
    // Process softrandom data
    if (has_softrandom) {
        std::cout << ">>> Processing softrandom data folders..." << std::endl;
        try {
            process_softrandom_folders_multimode_RF(
                RFDynamic_NC_MultiMode,
                data_dir,
                output_dir,
                checkpoint,
                modes_to_run,
                cout_mutex
            );
            std::cout << "Softrandom data processing completed." << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "Error processing softrandom data: " << e.what() << std::endl;
        }
        std::cout << std::endl;
    }
    
    if (!has_random && !has_softrandom) {
        std::cout << "No valid data folders found in " << data_dir << std::endl;
        std::cout << "Looking for folders starting with 'freq_' or 'softrandom_'" << std::endl;
        return 1;
    }
    
    std::cout << "=== All processing completed ===" << std::endl;
    std::cout << "Results saved to: " << output_dir << std::endl;
    
    return 0;
}