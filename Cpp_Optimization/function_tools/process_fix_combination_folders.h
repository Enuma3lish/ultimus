#ifndef PROCESS_FIX_COMBINATION_FOLDERS_H
#define PROCESS_FIX_COMBINATION_FOLDERS_H

#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include "utils.h"
#include "_run_random.h"

// Function for fixed arrival combination folders (fix20_combination, fix30_combination, fix40_combination)
// Similar to process_bounded_pareto_combination_random_folders but with fixed arrival rates
template<typename AlgoFunc>
void process_fix_combination_folders(AlgoFunc algo, const std::string& algo_name,
                                     const std::string& data_dir, const std::string& output_dir) {

    // Fixed arrival types
    std::vector<std::string> fix_types = {"fix20", "fix30", "fix40"};

    for (const auto& fix_type : fix_types) {
        std::string combination_result_dir = output_dir + "/" + fix_type + "_combination_result";
        create_directory(combination_result_dir);

        std::cout << "\n========================================" << std::endl;
        std::cout << "Processing " << fix_type << " combination folders..." << std::endl;
        std::cout << "========================================" << std::endl;

        auto folders = list_directory(data_dir);

        for (const auto& folder : folders) {
            std::string basename = folder.substr(folder.find_last_of('/') + 1);

            // Look for fix20_combination_*, fix30_combination_*, or fix40_combination_* folders
            std::string search_pattern = fix_type + "_combination_";
            if (basename.find(search_pattern) != 0 || !directory_exists(folder)) {
                continue;
            }

            int base_version = extract_version_from_path(basename);
            std::cout << "Processing " << basename << " (version=" << base_version << ")" << std::endl;

            // Process two_combination_*, three_combination_*, four_combination_* subfolders
            std::map<std::string, std::string> result_folder_mapping = {
                {"two_combination", "two_result_" + fix_type},
                {"three_combination", "three_result_" + fix_type},
                {"four_combination", "four_result_" + fix_type}
            };

            auto comb_subfolders = list_directory(folder);

            for (const auto& comb_folder : comb_subfolders) {
                std::string comb_basename = comb_folder.substr(comb_folder.find_last_of('/') + 1);
                if (!directory_exists(comb_folder)) continue;

                // Parse combination type (e.g., "two_combination" from "two_combination_H64_H512")
                std::string comb_type = parse_combination_type_from_folder(comb_basename);
                if (comb_type.empty() || result_folder_mapping.find(comb_type) == result_folder_mapping.end()) {
                    continue;
                }

                std::cout << "  Processing " << comb_basename << " (type: " << comb_type << ")" << std::endl;

                std::string result_folder_name = result_folder_mapping[comb_type];
                std::string result_dir = combination_result_dir + "/" + result_folder_name;
                create_directory(result_dir);

                std::map<std::string, std::vector<std::map<std::string, std::string>>> results_by_pair;

                auto freq_folders = list_directory(comb_folder);

                for (const auto& freq_folder : freq_folders) {
                    std::string freq_basename = freq_folder.substr(freq_folder.find_last_of('/') + 1);
                    if (freq_basename.find("freq_") == std::string::npos ||
                        !directory_exists(freq_folder)) {
                        continue;
                    }

                    int frequency = parse_freq_from_folder(freq_basename);
                    if (frequency < 0) continue;

                    std::cout << "    Processing subfolder: " << freq_basename
                             << " (freq=" << frequency << ")" << std::endl;

                    auto files = list_directory(freq_folder);

                    for (const auto& file : files) {
                        std::string filename = file.substr(file.find_last_of('/') + 1);
                        if (filename.find(".csv") == std::string::npos) {
                            continue;
                        }

                        // Extract pair/triplet/quadruplet identifier (e.g., "pair_1", "triplet_2", "quadruplet_1")
                        std::string pair_id;
                        if (filename.find("pair_") != std::string::npos) {
                            size_t start = filename.find("pair_");
                            size_t end = filename.find("_freq_");
                            if (end != std::string::npos) {
                                pair_id = filename.substr(start, end - start);
                            }
                        } else if (filename.find("triplet_") != std::string::npos) {
                            size_t start = filename.find("triplet_");
                            size_t end = filename.find("_freq_");
                            if (end != std::string::npos) {
                                pair_id = filename.substr(start, end - start);
                            }
                        } else if (filename.find("quadruplet_") != std::string::npos) {
                            size_t start = filename.find("quadruplet_");
                            size_t end = filename.find("_freq_");
                            if (end != std::string::npos) {
                                pair_id = filename.substr(start, end - start);
                            }
                        }

                        if (pair_id.empty()) continue;

                        std::cout << "      Processing " << filename << " (" << pair_id << ")" << std::endl;

                        auto jobs = read_jobs_from_csv(file);
                        if (jobs.empty()) continue;

                        try {
                            auto [l2_results, max_flow_results] = run_random(algo, jobs);
                            std::cout << "      Results: L2=" << l2_results
                                     << ", Max Flow=" << max_flow_results << std::endl;

                            std::map<std::string, std::string> result_map;
                            result_map["frequency"] = std::to_string(frequency);
                            result_map["l2_results"] = std::to_string(l2_results);
                            result_map["max_flow_results"] = std::to_string(max_flow_results);

                            results_by_pair[pair_id].push_back(result_map);
                        } catch (const std::exception& e) {
                            std::cerr << "Error processing " << file << ": " << e.what() << std::endl;
                            continue;
                        }
                    }
                }

                // Write results for each pair/triplet/quadruplet
                for (auto& pair : results_by_pair) {
                    if (pair.second.empty()) continue;

                    std::string output_file;
                    if (base_version >= 0) {
                        output_file = result_dir + "/" + pair.first + "_" + fix_type + "_" + algo_name + "_" +
                                     std::to_string(base_version) + "_result.csv";
                    } else {
                        output_file = result_dir + "/" + pair.first + "_" + fix_type + "_" + algo_name + "_result.csv";
                    }

                    std::cout << "    Writing " << pair.second.size() << " results to "
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

                    out.close();
                }
            }
        }

        std::cout << "========================================" << std::endl;
        std::cout << "Completed processing " << fix_type << " combination" << std::endl;
        std::cout << "========================================\n" << std::endl;
    }
}

