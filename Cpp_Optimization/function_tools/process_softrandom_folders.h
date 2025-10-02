#ifndef PROCESS_SOFTRANDOM_FOLDERS_H
#define PROCESS_SOFTRANDOM_FOLDERS_H

#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include "utils.h"
#include "_run_random.h"

template<typename AlgoFunc>
void process_softrandom_folders(AlgoFunc algo, const std::string& algo_name,
                               const std::string& data_dir, const std::string& output_dir) {
    std::string softrandom_result_dir = output_dir + "/softrandom_result";
    create_directory(softrandom_result_dir);
    
    std::map<int, std::vector<std::map<std::string, std::string>>> results_by_version;
    
    auto folders = list_directory(data_dir);
    
    for (const auto& folder : folders) {
        std::string basename = folder.substr(folder.find_last_of('/') + 1);
        if (basename.find("softrandom_") == std::string::npos || 
            !directory_exists(folder)) {
            continue;
        }
        
        int base_version = extract_version_from_path(basename);
        std::cout << "Processing softrandom base: " << basename 
                 << " (version=" << base_version << ")" << std::endl;
        
        auto freq_folders = list_directory(folder);
        
        for (const auto& freq_folder : freq_folders) {
            std::string freq_basename = freq_folder.substr(freq_folder.find_last_of('/') + 1);
            if (freq_basename.find("freq_") == std::string::npos || 
                !directory_exists(freq_folder)) {
                continue;
            }
            
            int frequency = parse_freq_from_folder(freq_basename);
            if (frequency < 0) {
                std::cerr << "Warning: Could not parse frequency from folder: " 
                         << freq_basename << std::endl;
                continue;
            }
            
            std::cout << "  Processing subfolder: " << freq_basename 
                     << " (freq=" << frequency << ")" << std::endl;
            
            auto files = list_directory(freq_folder);
            
            for (const auto& file : files) {
                std::string filename = file.substr(file.find_last_of('/') + 1);
                if (filename.find("softrandom_freq_") == std::string::npos || 
                    filename.find(".csv") == std::string::npos) {
                    continue;
                }
                
                std::cout << "    Processing " << filename << std::endl;
                
                auto jobs = read_jobs_from_csv(file);
                if (jobs.empty()) continue;
                
                try {
                    auto [l2_results, max_flow_results] = run_random(algo, jobs);
                    std::cout << "    Results: L2=" << l2_results 
                             << ", Max Flow=" << max_flow_results << std::endl;
                    
                    std::map<std::string, std::string> result_map;
                    result_map["frequency"] = std::to_string(frequency);
                    result_map["l2_results"] = std::to_string(l2_results);
                    result_map["max_flow_results"] = std::to_string(max_flow_results);
                    
                    results_by_version[base_version].push_back(result_map);
                } catch (const std::exception& e) {
                    std::cerr << "Error processing " << file << ": " << e.what() << std::endl;
                    continue;
                }
            }
        }
    }
    
    // Write results grouped by version
    for (auto& pair : results_by_version) {
        if (pair.second.empty()) continue;
        
        std::string output_file;
        if (pair.first >= 0) {
            output_file = softrandom_result_dir + "/softrandom_result_" + 
                         algo_name + "_" + std::to_string(pair.first) + ".csv";
        } else {
            output_file = softrandom_result_dir + "/softrandom_result_" + 
                         algo_name + ".csv";
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
        
        std::cout << "  Saved softrandom results (version " 
                 << pair.first << ") to " << output_file << std::endl;
    }
}

#endif // PROCESS_SOFTRANDOM_FOLDERS_H