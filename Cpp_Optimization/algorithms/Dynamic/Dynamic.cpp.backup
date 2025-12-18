#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <fstream>
#include <map>
#include <string>
#include <iomanip>
#include <sstream>
#include <set>
#include <cassert>
#include <thread>
#include <mutex>
#include <atomic>
#include "Optimized_SRPT_algorithm.h"
#include "Optimized_FCFS_algorithm.h"
#include "Optimized_Selector.h"
#include "utils.h"
#include "Job.h"
#include "process_avg_folders.h"
#include "process_random_folders.h"
#include "process_softrandom_folders.h"

// Global mutex for thread-safe console output
std::mutex cout_mutex;

// Thread-safe console output
void safe_cout(const std::string& message) {
    std::lock_guard<std::mutex> lock(cout_mutex);
    std::cout << message << std::flush;
}

struct DynamicResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
};

// Save analysis results for avg files
void save_analysis_results(const std::string& input_file_path, int nJobsPerRound, int mode,
                           const std::vector<std::string>& algorithm_history, int total_rounds) {
    if (input_file_path.empty() || algorithm_history.empty()) {
        return;
    }
    
    size_t last_slash = input_file_path.find_last_of('/');
    std::string dir_path = input_file_path.substr(0, last_slash);
    std::string folder_name = dir_path.substr(dir_path.find_last_of('/') + 1);
    std::string filename = input_file_path.substr(last_slash + 1);
    
    if (folder_name.find("avg_") != 0) {
        return;
    }
    
    int version = extract_version_from_path(folder_name);
    std::regex avg_type_pattern("avg_(\\d+)");
    std::smatch match;
    std::string avg_type;
    if (std::regex_search(folder_name, match, avg_type_pattern)) {
        avg_type = match[1];
    } else {
        return;
    }
    
    // Parse filename using new format
    NewAvgParams params = parse_new_avg_filename(filename);
    
    // Fallback to old format if new format fails
    if (params.arrival_rate < 0) {
        AvgParams old_params = parse_avg_filename(filename);
        if (old_params.arrival_rate < 0) return;
        params.arrival_rate = old_params.arrival_rate;
        params.bp_L = old_params.bp_L;
        params.bp_H = old_params.bp_H;
    }
    
    std::string main_dir = "/Users/melowu/Desktop/ultimus/Dynamic_analysis";
    std::string avg_folder = "avg_" + avg_type;
    std::string mode_folder = "mode_" + std::to_string(mode);
    std::string folder_path = main_dir + "/" + avg_folder + "/" + mode_folder;
    
    create_directory(main_dir);
    create_directory(main_dir + "/" + avg_folder);
    create_directory(folder_path);
    
    int srpt_count = 0, fcfs_count = 0;
    for (const auto& algo : algorithm_history) {
        if (algo == "SRPT") srpt_count++;
        else if (algo == "FCFS") fcfs_count++;
    }
    
    int total = algorithm_history.size();
    double srpt_percentage = total > 0 ? (srpt_count * 100.0 / total) : 0.0;
    double fcfs_percentage = total > 0 ? (fcfs_count * 100.0 / total) : 0.0;
    
    std::string output_file;
    if (version >= 0) {
        output_file = folder_path + "/Dynamic_avg_" + avg_type + "_nJobsPerRound_" + 
                     std::to_string(nJobsPerRound) + "_mode_" + std::to_string(mode) + 
                     "_round_" + std::to_string(version) + ".csv";
    } else {
        output_file = folder_path + "/Dynamic_avg_" + avg_type + "_nJobsPerRound_" + 
                     std::to_string(nJobsPerRound) + "_mode_" + std::to_string(mode) + ".csv";
    }
    
    bool write_header = !std::ifstream(output_file).good();
    
    std::ofstream out(output_file, std::ios::app);
    if (write_header) {
        out << "arrival_rate,bp_L,bp_H,FCFS_percentage,SRPT_percentage,total_rounds\n";
    }
    out << std::fixed << std::setprecision(2);
    out << params.arrival_rate << "," << params.bp_L << "," << params.bp_H << ","
        << fcfs_percentage << "," << srpt_percentage << "," << total_rounds << "\n";
}

