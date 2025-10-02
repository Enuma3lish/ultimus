#ifndef PROCESS_AVG_FOLDERS_H
#define PROCESS_AVG_FOLDERS_H

#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include <regex>
#include "utils.h"
#include "_run.h"

template<typename AlgoFunc>
void process_avg_folders(AlgoFunc algo, const std::string& algo_name, 
                        const std::string& data_dir, const std::string& output_dir) {
    std::vector<std::string> patterns = {"avg_30_"};
    
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
                AvgParams params = parse_avg_filename(filename);
                
                if (params.arrival_rate < 0) {
                    std::cerr << "Warning: Could not parse filename: " << filename << std::endl;
                    continue;
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

#endif // PROCESS_AVG_FOLDERS_H