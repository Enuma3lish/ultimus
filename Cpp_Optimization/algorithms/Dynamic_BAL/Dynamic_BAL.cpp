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
#include <memory>
#include "BAL_algorithm.h"
#include "FCFS_algorithm.h"
#include "BAL_Selector.h"
#include "FCFS_Selector.h"
#include "utils.h"
#include "Job.h"
#include <climits>

// Global mutex for thread-safe console output
std::mutex cout_mutex;

// Thread-safe console output with move semantics
void safe_cout(std::string&& message) {
    std::lock_guard<std::mutex> lock(cout_mutex);
    std::cout << message << std::flush;
}

struct DynamicResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
};

// Save analysis results for avg files (optimized)
void save_analysis_results(const std::string& input_file_path, int nJobsPerRound, int mode,
                           const std::vector<std::string>& algorithm_history, int total_rounds) {
    if (input_file_path.empty() || algorithm_history.empty()) {
        return;
    }
    
    const size_t last_slash = input_file_path.find_last_of('/');
    const std::string dir_path = input_file_path.substr(0, last_slash);
    const std::string folder_name = dir_path.substr(dir_path.find_last_of('/') + 1);
    const std::string filename = input_file_path.substr(last_slash + 1);
    
    if (folder_name.find("avg_") != 0) {
        return;
    }
    
    const int version = extract_version_from_path(folder_name);
    static const std::regex avg_type_pattern("avg_(\\d+)");
    std::smatch match;
    std::string avg_type;
    if (std::regex_search(folder_name, match, avg_type_pattern)) {
        avg_type = match[1];
    } else {
        return;
    }
    
    const AvgParams params = parse_avg_filename(filename);
    if (params.arrival_rate < 0) return;
    
    const std::string main_dir = "/home/melowu/Work/ultimus/Dynamic_BAL_analysis";
    const std::string avg_folder = "avg_" + avg_type;
    const std::string mode_folder = "mode_" + std::to_string(mode);
    const std::string folder_path = main_dir + "/" + avg_folder + "/" + mode_folder;
    
    create_directory(main_dir);
    create_directory(main_dir + "/" + avg_folder);
    create_directory(folder_path);
    
    // Count algorithms using std::count
    const int bal_count = std::count(algorithm_history.begin(), algorithm_history.end(), "BAL");
    const int fcfs_count = std::count(algorithm_history.begin(), algorithm_history.end(), "FCFS");
    
    const int total = algorithm_history.size();
    const double bal_percentage = total > 0 ? (bal_count * 100.0 / total) : 0.0;
    const double fcfs_percentage = total > 0 ? (fcfs_count * 100.0 / total) : 0.0;
    
    std::string output_file;
    if (version >= 0) {
        output_file = folder_path + "/Dynamic_BAL_avg_" + avg_type + "_nJobsPerRound_" + 
                     std::to_string(nJobsPerRound) + "_mode_" + std::to_string(mode) + 
                     "_round_" + std::to_string(version) + ".csv";
    } else {
        output_file = folder_path + "/Dynamic_BAL_avg_" + avg_type + "_nJobsPerRound_" + 
                     std::to_string(nJobsPerRound) + "_mode_" + std::to_string(mode) + ".csv";
    }
    
    const bool write_header = !std::ifstream(output_file).good();
    
    std::ofstream out(output_file, std::ios::app);
    if (write_header) {
        out << "arrival_rate,bp_L,bp_H,FCFS_percentage,BAL_percentage,total_rounds\n";
    }
    out << std::fixed << std::setprecision(2);
    out << params.arrival_rate << "," << params.bp_L << "," << params.bp_H << ","
        << fcfs_percentage << "," << bal_percentage << "," << total_rounds << "\n";
}