// Dynamic scheduling algorithm - CORRECT implementation matching your logic
// Dynamic scheduling algorithm - ALL BUGS FIXED
DynamicResult DYNAMIC(std::vector<Job>& jobs, int nJobsPerRound, int mode, 
                     const std::string& input_file_name = "") {
    int total_jobs = jobs.size();
    if (total_jobs == 0) {
        return {0.0, 0.0, 0.0};
    }
    
    // Sort by arrival time
    std::sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        if (a.arrival_time != b.arrival_time)
            return a.arrival_time < b.arrival_time;
        if (a.job_size != b.job_size)
            return a.job_size < b.job_size;
        return a.job_index < b.job_index;
    });
    
    long long current_time = 0;
    std::vector<Job*> active_jobs;
    std::vector<Job*> completed_jobs;
    int n_arrival_jobs = 0;
    int n_completed_jobs = 0;
    bool is_srpt_better = true;
    int jobs_pointer = 0;
    std::vector<Job> jobs_in_current_round;
    
    std::vector<std::vector<Job>> round_jobs_history;
    int current_round = 1;
    std::vector<std::string> algorithm_history;
    
    // Track currently executing job across iterations
    Job* currently_executing_job = nullptr;
    
    // Initialize all jobs
    for (size_t idx = 0; idx < jobs.size(); idx++) {
        jobs[idx].remaining_time = jobs[idx].job_size;
        jobs[idx].completion_time = -1;
        jobs[idx].start_time = -1;
    }
    
    while (n_completed_jobs < total_jobs) {
        long long prev_time = current_time;
        int prev_completed = n_completed_jobs;
        int prev_jobs_pointer = jobs_pointer;
        
        // Admit arrivals
        while (jobs_pointer < total_jobs && jobs[jobs_pointer].arrival_time <= current_time) {
            Job* job = &jobs[jobs_pointer];
            active_jobs.push_back(job);
            
            Job history_job;
            history_job.arrival_time = job->arrival_time;
            history_job.job_size = job->job_size;
            history_job.job_index = job->job_index;
            jobs_in_current_round.push_back(history_job);
            
            n_arrival_jobs++;
            jobs_pointer++;
        }
        
        // CHECKPOINT LOGIC - Can interrupt currently executing job
        while (n_arrival_jobs >= nJobsPerRound) {
            std::vector<Job> jobs_for_this_round(
                jobs_in_current_round.begin(),
                jobs_in_current_round.begin() + nJobsPerRound
            );
            
            if (!jobs_for_this_round.empty()) {
                round_jobs_history.push_back(jobs_for_this_round);
                
                // CRITICAL: If a job is currently executing, pause it and put back in queue
                if (currently_executing_job != nullptr) {
                    std::stringstream ss;
                    ss << "[Checkpoint at Round " << current_round 
                       << "] Pausing job " << currently_executing_job->job_index
                       << " (remaining: " << currently_executing_job->remaining_time 
                       << ") and putting back in queue\n";
                    safe_cout(ss.str());
                    
                    // Put the currently executing job back into active_jobs
                    active_jobs.push_back(currently_executing_job);
                    currently_executing_job = nullptr;
                }
                
                if (current_round == 1) {
                    is_srpt_better = true;
                    algorithm_history.push_back("SRPT");
                } else {
                    // Determine effective mode
                    int effective_mode = mode;
                    if (mode == 2 && current_round < 3) effective_mode = 1;
                    else if (mode == 3 && current_round < 5) effective_mode = 1;
                    else if (mode == 4 && current_round < 9) effective_mode = 1;
                    else if (mode == 5 && current_round < 17) effective_mode = 1;
                    
                    // Collect jobs from previous rounds based on mode
                    std::vector<Job> jobs_to_simulate;
                    
                    if (effective_mode == 1) {
                        // Last 1 round
                        jobs_to_simulate = round_jobs_history.back();
                    } else if (effective_mode == 2) {
                        // Last 2 rounds
                        size_t start = (round_jobs_history.size() >= 2) ? round_jobs_history.size() - 2 : 0;
                        for (size_t i = start; i < round_jobs_history.size(); i++) {
                            jobs_to_simulate.insert(jobs_to_simulate.end(),
                                round_jobs_history[i].begin(), round_jobs_history[i].end());
                        }
                    } else if (effective_mode == 3) {
                        // Last 4 rounds
                        size_t start = (round_jobs_history.size() >= 4) ? round_jobs_history.size() - 4 : 0;
                        for (size_t i = start; i < round_jobs_history.size(); i++) {
                            jobs_to_simulate.insert(jobs_to_simulate.end(),
                                round_jobs_history[i].begin(), round_jobs_history[i].end());
                        }
                    } else if (effective_mode == 4) {
                        // Last 8 rounds
                        size_t start = (round_jobs_history.size() >= 8) ? round_jobs_history.size() - 8 : 0;
                        for (size_t i = start; i < round_jobs_history.size(); i++) {
                            jobs_to_simulate.insert(jobs_to_simulate.end(),
                                round_jobs_history[i].begin(), round_jobs_history[i].end());
                        }
                    } else if (effective_mode == 5) {
                        // Last 16 rounds
                        size_t start = (round_jobs_history.size() >= 16) ? round_jobs_history.size() - 16 : 0;
                        for (size_t i = start; i < round_jobs_history.size(); i++) {
                            jobs_to_simulate.insert(jobs_to_simulate.end(),
                                round_jobs_history[i].begin(), round_jobs_history[i].end());
                        }
                    } else if (effective_mode == 6) {
                        // All history
                        for (const auto& round : round_jobs_history) {
                            jobs_to_simulate.insert(jobs_to_simulate.end(),
                                round.begin(), round.end());
                        }
                    }
                    
                    // Run simulations
                    std::vector<Job> jobs_srpt_copy = jobs_to_simulate;
                    std::vector<Job> jobs_fcfs_copy = jobs_to_simulate;
                    
                    SRPTResult srpt_result = SRPT(jobs_srpt_copy);
                    FCFSResult fcfs_result = Fcfs(jobs_fcfs_copy);
                    
                    if (std::isnan(srpt_result.l2_norm_flow_time) || std::isnan(fcfs_result.l2_norm_flow_time)) {
                        std::cerr << "WARNING: NaN detected in simulation at round " << current_round << std::endl;
                        is_srpt_better = true;
                    } else {
                        is_srpt_better = srpt_result.l2_norm_flow_time <= fcfs_result.l2_norm_flow_time;
                    }
                    algorithm_history.push_back(is_srpt_better ? "SRPT" : "FCFS");
                    
                    std::stringstream ss;
                    ss << "[Round " << current_round << "] Mode: " 
                       << (is_srpt_better ? "SRPT" : "FCFS")
                       << " (SRPT L2=" << srpt_result.l2_norm_flow_time
                       << ", FCFS L2=" << fcfs_result.l2_norm_flow_time << ")\n";
                    safe_cout(ss.str());
                }
                
                current_round++;
            }
            
            jobs_in_current_round.erase(
                jobs_in_current_round.begin(),
                jobs_in_current_round.begin() + nJobsPerRound
            );
            n_arrival_jobs -= nJobsPerRound;
        }
        
        // Select next job if no job is currently executing
        if (currently_executing_job == nullptr && !active_jobs.empty()) {
            if (is_srpt_better) {
                currently_executing_job = srpt_select_next_job_fast(active_jobs);
            } else {
                currently_executing_job = fcfs_select_next_job_fast(active_jobs);
            }
            
            // Remove from active_jobs
            auto it = std::find(active_jobs.begin(), active_jobs.end(), currently_executing_job);
            if (it != active_jobs.end()) {
                active_jobs.erase(it);
            }
            
            // Defensive check
            if (currently_executing_job && currently_executing_job->remaining_time <= 0) {
                std::cerr << "ERROR: Selected job " << currently_executing_job->job_index 
                          << " has remaining_time=" << currently_executing_job->remaining_time << std::endl;
                currently_executing_job = nullptr;
                continue;
            }
            
            // Validate and set start time
            if (currently_executing_job) {
                assert(currently_executing_job->arrival_time <= current_time && 
                       "Job cannot start before arrival time");
                
                if (currently_executing_job->start_time == -1) {
                    currently_executing_job->start_time = current_time;
                    assert(currently_executing_job->start_time >= currently_executing_job->arrival_time &&
                           "Start time cannot be before arrival time");
                }
            }
        }
        
        // Execute currently executing job
        if (currently_executing_job != nullptr) {
            // Calculate how long to execute before next event
            long long next_arrival_t = (jobs_pointer < total_jobs) ? 
                (long long)jobs[jobs_pointer].arrival_time : LLONG_MAX;
            
            int delta;
            
            if (is_srpt_better) {
                // SRPT: preemptive by arrivals
                // Checkpoint will handle pausing if needed during admission phase
                if (next_arrival_t == LLONG_MAX) {
                    // No more arrivals: run to completion
                    delta = currently_executing_job->remaining_time;
                } else if (next_arrival_t <= current_time) {
                    // Arrival is now/past - admit arrivals first
                    active_jobs.push_back(currently_executing_job);
                    currently_executing_job = nullptr;
                    continue;
                } else {
                    // Calculate time until next arrival
                    long long time_to_next_arrival = next_arrival_t - current_time;
                    
                    if (currently_executing_job->remaining_time <= time_to_next_arrival) {
                        // Job completes before next arrival
                        delta = currently_executing_job->remaining_time;
                    } else {
                        // Preempt at next arrival
                        delta = (int)time_to_next_arrival;
                    }
                }
            } else {
                // FCFS: non-preemptive
                // Job runs to completion - checkpoint will pause it during admission phase
                delta = currently_executing_job->remaining_time;
            }
            
            // Validate delta
            if (delta <= 0) {
                std::cerr << "FATAL ERROR: Invalid delta=" << delta << "\n"
                          << "  job_index=" << currently_executing_job->job_index << "\n"
                          << "  remaining_time=" << currently_executing_job->remaining_time << "\n"
                          << "  current_time=" << current_time << "\n"
                          << "  next_arrival=" << next_arrival_t << "\n"
                          << "  mode=" << (is_srpt_better ? "SRPT" : "FCFS") << "\n";
                std::abort();
            }
            
            // Execute
            current_time += delta;
            currently_executing_job->remaining_time -= delta;
            
            assert(currently_executing_job->remaining_time >= 0 && "Remaining time cannot be negative");
            
            // Check completion
            if (currently_executing_job->remaining_time == 0) {
                // Job completed
                currently_executing_job->completion_time = current_time;
                
                assert(currently_executing_job->completion_time >= currently_executing_job->arrival_time && 
                       "Completion must be after arrival");
                assert(currently_executing_job->completion_time >= currently_executing_job->start_time && 
                       "Completion must be after start");
                assert(currently_executing_job->start_time >= currently_executing_job->arrival_time && 
                       "Start must be after arrival");
                
                completed_jobs.push_back(currently_executing_job);
                n_completed_jobs++;
                currently_executing_job = nullptr;  // Job finished, select new one next iteration
            }
            // If remaining_time > 0: Job continues to next iteration
            // - SRPT: May be preempted by new arrivals
            // - FCFS: Will continue OR be paused at checkpoint during admission phase
            
        } else {
            // No job to run, jump to next arrival
            if (jobs_pointer < total_jobs) {
                long long next_arrival = jobs[jobs_pointer].arrival_time;
                assert(next_arrival > current_time && "Next arrival must be in the future");
                current_time = next_arrival;
            } else {
                assert(active_jobs.empty() && currently_executing_job == nullptr && 
                       "If no job and no arrivals, should be no active jobs");
                break;
            }
        }
        
        // Assert progress
        assert((current_time > prev_time || 
                n_completed_jobs > prev_completed || 
                jobs_pointer > prev_jobs_pointer) && 
               "Scheduler must make progress each iteration");
    }
    
    // Process remaining jobs in last round
    if (!jobs_in_current_round.empty() && n_arrival_jobs > 0) {
        round_jobs_history.push_back(jobs_in_current_round);
        algorithm_history.push_back(is_srpt_better ? "SRPT" : "FCFS");
    }
    
    // Validate completion
    assert(completed_jobs.size() == (size_t)total_jobs && "All jobs must complete");
    assert(active_jobs.empty() && currently_executing_job == nullptr && "All jobs must be completed");
    
    // Calculate metrics
    long double sum_flow = 0.0;
    long double sum_sq = 0.0;
    long long max_flow = 0;
    
    for (Job* c : completed_jobs) {
        assert(c->completion_time >= 0 && "Completion time must be non-negative");
        assert(c->arrival_time >= 0 && "Arrival time must be non-negative");
        assert(c->completion_time >= c->arrival_time && "Completion must be after arrival");
        assert(c->start_time >= c->arrival_time && "Start must be after arrival");
        
        long long flow = c->completion_time - c->arrival_time;
        sum_flow += flow;
        sum_sq += (long double)flow * flow;
        max_flow = std::max(max_flow, flow);
    }
    
    double avg_flow = sum_flow / total_jobs;
    double l2 = std::sqrt((double)sum_sq);
    
    assert(!std::isnan(avg_flow) && !std::isinf(avg_flow) && "avg_flow must be valid");
    assert(!std::isnan(l2) && !std::isinf(l2) && "l2 must be valid");
    
    if (!input_file_name.empty()) {
        save_analysis_results(input_file_name, nJobsPerRound, mode, 
                            algorithm_history, current_round - 1);
    }
    
    return {avg_flow, l2, static_cast<double>(max_flow)};
}
std::map<int, double> run_all_modes_for_file_normal(std::vector<Job> jobs, int nJobsPerRound,
                                                    const std::string& input_file_path,
                                                    const std::vector<int>& modes_to_run) {
    std::map<int, double> mode_results;
    std::mutex results_mutex;
    std::vector<std::thread> threads;
    
    // Process each mode in parallel
    for (int mode : modes_to_run) {
        threads.emplace_back([&, mode]() {
            std::vector<Job> jobs_copy = jobs;
            DynamicResult result = DYNAMIC(jobs_copy, nJobsPerRound, mode, input_file_path);
            
            {
                std::lock_guard<std::mutex> lock(results_mutex);
                mode_results[mode] = result.l2_norm_flow_time;
            }
            
            std::stringstream ss;
            ss << "    Mode " << mode << ": L2 norm = " << std::fixed 
               << std::setprecision(4) << result.l2_norm_flow_time << std::endl;
            safe_cout(ss.str());
        });
    }
    
    // Wait for all mode computations to finish
    for (auto& thread : threads) {
        thread.join();
    }
    
    return mode_results;
}

