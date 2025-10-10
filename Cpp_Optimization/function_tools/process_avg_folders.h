#ifndef PROCESS_AVG_FOLDERS_H
#define PROCESS_AVG_FOLDERS_H

#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include <regex>
#include <thread>
#include <mutex>
#include "utils.h"
#include "_run.h"

// Parse new filename format: (arrival_rate, bp_L_bp_H).csv
struct NewAvgParams {
    double arrival_rate;
    double bp_L;
    int bp_H;
    
    NewAvgParams() : arrival_rate(-1), bp_L(-1), bp_H(-1) {}
};

inline NewAvgParams parse_new_avg_filename(const std::string& filename) {
    NewAvgParams params;
    
    // Pattern: (20, 4.639_32768).csv or (20, Normal_250_100).csv
    std::regex pattern(R"(\((\d+(?:\.\d+)?),\s*([^)]+)\)\.csv)");
    std::smatch match;
    
    if (std::regex_search(filename, match, pattern)) {
        params.arrival_rate = std::stod(match[1]);
        std::string second_part = match[2];
        
        // Check if it's Normal format or numeric format
        if (second_part.find("Normal") != std::string::npos) {
            // Format: Normal_250_100
            std::regex normal_pattern(R"(Normal_(\d+)_(\d+))");
            std::smatch normal_match;
            if (std::regex_search(second_part, normal_match, normal_pattern)) {
                params.bp_L = std::stod(normal_match[1]);
                params.bp_H = std::stoi(normal_match[2]);
            }
        } else {
            // Format: 4.639_32768
            std::regex numeric_pattern(R"((\d+(?:\.\d+)?)_(\d+))");
            std::smatch numeric_match;
            if (std::regex_search(second_part, numeric_match, numeric_pattern)) {
                params.bp_L = std::stod(numeric_match[1]);
                params.bp_H = std::stoi(numeric_match[2]);
            }
        }
    }
    
    return params;
}