// Dynamic scheduling algorithm with bug fixes and optimizations
DynamicResult DYNAMIC_BAL(std::vector<Job>& jobs, int nJobsPerRound, int mode, 
                     const std::string& input_file_name = "") {
    const int total_jobs = jobs.size();
    if (total_jobs == 0) {
        return {0.0, 0.0, 0.0};
    }
    
    // Sort by arrival time (stable sort for deterministic ordering)
    std::stable_sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        if (a.arrival_time != b.arrival_time)
            return a.arrival_time < b.arrival_time;
        if (a.job_size != b.job_size)
            return a.job_size < b.job_size;
        return a.job_index < b.job_index;
    });
    
    long long current_time = 0;
    std::vector<Job*> active_jobs;
    std::vector<Job*> completed_jobs;
    active_jobs.reserve(total_jobs / 10);  // Optimization: pre-allocate
    completed_jobs.reserve(total_jobs);
    
    int n_arrival_jobs = 0;
    int n_completed_jobs = 0;
    bool is_bal_better = true;
    int jobs_pointer = 0;
    std::vector<Job> jobs_in_current_round;
    jobs_in_current_round.reserve(nJobsPerRound * 2);  // Optimization
    
    std::vector<std::vector<Job>> round_jobs_history;
    round_jobs_history.reserve(total_jobs / nJobsPerRound + 10);  // Optimization
    int current_round = 1;
    std::vector<std::string> algorithm_history;
    algorithm_history.reserve(total_jobs / nJobsPerRound + 10);  // Optimization
    
    // Initialize all jobs
    for (auto& job : jobs) {
        job.remaining_time = job.job_size;
        job.completion_time = -1;
        job.start_time = -1;
    }
    
    while (n_completed_jobs < total_jobs) {
        // Track progress each iteration
        const long long prev_time = current_time;
        const int prev_completed = n_completed_jobs;
        const int prev_jobs_pointer = jobs_pointer;
        
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
        
        // Checkpoint logic
        while (n_arrival_jobs >= nJobsPerRound) {
            std::vector<Job> jobs_for_this_round(
                jobs_in_current_round.begin(),
                jobs_in_current_round.begin() + nJobsPerRound
            );
            
            if (!jobs_for_this_round.empty()) {
                round_jobs_history.push_back(std::move(jobs_for_this_round));  // Use move
                
                if (current_round == 1) {
                    is_bal_better = true;
                    algorithm_history.push_back("BAL");
                } else {
                    // Determine effective mode
                    int effective_mode = mode;
                    if (mode == 2 && current_round < 3) effective_mode = 1;
                    else if (mode == 3 && current_round < 5) effective_mode = 1;
                    else if (mode == 4 && current_round < 9) effective_mode = 1;
                    else if (mode == 5 && current_round < 17) effective_mode = 1;
                    
                    // Collect jobs from previous rounds
                    std::vector<Job> jobs_to_simulate;
                    jobs_to_simulate.reserve(nJobsPerRound * 16);  // Optimization
                    
                    // Determine start index based on mode
                    size_t start_idx = 0;
                    switch (effective_mode) {
                        case 1: start_idx = (round_jobs_history.size() >= 1) ? round_jobs_history.size() - 1 : 0; break;
                        case 2: start_idx = (round_jobs_history.size() >= 2) ? round_jobs_history.size() - 2 : 0; break;
                        case 3: start_idx = (round_jobs_history.size() >= 4) ? round_jobs_history.size() - 4 : 0; break;
                        case 4: start_idx = (round_jobs_history.size() >= 8) ? round_jobs_history.size() - 8 : 0; break;
                        case 5: start_idx = (round_jobs_history.size() >= 16) ? round_jobs_history.size() - 16 : 0; break;
                        case 6: start_idx = 0; break;
                        case 7: {
                            int rounds_to_use = std::ceil(current_round * 0.5);
                            start_idx = (round_jobs_history.size() >= (size_t)rounds_to_use) ? 
                                       round_jobs_history.size() - rounds_to_use : 0;
                            break;
                        }
                        default: start_idx = 0; break;
                    }
                    
                    for (size_t i = start_idx; i < round_jobs_history.size(); i++) {
                        jobs_to_simulate.insert(jobs_to_simulate.end(),
                            round_jobs_history[i].begin(), round_jobs_history[i].end());
                    }
                    
                    // Run simulations with copies
                    std::vector<Job> jobs_srpt_copy = jobs_to_simulate;
                    std::vector<Job> jobs_fcfs_copy = jobs_to_simulate;
                    const double starvation_threshold = std::pow(total_jobs, 2.0/3.0);
                    const BALResult bal_result = Bal(jobs_srpt_copy, starvation_threshold);
                    const FCFSResult fcfs_result = Fcfs(jobs_fcfs_copy);
                    
                    // Validate results
                    if (std::isnan(bal_result.l2_norm_flow_time) || std::isnan(fcfs_result.l2_norm_flow_time)) {
                        std::cerr << "WARNING: NaN detected in simulation at round " << current_round << std::endl;
                        is_bal_better = true;
                    } else {
                        is_bal_better = bal_result.l2_norm_flow_time <= fcfs_result.l2_norm_flow_time;
                    }
                    algorithm_history.push_back(is_bal_better ? "BAL" : "FCFS");
                }
                
                current_round++;
            }
            
            // Move excess jobs to next round
            jobs_in_current_round.erase(
                jobs_in_current_round.begin(),
                jobs_in_current_round.begin() + nJobsPerRound
            );
            n_arrival_jobs -= nJobsPerRound;
        }
        
        // Select next job
        const double starvation_threshold = std::pow(total_jobs, 2.0/3.0);
        Job* selected_job = nullptr;
        if (!active_jobs.empty()) {
            if (is_bal_better) {
                selected_job = bal_select_next_job_optimized(active_jobs, current_time, starvation_threshold);
            } else {
                selected_job = fcfs_select_next_job_optimized(active_jobs);
            }
            
            // BUG FIX: Defensive check for invalid job selection
            if (selected_job && selected_job->remaining_time <= 0) {
                std::cerr << "ERROR: Selected job " << selected_job->job_index 
                          << " has remaining_time=" << selected_job->remaining_time 
                          << " at time=" << current_time << "\n";
                auto it = std::find(active_jobs.begin(), active_jobs.end(), selected_job);
                if (it != active_jobs.end()) {
                    active_jobs.erase(it);
                }
                selected_job = nullptr;
            }
        }
        
        if (selected_job) {
            // Remove job from active_jobs BEFORE execution
            auto it = std::find(active_jobs.begin(), active_jobs.end(), selected_job);
            assert(it != active_jobs.end() && "Selected job must be in active_jobs");
            active_jobs.erase(it);
            
            // BUG FIX: Verify start_time is set correctly
            if (selected_job->start_time == -1) {
                selected_job->start_time = current_time;
                // ASSERTION: Start time must be >= arrival time
                assert(selected_job->start_time >= selected_job->arrival_time && 
                       "Job start time must be after or equal to arrival time");
            }
            
            // Calculate delta - FIXED: Use long long instead of int
            const long long next_arrival_t = (jobs_pointer < total_jobs) ? 
                static_cast<long long>(jobs[jobs_pointer].arrival_time) : LLONG_MAX;
            
            long long delta;  // BUG FIX: Changed from int to long long
            if (is_bal_better) {
                // SRPT: preemptive
                if (next_arrival_t == LLONG_MAX || next_arrival_t > current_time + selected_job->remaining_time) {
                    delta = selected_job->remaining_time;
                } else {
                    delta = next_arrival_t - current_time;
                }
            } else {
                // FCFS: non-preemptive - run to completion
                delta = selected_job->remaining_time;
            }
            
            // Validate delta
            if (delta <= 0 || delta > selected_job->remaining_time) {
                std::cerr << "FATAL ERROR: delta=" << delta << "\n"
                          << "  job_index=" << selected_job->job_index << "\n"
                          << "  remaining_time=" << selected_job->remaining_time << "\n"
                          << "  current_time=" << current_time << "\n"
                          << "  next_arrival=" << next_arrival_t << "\n"
                          << "  is_bal=" << is_bal_better << "\n";
                std::abort();
            }
            
            // Execute
            current_time += delta;
            selected_job->remaining_time -= delta;
            
            assert(selected_job->remaining_time >= 0 && "Remaining time cannot be negative");
            
            if (selected_job->remaining_time == 0) {
                // Job completed
                selected_job->completion_time = current_time;
                // ASSERTION: Completion time must be >= start time
                assert(selected_job->completion_time >= selected_job->start_time &&
                       "Completion time must be after start time");
                // ASSERTION: Completion time must be >= arrival time
                assert(selected_job->completion_time >= selected_job->arrival_time &&
                       "Completion time must be after arrival time");
                completed_jobs.push_back(selected_job);
                n_completed_jobs++;
            } else {
                // Job not finished - re-queue
                active_jobs.push_back(selected_job);
            }
            
        } else {
            // No job to run, jump to next arrival
            if (jobs_pointer < total_jobs) {
                current_time = jobs[jobs_pointer].arrival_time;
            } else {
                assert(active_jobs.empty() && "If no job selected and no arrivals, active_jobs must be empty");
                break;
            }
        }
        
        // Assert progress is being made
        assert((current_time > prev_time || 
                n_completed_jobs > prev_completed || 
                jobs_pointer > prev_jobs_pointer) && 
               "Scheduler must make progress each iteration");
    }
    
    // Process remaining jobs in last round
    if (!jobs_in_current_round.empty() && n_arrival_jobs > 0) {
        round_jobs_history.push_back(std::move(jobs_in_current_round));
        algorithm_history.push_back(is_bal_better ? "BAL" : "FCFS");
    }
    
    // Validate completion
    assert(completed_jobs.size() == (size_t)total_jobs && "All jobs must complete");
    assert(active_jobs.empty() && "Active jobs queue must be empty");
    
    // Calculate metrics
    long double sum_flow = 0.0;
    long double sum_sq = 0.0;
    long long max_flow = 0;
    
    for (const Job* c : completed_jobs) {
        assert(c->completion_time >= 0 && "Completion time must be non-negative");
        assert(c->arrival_time >= 0 && "Arrival time must be non-negative");
        assert(c->completion_time >= c->arrival_time && "Completion must be after arrival");
        
        const long long flow = c->completion_time - c->arrival_time;
        sum_flow += flow;
        sum_sq += static_cast<long double>(flow) * flow;
        max_flow = std::max(max_flow, flow);
    }
    
    const double avg_flow = static_cast<double>(sum_flow / total_jobs);
    const double l2 = std::sqrt(static_cast<double>(sum_sq));
    
    assert(!std::isnan(avg_flow) && !std::isinf(avg_flow) && "avg_flow must be valid");
    assert(!std::isnan(l2) && !std::isinf(l2) && "l2 must be valid");
    
    if (!input_file_name.empty()) {
        save_analysis_results(input_file_name, nJobsPerRound, mode, 
                            algorithm_history, current_round - 1);
    }
    
    return {avg_flow, l2, static_cast<double>(max_flow)};
}