// For random/softrandom folders: runs all modes and returns pair of maps
std::pair<std::map<int, double>, std::map<int, double>> 
run_all_modes_for_file_frequency(std::vector<Job> jobs, int nJobsPerRound,
                                 const std::vector<int>& modes_to_run) {
    std::map<int, double> mode_results;
    std::map<int, double> max_flow_results;
    std::mutex results_mutex;
    std::vector<std::thread> threads;
    
    // Process each mode in parallel
    for (int mode : modes_to_run) {
        threads.emplace_back([&, mode]() {
            std::vector<Job> jobs_copy = jobs;
            DynamicResult result = DYNAMIC(jobs_copy, nJobsPerRound, mode, "");
            
            {
                std::lock_guard<std::mutex> lock(results_mutex);
                mode_results[mode] = result.l2_norm_flow_time;
                max_flow_results[mode] = result.max_flow_time;
            }
            
            std::stringstream ss;
            ss << "    Mode " << mode << ": L2 norm = " << std::fixed 
               << std::setprecision(4) << result.l2_norm_flow_time 
               << ", Max flow = " << result.max_flow_time << std::endl;
            safe_cout(ss.str());
        });
    }
    
    // Wait for all mode computations to finish
    for (auto& thread : threads) {
        thread.join();
    }
    
    return std::make_pair(mode_results, max_flow_results);
}