// Multimode version for Dynamic algorithms (Dynamic, Dynamic_BAL, RFDynamic)
// Similar to process_fix_combination_folders but runs all modes and outputs mode-specific columns
template<typename MultiModeFunc>
void process_fix_combination_folders_multimode(MultiModeFunc multi_mode_algo,
                                               const std::string& algo_name,
                                               const std::string& data_dir,
                                               const std::string& output_dir,
                                               int nJobsPerRound,
                                               const std::vector<int>& modes_to_run,
                                               std::mutex& cout_mutex) {

    auto safe_cout = [&](const std::string& msg) {
        std::lock_guard<std::mutex> lock(cout_mutex);
        std::cout << msg << std::flush;
    };

    // Fixed arrival types
    std::vector<std::string> fix_types = {"fix20", "fix30", "fix40"};

    for (const auto& fix_type : fix_types) {
        std::string combination_result_dir = output_dir + "/" + fix_type + "_combination_result";
        create_directory(combination_result_dir);

        safe_cout("\n========================================\n");
        safe_cout("Processing " + fix_type + " combination folders (multimode)...\n");
        safe_cout("========================================\n");

        auto folders = list_directory(data_dir);

        for (const auto& folder : folders) {
            std::string basename = folder.substr(folder.find_last_of('/') + 1);

            // Look for fix20_combination_*, fix30_combination_*, or fix40_combination_* folders
            std::string search_pattern = fix_type + "_combination_";
            if (basename.find(search_pattern) != 0 || !directory_exists(folder)) {
                continue;
            }

            int base_version = extract_version_from_path(basename);
            safe_cout("Processing " + basename + " (version=" + std::to_string(base_version) + ")\n");

            // Process two_combination_*, three_combination_*, four_combination_* subfolders
            std::map<std::string, std::string> result_folder_mapping = {
                {"two_combination", "two_result_" + fix_type},
                {"three_combination", "three_result_" + fix_type},
                {"four_combination", "four_result_" + fix_type}
            };

            auto comb_subfolders = list_directory(folder);

            for (const auto& comb_folder : comb_subfolders) {
                std::string comb_basename = comb_folder.substr(comb_folder.find_last_of('/') + 1);
                if (!directory_exists(comb_folder)) continue;

                // Parse combination type (e.g., "two_combination" from "two_combination_H64_H512")
                std::string comb_type = parse_combination_type_from_folder(comb_basename);
                if (comb_type.empty() || result_folder_mapping.find(comb_type) == result_folder_mapping.end()) {
                    continue;
                }

                safe_cout("  Processing " + comb_basename + " (type: " + comb_type + ")\n");

                std::string result_folder_name = result_folder_mapping[comb_type];
                std::string result_dir = combination_result_dir + "/" + result_folder_name;
                create_directory(result_dir);

                std::map<std::string, std::vector<std::map<std::string, std::string>>> results_by_pair;
                std::mutex results_mutex;

                auto freq_folders = list_directory(comb_folder);

                for (const auto& freq_folder : freq_folders) {
                    std::string freq_basename = freq_folder.substr(freq_folder.find_last_of('/') + 1);
                    if (freq_basename.find("freq_") == std::string::npos ||
                        !directory_exists(freq_folder)) {
                        continue;
                    }

                    int frequency = parse_freq_from_folder(freq_basename);
                    if (frequency < 0) continue;

                    safe_cout("    Processing subfolder: " + freq_basename +
                             " (freq=" + std::to_string(frequency) + ")\n");

                    auto files = list_directory(freq_folder);

                    for (const auto& file : files) {
                        std::string filename = file.substr(file.find_last_of('/') + 1);
                        if (filename.find(".csv") == std::string::npos) {
                            continue;
                        }

                        // Extract pair/triplet/quadruplet identifier
                        std::string pair_id;
                        if (filename.find("pair_") != std::string::npos) {
                            size_t start = filename.find("pair_");
                            size_t end = filename.find("_freq_");
                            if (end != std::string::npos) {
                                pair_id = filename.substr(start, end - start);
                            }
                        } else if (filename.find("triplet_") != std::string::npos) {
                            size_t start = filename.find("triplet_");
                            size_t end = filename.find("_freq_");
                            if (end != std::string::npos) {
                                pair_id = filename.substr(start, end - start);
                            }
                        } else if (filename.find("quadruplet_") != std::string::npos) {
                            size_t start = filename.find("quadruplet_");
                            size_t end = filename.find("_freq_");
                            if (end != std::string::npos) {
                                pair_id = filename.substr(start, end - start);
                            }
                        }

                        if (pair_id.empty()) continue;

                        safe_cout("      Processing " + filename + " (" + pair_id + ")\n");

                        auto jobs = read_jobs_from_csv(file);
                        if (jobs.empty()) continue;

                        try {
                            // Run multimode algorithm
                            auto result_pair = multi_mode_algo(jobs, nJobsPerRound, modes_to_run);
                            std::map<int, double> mode_l2_results = result_pair.first;
                            std::map<int, double> mode_max_flow_results = result_pair.second;

                            std::map<std::string, std::string> result_map;
                            result_map["frequency"] = std::to_string(frequency);

                            // Store results for each mode
                            for (int mode : modes_to_run) {
                                result_map["l2_mode_" + std::to_string(mode)] =
                                    std::to_string(mode_l2_results[mode]);
                                result_map["max_mode_" + std::to_string(mode)] =
                                    std::to_string(mode_max_flow_results[mode]);
                            }

                            {
                                std::lock_guard<std::mutex> lock(results_mutex);
                                results_by_pair[pair_id].push_back(result_map);
                            }
                        } catch (const std::exception& e) {
                            safe_cout("Error processing " + file + ": " + std::string(e.what()) + "\n");
                            continue;
                        }
                    }
                }

                // Write results for each pair/triplet/quadruplet
                for (auto& pair : results_by_pair) {
                    if (pair.second.empty()) continue;

                    std::string output_file;
                    if (base_version >= 0) {
                        output_file = result_dir + "/" + pair.first + "_" + fix_type + "_" +
                                     algo_name + "_njobs" + std::to_string(nJobsPerRound) + "_" +
                                     std::to_string(base_version) + "_result.csv";
                    } else {
                        output_file = result_dir + "/" + pair.first + "_" + fix_type + "_" +
                                     algo_name + "_njobs" + std::to_string(nJobsPerRound) + "_result.csv";
                    }

                    safe_cout("    Writing " + std::to_string(pair.second.size()) +
                             " results to " + output_file + "\n");

                    std::ofstream out(output_file);

                    // Write header with mode-specific columns
                    out << "frequency";
                    for (int mode : modes_to_run) {
                        out << "," << algo_name << "_njobs" << nJobsPerRound
                            << "_mode" << mode << "_L2_norm_flow_time";
                    }
                    for (int mode : modes_to_run) {
                        out << "," << algo_name << "_njobs" << nJobsPerRound
                            << "_mode" << mode << "_maximum_flow_time";
                    }
                    out << "\n";

                    // Sort by frequency
                    std::sort(pair.second.begin(), pair.second.end(),
                        [](const auto& a, const auto& b) {
                            return std::stoi(a.at("frequency")) < std::stoi(b.at("frequency"));
                        });

                    // Write data rows
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

                    out.close();
                }
            }
        }

        safe_cout("========================================\n");
        safe_cout("Completed processing " + fix_type + " combination (multimode)\n");
        safe_cout("========================================\n\n");
    }
}

#endif // PROCESS_FIX_COMBINATION_FOLDERS_H