// Optimized parallel processing functions
std::map<int, double> run_all_modes_for_file_normal(std::vector<Job> jobs, int nJobsPerRound,
                                                    const std::string& input_file_path,
                                                    const std::vector<int>& modes_to_run) {
    std::map<int, double> mode_results;
    std::mutex results_mutex;
    std::vector<std::thread> threads;
    threads.reserve(modes_to_run.size());
    
    for (int mode : modes_to_run) {
        threads.emplace_back([&, mode]() {
            std::vector<Job> jobs_copy = jobs;
            const DynamicResult result = DYNAMIC_BAL(jobs_copy, nJobsPerRound, mode, input_file_path);
            
            {
                std::lock_guard<std::mutex> lock(results_mutex);
                mode_results[mode] = result.l2_norm_flow_time;
            }
            
            std::ostringstream oss;
            oss << "    Mode " << mode << ": L2 norm = " << std::fixed 
               << std::setprecision(4) << result.l2_norm_flow_time << '\n';
            safe_cout(oss.str());
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
    
    return mode_results;
}

std::pair<std::map<int, double>, std::map<int, double>> 
run_all_modes_for_file_frequency(std::vector<Job> jobs, int nJobsPerRound,
                                 const std::vector<int>& modes_to_run) {
    std::map<int, double> mode_results;
    std::map<int, double> max_flow_results;
    std::mutex results_mutex;
    std::vector<std::thread> threads;
    threads.reserve(modes_to_run.size());
    
    for (int mode : modes_to_run) {
        threads.emplace_back([&, mode]() {
            std::vector<Job> jobs_copy = jobs;
            const DynamicResult result = DYNAMIC_BAL(jobs_copy, nJobsPerRound, mode, "");
            
            {
                std::lock_guard<std::mutex> lock(results_mutex);
                mode_results[mode] = result.l2_norm_flow_time;
                max_flow_results[mode] = result.max_flow_time;
            }
            
            std::ostringstream oss;
            oss << "    Mode " << mode << ": L2 norm = " << std::fixed 
               << std::setprecision(4) << result.l2_norm_flow_time 
               << ", Max flow = " << result.max_flow_time << '\n';
            safe_cout(oss.str());
        });
    }
    
    for (auto& thread : threads) {
        thread.join();
    }
    
    return std::make_pair(std::move(mode_results), std::move(max_flow_results));
}
void process_avg_folders(const std::string& data_dir, const std::string& output_dir, 
                        int nJobsPerRound, const std::vector<int>& modes_to_run) {
    std::vector<std::string> patterns = {"avg_30_"};
    
    for (const auto& pattern : patterns) {
        auto folders = list_directory(data_dir);
        
        for (const auto& folder : folders) {
            std::string basename = folder.substr(folder.find_last_of('/') + 1);
            if (basename.find(pattern) == std::string::npos || !directory_exists(folder)) {
                continue;
            }
            
            int version = extract_version_from_path(basename);
            std::regex avg_type_pattern("avg_(\\d+)");
            std::smatch match;
            std::string avg_type;
            if (std::regex_search(basename, match, avg_type_pattern)) {
                avg_type = match[1];
            } else {
                continue;
            }
            
            safe_cout("Processing folder: " + basename + " (version=" + std::to_string(version) + ")\n");
            
            std::string avg_result_dir = output_dir + "/avg" + avg_type + "_result";
            create_directory(avg_result_dir);
            
            std::map<int, std::vector<std::map<std::string, std::string>>> results_by_arrival_rate;
            std::mutex results_mutex;
            
            auto csv_files = list_directory(folder);
            std::vector<std::thread> file_threads;
            
            // Process CSV files in parallel
            for (const auto& csv_file : csv_files) {
                if (csv_file.find(".csv") == std::string::npos) continue;
                
                file_threads.emplace_back([&, csv_file]() {
                    std::string filename = csv_file.substr(csv_file.find_last_of('/') + 1);
                    AvgParams params = parse_avg_filename(filename);
                    
                    if (params.arrival_rate < 0) return;
                    
                    safe_cout("  Processing " + filename + "\n");
                    
                    auto jobs = read_jobs_from_csv(csv_file);
                    if (jobs.empty()) return;
                    
                    auto mode_results = run_all_modes_for_file_normal(jobs, nJobsPerRound, csv_file, modes_to_run);
                    
                    std::map<std::string, std::string> result_map;
                    result_map["bp_parameter_L"] = std::to_string(params.bp_L);
                    result_map["bp_parameter_H"] = std::to_string(params.bp_H);
                    for (int mode : modes_to_run) {
                        result_map["mode_" + std::to_string(mode)] = std::to_string(mode_results[mode]);
                    }
                    
                    {
                        std::lock_guard<std::mutex> lock(results_mutex);
                        results_by_arrival_rate[(int)params.arrival_rate].push_back(result_map);
                    }
                });
            }
            
            // Wait for all CSV file processing to finish
            for (auto& thread : file_threads) {
                thread.join();
            }
            
            // Write results
            for (auto& pair : results_by_arrival_rate) {
                std::string output_file = avg_result_dir + "/" + 
                    std::to_string(pair.first) + "_Dynamic_BAL_result_" + 
                    std::to_string(version) + ".csv";
                
                std::ofstream out(output_file);
                out << "arrival_rate,bp_parameter_L,bp_parameter_H";
                for (int mode : modes_to_run) {
                    out << ",Dynamic_BAL_njobs" << nJobsPerRound << "_mode" << mode << "_L2_norm_flow_time";
                }
                out << "\n";
                
                for (const auto& result : pair.second) {
                    out << pair.first << "," << result.at("bp_parameter_L") << ","
                        << result.at("bp_parameter_H");
                    for (int mode : modes_to_run) {
                        out << "," << result.at("mode_" + std::to_string(mode));
                    }
                    out << "\n";
                }
                
                safe_cout("  Saved results to " + output_file + "\n");
            }
        }
    }
}

void process_random_folders(const std::string& data_dir, const std::string& output_dir, 
                           int nJobsPerRound, const std::vector<int>& modes_to_run) {
    std::string random_result_dir = output_dir + "/random_result";
    create_directory(random_result_dir);
    
    std::map<int, std::vector<std::map<std::string, std::string>>> results_by_version;
    std::mutex results_mutex;
    
    auto folders = list_directory(data_dir);
    std::vector<std::thread> folder_threads;
    
    for (const auto& folder : folders) {
        std::string basename = folder.substr(folder.find_last_of('/') + 1);
        if (basename.find("freq_") == std::string::npos || !directory_exists(folder)) {
            continue;
        }
        
        folder_threads.emplace_back([&, folder, basename]() {
            int frequency = parse_freq_from_folder(basename);
            int version = extract_version_from_path(basename);
            
            if (frequency < 0) return;
            
            safe_cout("Processing folder: " + basename + "\n");
            
            auto files = list_directory(folder);
            
            for (const auto& file : files) {
                std::string filename = file.substr(file.find_last_of('/') + 1);
                if (filename.find("random_freq_") == std::string::npos || 
                    filename.find(".csv") == std::string::npos) {
                    continue;
                }
                
                auto jobs = read_jobs_from_csv(file);
                if (jobs.empty()) continue;
                
                std::pair<std::map<int, double>, std::map<int, double>> result_pair = 
                    run_all_modes_for_file_frequency(jobs, nJobsPerRound, modes_to_run);
                std::map<int, double> mode_results = result_pair.first;
                std::map<int, double> max_flow_results = result_pair.second;
                
                std::map<std::string, std::string> result_map;
                result_map["frequency"] = std::to_string(frequency);
                for (int mode : modes_to_run) {
                    result_map["l2_mode_" + std::to_string(mode)] = std::to_string(mode_results[mode]);
                    result_map["max_mode_" + std::to_string(mode)] = std::to_string(max_flow_results[mode]);
                }
                
                {
                    std::lock_guard<std::mutex> lock(results_mutex);
                    results_by_version[version].push_back(result_map);
                }
            }
        });
    }
    
    // Wait for all folder processing to finish
    for (auto& thread : folder_threads) {
        thread.join();
    }
    
    // Write results
    for (auto& pair : results_by_version) {
        std::string output_file = random_result_dir + "/random_result_Dynamic_BAL_njobs" + 
                                 std::to_string(nJobsPerRound) + "_" + 
                                 std::to_string(pair.first) + ".csv";
        
        std::ofstream out(output_file);
        out << "frequency";
        for (int mode : modes_to_run) {
            out << ",Dynamic_BAL_njobs" << nJobsPerRound << "_mode" << mode << "_L2_norm_flow_time";
        }
        for (int mode : modes_to_run) {
            out << ",Dynamic_BAL_njobs" << nJobsPerRound << "_mode" << mode << "_max_flow_time";
        }
        out << "\n";
        
        for (const auto& result : pair.second) {
            out << result.at("frequency");
            for (int mode : modes_to_run) {
                out << "," << result.at("l2_mode_" + std::to_string(mode));
            }
            for (int mode : modes_to_run) {
                out << "," << result.at("max_mode_" + std::to_string(mode));
            }
            out << "\n";
        }
        
        safe_cout("Saved results to " + output_file + "\n");
    }
}

void process_softrandom_folders(const std::string& data_dir, const std::string& output_dir, 
                               int nJobsPerRound, const std::vector<int>& modes_to_run) {
    std::string softrandom_result_dir = output_dir + "/softrandom_result";
    create_directory(softrandom_result_dir);
    
    std::map<int, std::vector<std::map<std::string, std::string>>> results_by_version;
    std::mutex results_mutex;
    
    auto folders = list_directory(data_dir);
    std::vector<std::thread> base_threads;
    
    for (const auto& folder : folders) {
        std::string basename = folder.substr(folder.find_last_of('/') + 1);
        if (basename.find("softrandom_") == std::string::npos || !directory_exists(folder)) {
            continue;
        }
        
        base_threads.emplace_back([&, folder, basename]() {
            int base_version = extract_version_from_path(basename);
            safe_cout("Processing softrandom base: " + basename + "\n");
            
            auto freq_folders = list_directory(folder);
            
            for (const auto& freq_folder : freq_folders) {
                std::string freq_basename = freq_folder.substr(freq_folder.find_last_of('/') + 1);
                if (freq_basename.find("freq_") == std::string::npos || !directory_exists(freq_folder)) {
                    continue;
                }
                
                int frequency = parse_freq_from_folder(freq_basename);
                if (frequency < 0) continue;
                
                auto files = list_directory(freq_folder);
                
                for (const auto& file : files) {
                    std::string filename = file.substr(file.find_last_of('/') + 1);
                    if (filename.find("softrandom_freq_") == std::string::npos || 
                        filename.find(".csv") == std::string::npos) {
                        continue;
                    }
                    
                    auto jobs = read_jobs_from_csv(file);
                    if (jobs.empty()) continue;
                    
                    std::pair<std::map<int, double>, std::map<int, double>> result_pair = 
                        run_all_modes_for_file_frequency(jobs, nJobsPerRound, modes_to_run);
                    std::map<int, double> mode_results = result_pair.first;
                    std::map<int, double> max_flow_results = result_pair.second;
                    
                    std::map<std::string, std::string> result_map;
                    result_map["frequency"] = std::to_string(frequency);
                    for (int mode : modes_to_run) {
                        result_map["l2_mode_" + std::to_string(mode)] = std::to_string(mode_results[mode]);
                        result_map["max_mode_" + std::to_string(mode)] = std::to_string(max_flow_results[mode]);
                    }
                    
                    {
                        std::lock_guard<std::mutex> lock(results_mutex);
                        results_by_version[base_version].push_back(result_map);
                    }
                }
            }
        });
    }
    
    // Wait for all base folder processing to finish
    for (auto& thread : base_threads) {
        thread.join();
    }
    
    // Write results
    for (auto& pair : results_by_version) {
        std::string output_file = softrandom_result_dir + "/softrandom_result_Dynamic_BAL_njobs" + 
                                 std::to_string(nJobsPerRound) + "_" + 
                                 std::to_string(pair.first) + ".csv";
        
        std::ofstream out(output_file);
        out << "frequency";
        for (int mode : modes_to_run) {
            out << ",Dynamic_BAL_njobs" << nJobsPerRound << "_mode" << mode << "_L2_norm_flow_time";
        }
        for (int mode : modes_to_run) {
            out << ",Dynamic_BAL_njobs" << nJobsPerRound << "_mode" << mode << "_max_flow_time";
        }
        out << "\n";
        
        for (const auto& result : pair.second) {
            out << result.at("frequency");
            for (int mode : modes_to_run) {
                out << "," << result.at("l2_mode_" + std::to_string(mode));
            }
            for (int mode : modes_to_run) {
                out << "," << result.at("max_mode_" + std::to_string(mode));
            }
            out << "\n";
        }
        
        safe_cout("Saved results to " + output_file + "\n");
    }
}

// Print usage information
void print_usage(const char* program_name) {
    std::cout << "Usage: " << program_name << " [nJobsPerRound] [mode1,mode2,...]\n\n";
    std::cout << "Arguments:\n";
    std::cout << "  nJobsPerRound  Number of jobs per round (default: 100)\n";
    std::cout << "  modes          Comma-separated list of modes to run (1-7)\n";
    std::cout << "                 Examples: 1,3,5  or  2  or  1,2,3,4,5,6,7\n";
    std::cout << "                 If omitted, runs all modes (1-7)\n\n";
    std::cout << "Examples:\n";
    std::cout << "  " << program_name << "                    # Default: nJobsPerRound=100, all modes\n";
    std::cout << "  " << program_name << " 50                 # nJobsPerRound=50, all modes\n";
    std::cout << "  " << program_name << " 100 1,3,5          # nJobsPerRound=100, modes 1,3,5\n";
    std::cout << "  " << program_name << " 200 2              # nJobsPerRound=200, mode 2 only\n\n";
    std::cout << "Available modes:\n";
    std::cout << "  Mode 1: Last 1 round\n";
    std::cout << "  Mode 2: Last 2 rounds\n";
    std::cout << "  Mode 3: Last 4 rounds\n";
    std::cout << "  Mode 4: Last 8 rounds\n";
    std::cout << "  Mode 5: Last 16 rounds\n";
    std::cout << "  Mode 6: All history\n";
    std::cout << "  Mode 7: Last 50%% of rounds\n";
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
            if (mode >= 1 && mode <= 7) {
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
    std::vector<int> modes_to_run = {1, 2, 3, 4, 5, 6, 7}; // All modes by default
    
    // Parse command-line arguments
    if (argc > 1) {
        if (std::string(argv[1]) == "-h" || std::string(argv[1]) == "--help") {
            print_usage(argv[0]);
            return 0;
        }
        
        // Parse nJobsPerRound
        try {
            nJobsPerRound = std::atoi(argv[1]);
            if (nJobsPerRound <= 0) {
                std::cerr << "ERROR: nJobsPerRound must be positive\n";
                print_usage(argv[0]);
                return 1;
            }
        } catch (const std::exception& e) {
            std::cerr << "ERROR: Invalid nJobsPerRound value\n";
            print_usage(argv[0]);
            return 1;
        }
    }
    
    if (argc > 2) {
        // Parse modes
        modes_to_run = parse_modes(argv[2]);
        if (modes_to_run.empty()) {
            std::cerr << "ERROR: No valid modes specified\n";
            print_usage(argv[0]);
            return 1;
        }
    }
    
    std::string data_dir = "/home/melowu/Work/ultimus/data";
    std::string output_dir = "/home/melowu/Work/ultimus/Dynamic_BAL_result";
    
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
    
    // Launch three main processing functions in parallel
    std::vector<std::thread> main_threads;
    
    std::cout << "\nLaunching parallel processing threads...\n\n";
    
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 1] Processing avg files...\n");
        safe_cout("========================================\n");
        process_avg_folders(data_dir, output_dir, nJobsPerRound, modes_to_run);
        safe_cout("\n[Thread 1] ✓ Avg files completed!\n\n");
    });
    
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 2] Processing random files...\n");
        safe_cout("========================================\n");
        process_random_folders(data_dir, output_dir, nJobsPerRound, modes_to_run);
        safe_cout("\n[Thread 2] ✓ Random files completed!\n\n");
    });
    
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 3] Processing softrandom files...\n");
        safe_cout("========================================\n");
        process_softrandom_folders(data_dir, output_dir, nJobsPerRound, modes_to_run);
        safe_cout("\n[Thread 3] ✓ Softrandom files completed!\n\n");
    });
    
    // Wait for all three main threads to complete
    for (auto& thread : main_threads) {
        thread.join();
    }
    
    std::cout << "\n============================================================\n";
    std::cout << "All Dynamic processing completed successfully!\n";
    std::cout << "============================================================\n";
    
    return 0;
}