// Parse comma-separated mode list
std::vector<int> parse_modes(const std::string& mode_str) {
    std::vector<int> modes;
    std::stringstream ss(mode_str);
    std::string token;
    
    while (std::getline(ss, token, ',')) {
        // Trim whitespace
        token.erase(0, token.find_first_not_of(" \t"));
        token.erase(token.find_last_not_of(" \t") + 1);
        
        try {
            int mode = std::stoi(token);
            if (mode >= 1 && mode <= 8) {
                modes.push_back(mode);
            } else {
                std::cerr << "WARNING: Invalid mode " << mode << " (must be 1-7), skipping\n";
            }
        } catch (const std::exception& e) {
            std::cerr << "WARNING: Invalid mode value '" << token << "', skipping\n";
        }
    }
    
    // Remove duplicates and sort
    std::set<int> unique_modes(modes.begin(), modes.end());
    modes.assign(unique_modes.begin(), unique_modes.end());
    
    return modes;
}

int main(int argc, char* argv[]) {
    // Default values
    int nJobsPerRound = 100;
    std::vector<int> modes_to_run = {1, 2, 3, 4, 5, 6}; // All modes by default
    
    // Parse command-line arguments
    if (argc > 1) {
        if (std::string(argv[1]) == "-h" || std::string(argv[1]) == "--help") {
            return 0;
        }
        
        // Parse nJobsPerRound
        try {
            nJobsPerRound = std::atoi(argv[1]);
            if (nJobsPerRound <= 0) {
                std::cerr << "ERROR: nJobsPerRound must be positive\n";
                return 1;
            }
        } catch (const std::exception& e) {
            std::cerr << "ERROR: Invalid nJobsPerRound value\n";
            return 1;
        }
    }
    
    if (argc > 2) {
        // Parse modes
        modes_to_run = parse_modes(argv[2]);
        if (modes_to_run.empty()) {
            std::cerr << "ERROR: No valid modes specified\n";
            return 1;
        }
    }
    
    std::string data_dir = "/Users/melowu/Desktop/ultimus/data";
    std::string output_dir = "/Users/melowu/Desktop/ultimus/Dynamic_result";
    
    // Detect number of hardware threads
    unsigned int num_threads = std::thread::hardware_concurrency();
    if (num_threads == 0) num_threads = 4; // Fallback if detection fails
    
    std::cout << "============================================================\n";
    std::cout << "Starting Dynamic batch processing with multi-threading:\n";
    std::cout << "  Data directory: " << data_dir << "\n";
    std::cout << "  Output directory: " << output_dir << "\n";
    std::cout << "  nJobsPerRound: " << nJobsPerRound << "\n";
    std::cout << "  Hardware threads available: " << num_threads << "\n";
    std::cout << "  Modes to run: ";
    for (size_t i = 0; i < modes_to_run.size(); i++) {
        std::cout << modes_to_run[i];
        if (i < modes_to_run.size() - 1) std::cout << ", ";
    }
    std::cout << "\n";
    std::cout << "============================================================\n";
    
    create_directory(output_dir);
    
    // Launch three main processing functions in parallel using the extended header functions
    std::vector<std::thread> main_threads;
    
    std::cout << "\nLaunching parallel processing threads...\n\n";
    
    // Thread 1: Process avg files using multimode function
    // main_threads.emplace_back([&]() {
    //     safe_cout("========================================\n");
    //     safe_cout("[Thread 1] Processing avg files...\n");
    //     safe_cout("========================================\n");
    //
    //     // Lambda that wraps our function for the template
    //     auto avg_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
    //                          const std::string& input_file_path,
    //                          const std::vector<int>& modes_to_run) {
    //         return run_all_modes_for_file_normal(jobs, nJobsPerRound, input_file_path, modes_to_run);
    //     };
    //
    //     process_avg_folders_multimode(avg_wrapper, data_dir, output_dir,
    //                                   nJobsPerRound, modes_to_run, cout_mutex);
    //     safe_cout("\n[Thread 1] ✓ Avg files completed!\n\n");
    // });
    
    // Thread 2: Process Bounded Pareto random files using multimode function
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 2] Processing Bounded Pareto random files...\n");
        safe_cout("========================================\n");

        // Lambda that wraps our function for the template
        auto random_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                const std::vector<int>& modes_to_run) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, modes_to_run);
        };

        process_bounded_pareto_random_folders_multimode(random_wrapper, data_dir, output_dir,
                                        nJobsPerRound, modes_to_run, cout_mutex);
        safe_cout("\n[Thread 2] ✓ Bounded Pareto random files completed!\n\n");
    });

    // Thread 3: Process Normal random files using multimode function
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 3] Processing Normal random files...\n");
        safe_cout("========================================\n");

        // Lambda that wraps our function for the template
        auto random_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                const std::vector<int>& modes_to_run) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, modes_to_run);
        };

        process_normal_random_folders_multimode(random_wrapper, data_dir, output_dir,
                                        nJobsPerRound, modes_to_run, cout_mutex);
        safe_cout("\n[Thread 3] ✓ Normal random files completed!\n\n");
    });

    // Thread 4: Process Bounded Pareto softrandom files using multimode function
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 4] Processing Bounded Pareto softrandom files...\n");
        safe_cout("========================================\n");

        // Lambda that wraps our function for the template
        auto softrandom_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                    const std::vector<int>& modes_to_run) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, modes_to_run);
        };

        process_bounded_pareto_softrandom_folders_multimode(softrandom_wrapper, data_dir, output_dir,
                                            nJobsPerRound, modes_to_run, cout_mutex);
        safe_cout("\n[Thread 4] ✓ Bounded Pareto softrandom files completed!\n\n");
    });

    // Thread 5: Process Normal softrandom files using multimode function
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 5] Processing Normal softrandom files...\n");
        safe_cout("========================================\n");

        // Lambda that wraps our function for the template
        auto softrandom_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                    const std::vector<int>& modes_to_run) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, modes_to_run);
        };

        process_normal_softrandom_folders_multimode(softrandom_wrapper, data_dir, output_dir,
                                            nJobsPerRound, modes_to_run, cout_mutex);
        safe_cout("\n[Thread 5] ✓ Normal softrandom files completed!\n\n");
    });

    // Thread 6: Process Bounded Pareto combination random files
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 6] Processing Bounded Pareto combination random files...\n");
        safe_cout("========================================\n");

        auto combination_random_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                            const std::string& input_file_path,
                                            const std::vector<int>& modes_to_run) {
            return run_all_modes_for_file_normal(jobs, nJobsPerRound, input_file_path, modes_to_run);
        };

        process_bounded_pareto_combination_random_folders_multimode(combination_random_wrapper, data_dir, output_dir,
                                                    nJobsPerRound, modes_to_run, cout_mutex);
        safe_cout("\n[Thread 6] ✓ Bounded Pareto combination random files completed!\n\n");
    });

    // Thread 7: Process Normal combination random files
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 7] Processing Normal combination random files...\n");
        safe_cout("========================================\n");

        auto combination_random_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                            const std::string& input_file_path,
                                            const std::vector<int>& modes_to_run) {
            return run_all_modes_for_file_normal(jobs, nJobsPerRound, input_file_path, modes_to_run);
        };

        process_normal_combination_random_folders_multimode(combination_random_wrapper, data_dir, output_dir,
                                                    nJobsPerRound, modes_to_run, cout_mutex);
        safe_cout("\n[Thread 7] ✓ Normal combination random files completed!\n\n");
    });

    // Thread 8: Process Bounded Pareto combination softrandom files
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 8] Processing Bounded Pareto combination softrandom files...\n");
        safe_cout("========================================\n");

        auto combination_softrandom_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                                const std::string& input_file_path,
                                                const std::vector<int>& modes_to_run) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, modes_to_run);
        };

        process_bounded_pareto_combination_softrandom_folders_multimode(combination_softrandom_wrapper, data_dir, output_dir,
                                                         nJobsPerRound, modes_to_run, cout_mutex);
        safe_cout("\n[Thread 8] ✓ Bounded Pareto combination softrandom files completed!\n\n");
    });

    // Thread 9: Process Normal combination softrandom files
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 9] Processing Normal combination softrandom files...\n");
        safe_cout("========================================\n");

        auto combination_softrandom_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                                const std::string& input_file_path,
                                                const std::vector<int>& modes_to_run) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, modes_to_run);
        };

        process_normal_combination_softrandom_folders_multimode(combination_softrandom_wrapper, data_dir, output_dir,
                                                         nJobsPerRound, modes_to_run, cout_mutex);
        safe_cout("\n[Thread 9] ✓ Normal combination softrandom files completed!\n\n");
    });

    // Wait for all main threads to complete
    for (auto& thread : main_threads) {
        thread.join();
    }
    
    std::cout << "\n============================================================\n";
    std::cout << "All Dynamic processing completed successfully!\n";
    std::cout << "============================================================\n";


    
    return 0;
}