// Original function for single algorithm
template<typename AlgoFunc>
void process_avg_folders(AlgoFunc algo, const std::string& algo_name, 
                        const std::string& data_dir, const std::string& output_dir) {
    std::vector<std::string> patterns = {"avg_30_", "avg_60_", "avg_90_"};
    
    for (const auto& pattern : patterns) {
        auto folders = list_directory(data_dir);
        
        for (const auto& folder : folders) {
            std::string basename = folder.substr(folder.find_last_of('/') + 1);
            if (basename.find(pattern) == std::string::npos || 
                !directory_exists(folder)) {
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
            
            std::cout << "Processing folder: " << basename << " (version=" 
                     << version << ")" << std::endl;
            
            std::string avg_result_dir = output_dir + "/avg" + avg_type + "_result";
            create_directory(avg_result_dir);
            
            std::map<int, std::vector<std::map<std::string, std::string>>> results_by_arrival_rate;
            
            auto csv_files = list_directory(folder);
            
            for (const auto& csv_file : csv_files) {
                if (csv_file.find(".csv") == std::string::npos) continue;
                
                std::string filename = csv_file.substr(csv_file.find_last_of('/') + 1);
                
                // Try new format first
                NewAvgParams params = parse_new_avg_filename(filename);
                
                // Fallback to old format if new format fails
                if (params.arrival_rate < 0) {
                    AvgParams old_params = parse_avg_filename(filename);
                    if (old_params.arrival_rate < 0) {
                        std::cerr << "Warning: Could not parse filename: " << filename << std::endl;
                        continue;
                    }
                    params.arrival_rate = old_params.arrival_rate;
                    params.bp_L = old_params.bp_L;
                    params.bp_H = old_params.bp_H;
                }
                
                std::cout << "  Processing " << filename << ": arrival_rate=" 
                         << params.arrival_rate << ", bp_L=" << params.bp_L 
                         << ", bp_H=" << params.bp_H << std::endl;
                
                auto jobs = read_jobs_from_csv(csv_file);
                if (jobs.empty()) continue;
                
                // Run algorithm
                double result = run(algo, jobs);
                
                std::map<std::string, std::string> result_map;
                result_map["bp_parameter_L"] = std::to_string(params.bp_L);
                result_map["bp_parameter_H"] = std::to_string(params.bp_H);
                result_map["results"] = std::to_string(result);
                
                results_by_arrival_rate[(int)params.arrival_rate].push_back(result_map);
            }
            
            // Write results grouped by arrival_rate with version number
            for (auto& pair : results_by_arrival_rate) {
                std::string output_file;
                if (version >= 0) {
                    output_file = avg_result_dir + "/" + 
                        std::to_string(pair.first) + "_" + algo_name + "_" + 
                        std::to_string(version) + "_result.csv";
                } else {
                    output_file = avg_result_dir + "/" + 
                        std::to_string(pair.first) + "_" + algo_name + "_result.csv";
                }
                
                std::ofstream out(output_file);
                out << "arrival_rate,bp_parameter_L,bp_parameter_H," 
                    << algo_name << "_L2_norm_flow_time\n";
                
                // Sort results by bp_L and bp_H for consistency
                std::sort(pair.second.begin(), pair.second.end(), 
                    [](const auto& a, const auto& b) {
                        double a_L = std::stod(a.at("bp_parameter_L"));
                        double b_L = std::stod(b.at("bp_parameter_L"));
                        int a_H = std::stoi(a.at("bp_parameter_H"));
                        int b_H = std::stoi(b.at("bp_parameter_H"));
                        if (a_L != b_L) return a_L < b_L;
                        return a_H < b_H;
                    });
                
                for (const auto& result : pair.second) {
                    out << pair.first << "," << result.at("bp_parameter_L") << ","
                        << result.at("bp_parameter_H") << "," 
                        << result.at("results") << "\n";
                }
                
                std::cout << "  Saved results for arrival_rate=" << pair.first 
                         << " to " << output_file << std::endl;
            }
        }
    }
}

// Extended function for Dynamic algorithm (multi-mode)
template<typename MultiModeFunc>
void process_avg_folders_multimode(MultiModeFunc multi_mode_algo,
                                   const std::string& data_dir, 
                                   const std::string& output_dir,
                                   int nJobsPerRound,
                                   const std::vector<int>& modes_to_run,
                                   std::mutex& cout_mutex) {
    std::vector<std::string> patterns = {"avg_30_", "avg_60_", "avg_90_"};
    
    auto safe_cout = [&](const std::string& msg) {
        std::lock_guard<std::mutex> lock(cout_mutex);
        std::cout << msg << std::flush;
    };
    
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
                    
                    // Try new format first
                    NewAvgParams params = parse_new_avg_filename(filename);
                    
                    // Fallback to old format if new format fails
                    if (params.arrival_rate < 0) {
                        AvgParams old_params = parse_avg_filename(filename);
                        if (old_params.arrival_rate < 0) return;
                        params.arrival_rate = old_params.arrival_rate;
                        params.bp_L = old_params.bp_L;
                        params.bp_H = old_params.bp_H;
                    }
                    
                    safe_cout("  Processing " + filename + "\n");
                    
                    auto jobs = read_jobs_from_csv(csv_file);
                    if (jobs.empty()) return;
                    
                    // Run multi-mode algorithm - expects function that returns map<int, double>
                    auto mode_results = multi_mode_algo(jobs, nJobsPerRound, csv_file, modes_to_run);
                    
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
                    std::to_string(pair.first) + "_Dynamic_result_" + 
                    std::to_string(version) + ".csv";
                
                std::ofstream out(output_file);
                out << "arrival_rate,bp_parameter_L,bp_parameter_H";
                for (int mode : modes_to_run) {
                    out << ",Dynamic_njobs" << nJobsPerRound << "_mode" << mode << "_L2_norm_flow_time";
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
// Extended function for Dynamic_BAL algorithm (multi-mode)
template<typename MultiModeFunc>
void process_avg_folders_multimode_DBAL(MultiModeFunc multi_mode_algo,
                                   const std::string& data_dir, 
                                   const std::string& output_dir,
                                   int nJobsPerRound,
                                   const std::vector<int>& modes_to_run,
                                   std::mutex& cout_mutex) {
    std::vector<std::string> patterns = {"avg_30_", "avg_60_", "avg_90_"};
    
    auto safe_cout = [&](const std::string& msg) {
        std::lock_guard<std::mutex> lock(cout_mutex);
        std::cout << msg << std::flush;
    };
    
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
                    
                    // Try new format first
                    NewAvgParams params = parse_new_avg_filename(filename);
                    
                    // Fallback to old format if new format fails
                    if (params.arrival_rate < 0) {
                        AvgParams old_params = parse_avg_filename(filename);
                        if (old_params.arrival_rate < 0) return;
                        params.arrival_rate = old_params.arrival_rate;
                        params.bp_L = old_params.bp_L;
                        params.bp_H = old_params.bp_H;
                    }
                    
                    safe_cout("  Processing " + filename + "\n");
                    
                    auto jobs = read_jobs_from_csv(csv_file);
                    if (jobs.empty()) return;
                    
                    // Run multi-mode algorithm - expects function that returns map<int, double>
                    auto mode_results = multi_mode_algo(jobs, nJobsPerRound, csv_file, modes_to_run);
                    
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
#endif // PROCESS_AVG_FOLDERS_H