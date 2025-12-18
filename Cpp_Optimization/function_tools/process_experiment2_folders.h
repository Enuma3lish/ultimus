#ifndef PROCESS_EXPERIMENT2_FOLDERS_H
#define PROCESS_EXPERIMENT2_FOLDERS_H

#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include <regex>
#include "utils.h"
#include "_run_random.h"

/**
 * Experiment 2: Fixed job size, vary coherence_time
 *
 * This experiment tests the effect of coherence_time when job size parameters are fixed.
 * Only inter-arrival time changes, job size distribution remains constant.
 */

// Helper to parse param folder name
inline std::pair<double, int> parse_param_folder(const std::string& folder_name) {
    // Extract L and H from folder name like "param_L16.772_H64"
    std::regex pattern("param_L([0-9.]+)_H(\\d+)");
    std::smatch match;
    if (std::regex_search(folder_name, match, pattern)) {
        return {std::stod(match[1]), std::stoi(match[2])};
    }
    return {-1.0, -1};
}

template<typename AlgoFunc>
void process_experiment2_folders(AlgoFunc algo, const std::string& algo_name,
                                 const std::string& data_dir, const std::string& output_dir) {
    std::string exp2_result_dir = output_dir + "/experiment2_fixed_jobsize_result";
    create_directory(exp2_result_dir);

    // Structure: version -> param_folder -> results
    std::map<int, std::map<std::string, std::vector<std::map<std::string, std::string>>>> results_by_version_and_param;

    auto folders = list_directory(data_dir);

    for (const auto& folder : folders) {
        std::string basename = folder.substr(folder.find_last_of('/') + 1);
        if (basename.find("experiment2_fixed_jobsize_") == std::string::npos ||
            !directory_exists(folder)) {
            continue;
        }

        int base_version = extract_version_from_path(basename);
        std::cout << "Processing experiment2_fixed_jobsize base: " << basename
                 << " (version=" << base_version << ")" << std::endl;

        // Get parameter folders
        auto param_folders = list_directory(folder);

        for (const auto& param_folder : param_folders) {
            std::string param_basename = param_folder.substr(param_folder.find_last_of('/') + 1);
            if (param_basename.find("param_L") == std::string::npos ||
                !directory_exists(param_folder)) {
                continue;
            }

            auto [param_L, param_H] = parse_param_folder(param_basename);
            std::cout << "  Processing parameter folder: " << param_basename
                     << " (L=" << param_L << ", H=" << param_H << ")" << std::endl;

            // Get frequency folders
            auto freq_folders = list_directory(param_folder);

            for (const auto& freq_folder : freq_folders) {
                std::string freq_basename = freq_folder.substr(freq_folder.find_last_of('/') + 1);
                if (freq_basename.find("freq_") == std::string::npos ||
                    !directory_exists(freq_folder)) {
                    continue;
                }

                int frequency = parse_freq_from_folder(freq_basename);
                if (frequency < 0) continue;

                std::cout << "    Processing subfolder: " << freq_basename
                         << " (coherence_time=" << frequency << ")" << std::endl;

                auto files = list_directory(freq_folder);

                for (const auto& file : files) {
                    std::string filename = file.substr(file.find_last_of('/') + 1);
                    if (filename.find("exp2_fixed_jobsize_") == std::string::npos ||
                        filename.find(".csv") == std::string::npos) {
                        continue;
                    }

                    std::cout << "      Processing " << filename << std::endl;

                    auto jobs = read_jobs_from_csv(file);
                    if (jobs.empty()) continue;

                    try {
                        auto [l2_results, max_flow_results] = run_random(algo, jobs);
                        std::cout << "      Results: L2=" << l2_results
                                 << ", Max Flow=" << max_flow_results << std::endl;

                        std::map<std::string, std::string> result_map;
                        result_map["coherence_time"] = std::to_string(frequency);
                        result_map["param_L"] = std::to_string(param_L);
                        result_map["param_H"] = std::to_string(param_H);
                        result_map["l2_results"] = std::to_string(l2_results);
                        result_map["max_flow_results"] = std::to_string(max_flow_results);

                        results_by_version_and_param[base_version][param_basename].push_back(result_map);
                    } catch (const std::exception& e) {
                        std::cerr << "Error processing " << file << ": " << e.what() << std::endl;
                        continue;
                    }
                }
            }
        }
    }

    // Write results grouped by version and parameter
    for (auto& version_pair : results_by_version_and_param) {
        int version = version_pair.first;

        for (auto& param_pair : version_pair.second) {
            if (param_pair.second.empty()) continue;

            std::string param_name = param_pair.first;
            std::string output_file;

            if (version >= 0) {
                output_file = exp2_result_dir + "/experiment2_" + param_name + "_result_" +
                             algo_name + "_" + std::to_string(version) + ".csv";
            } else {
                output_file = exp2_result_dir + "/experiment2_" + param_name + "_result_" +
                             algo_name + ".csv";
            }

            std::cout << "Writing " << param_pair.second.size() << " results to "
                     << output_file << std::endl;

            std::ofstream out(output_file);
            out << "coherence_time,param_L,param_H,"
                << algo_name << "_L2_norm_flow_time,"
                << algo_name << "_max_flow_time\n";

            for (const auto& result : param_pair.second) {
                out << result.at("coherence_time") << ","
                    << result.at("param_L") << ","
                    << result.at("param_H") << ","
                    << result.at("l2_results") << ","
                    << result.at("max_flow_results") << "\n";
            }

            out.close();
            std::cout << "Successfully wrote " << output_file << std::endl;
        }
    }

    std::cout << "\nExperiment 2 processing complete!" << std::endl;
}

#endif // PROCESS_EXPERIMENT2_FOLDERS_H
