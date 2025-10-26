#ifndef PROCESS_RANDOM_FOLDERS_H
#define PROCESS_RANDOM_FOLDERS_H

#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include <thread>
#include <mutex>
#include "utils.h"
#include "_run_random.h"

// Original function for single algorithm
template<typename AlgoFunc>
void process_random_folders(AlgoFunc algo, const std::string& algo_name,
                           const std::string& data_dir, const std::string& output_dir) {
    std::string random_result_dir = output_dir + "/random_result";
    create_directory(random_result_dir);
    
    std::map<int, std::vector<std::map<std::string, std::string>>> results_by_version;
    
    auto folders = list_directory(data_dir);
    
    for (const auto& folder : folders) {
        std::string basename = folder.substr(folder.find_last_of('/') + 1);
        if (basename.find("freq_") == std::string::npos || 
            !directory_exists(folder)) {
            continue;
        }
        
        int frequency = parse_freq_from_folder(basename);
        int version = extract_version_from_path(basename);
        
        if (frequency < 0) {
            std::cerr << "Warning: Could not parse frequency from folder: " 
                     << basename << std::endl;
            continue;
        }
        
        std::cout << "Processing folder: " << basename << " (freq=" 
                 << frequency << ", version=" << version << ")" << std::endl;
        
        auto files = list_directory(folder);
        
        for (const auto& file : files) {
            std::string filename = file.substr(file.find_last_of('/') + 1);
            if (filename.find("random_freq_") == std::string::npos || 
                filename.find(".csv") == std::string::npos) {
                continue;
            }
            
            std::cout << "  Processing " << filename << std::endl;
            
            auto jobs = read_jobs_from_csv(file);
            if (jobs.empty()) {
                std::cerr << "Warning: Failed to read jobs from " << file << std::endl;
                continue;
            }
            
            try {
                auto [l2_results, max_flow_results] = run_random(algo, jobs);
                std::cout << "  Results: L2=" << l2_results 
                         << ", Max Flow=" << max_flow_results << std::endl;
                
                std::map<std::string, std::string> result_map;
                result_map["frequency"] = std::to_string(frequency);
                result_map["l2_results"] = std::to_string(l2_results);
                result_map["max_flow_results"] = std::to_string(max_flow_results);
                
                results_by_version[version].push_back(result_map);
            } catch (const std::exception& e) {
                std::cerr << "Error processing " << file << ": " << e.what() << std::endl;
                continue;
            }
        }
    }
    
    // Write results grouped by version
    for (auto& pair : results_by_version) {
        if (pair.second.empty()) continue;
        
        std::string output_file;
        if (pair.first >= 0) {
            output_file = random_result_dir + "/random_result_" + 
                         algo_name + "_" + std::to_string(pair.first) + ".csv";
        } else {
            output_file = random_result_dir + "/random_result_" + algo_name + ".csv";
        }
        
        std::cout << "Writing " << pair.second.size() << " results to " 
                 << output_file << std::endl;
        
        std::ofstream out(output_file);
        out << "frequency," << algo_name << "_L2_norm_flow_time," 
            << algo_name << "_maximum_flow_time\n";
        
        // Sort by frequency
        std::sort(pair.second.begin(), pair.second.end(),
            [](const auto& a, const auto& b) {
                return std::stoi(a.at("frequency")) < std::stoi(b.at("frequency"));
            });
        
        for (const auto& result : pair.second) {
            out << result.at("frequency") << "," 
                << result.at("l2_results") << "," 
                << result.at("max_flow_results") << "\n";
        }
        
        std::cout << "Successfully saved random results (version " 
                 << pair.first << ") to " << output_file << std::endl;
    }
}

// Extended function for Dynamic algorithm (multi-mode)
template<typename MultiModeFunc>
void process_random_folders_multimode(MultiModeFunc multi_mode_algo,
                                     const std::string& data_dir, 
                                     const std::string& output_dir,
                                     int nJobsPerRound,
                                     const std::vector<int>& modes_to_run,
                                     std::mutex& cout_mutex) {
    std::string random_result_dir = output_dir + "/random_result";
    create_directory(random_result_dir);
    
    auto safe_cout = [&](const std::string& msg) {
        std::lock_guard<std::mutex> lock(cout_mutex);
        std::cout << msg << std::flush;
    };
    
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
                
                // Run multi-mode algorithm - expects function that returns pair<map<int,double>, map<int,double>>
                auto result_pair = multi_mode_algo(jobs, nJobsPerRound, modes_to_run);
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
        std::string output_file = random_result_dir + "/random_result_Dynamic_njobs" + 
                                 std::to_string(nJobsPerRound) + "_" + 
                                 std::to_string(pair.first) + ".csv";
        
        std::ofstream out(output_file);
        out << "frequency";
        for (int mode : modes_to_run) {
            out << ",Dynamic_njobs" << nJobsPerRound << "_mode" << mode << "_L2_norm_flow_time";
        }
        for (int mode : modes_to_run) {
            out << ",Dynamic_njobs" << nJobsPerRound << "_mode" << mode << "_maximum_flow_time";
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
// Extended function for Dynamic_BAL algorithm (multi-mode)
template<typename MultiModeFunc>
void process_random_folders_multimode_DBAL(MultiModeFunc multi_mode_algo,
                                     const std::string& data_dir, 
                                     const std::string& output_dir,
                                     int nJobsPerRound,
                                     const std::vector<int>& modes_to_run,
                                     std::mutex& cout_mutex) {
    std::string random_result_dir = output_dir + "/random_result";
    create_directory(random_result_dir);
    
    auto safe_cout = [&](const std::string& msg) {
        std::lock_guard<std::mutex> lock(cout_mutex);
        std::cout << msg << std::flush;
    };
    
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
                
                // Run multi-mode algorithm - expects function that returns pair<map<int,double>, map<int,double>>
                auto result_pair = multi_mode_algo(jobs, nJobsPerRound, modes_to_run);
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
            out << ",Dynamic_BAL_njobs" << nJobsPerRound << "_mode" << mode << "_maximum_flow_time";
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
// Extended function for Dynamic algorithm (multi-mode)
template<typename MultiModeFunc>
void process_random_folders_multimode_RF(MultiModeFunc multi_mode_algo,
                                     const std::string& data_dir, 
                                     const std::string& output_dir,
                                     int nJobsPerRound,
                                     const std::vector<int>& modes_to_run,
                                     std::mutex& cout_mutex) {
    std::string random_result_dir = output_dir + "/random_result";
    create_directory(random_result_dir);
    
    auto safe_cout = [&](const std::string& msg) {
        std::lock_guard<std::mutex> lock(cout_mutex);
        std::cout << msg << std::flush;
    };
    
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
                
                // Run multi-mode algorithm - expects function that returns pair<map<int,double>, map<int,double>>
                auto result_pair = multi_mode_algo(jobs, nJobsPerRound, modes_to_run);
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
        std::string output_file = random_result_dir + "/random_result_RFDynamic_njobs" + 
                                 std::to_string(nJobsPerRound) + "_" + 
                                 std::to_string(pair.first) + ".csv";
        
        std::ofstream out(output_file);
        out << "frequency";
        for (int mode : modes_to_run) {
            out << ",RFDynamic_njobs" << nJobsPerRound << "_mode" << mode << "_L2_norm_flow_time";
        }
        for (int mode : modes_to_run) {
            out << ",RFDynamic_njobs" << nJobsPerRound << "_mode" << mode << "_maximum_flow_time";
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

#endif // PROCESS_RANDOM_FOLDERS_H