#ifndef PROCESS_EXPERIMENT3_FOLDERS_H
#define PROCESS_EXPERIMENT3_FOLDERS_H

#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include "utils.h"
#include "_run_random.h"

/**
 * Experiment 3: Record parameter switches
 *
 * This experiment records detailed information about parameter switches
 * and analyzes the relationship between switching patterns and performance.
 */

struct SwitchEvent {
    int switch_time;
    int job_index;
    double old_param_L;
    double old_param_H;
    double new_param_L;
    double new_param_H;
    double old_inter_arrival;
    double new_inter_arrival;
    double old_load;
    double new_load;
    int duration_since_last_switch;
};

inline std::vector<SwitchEvent> read_switch_history_from_csv(const std::string& filepath) {
    std::vector<SwitchEvent> switches;
    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file " << filepath << std::endl;
        return switches;
    }

    std::string line;
    std::getline(file, line); // Skip header

    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string field;
        std::vector<std::string> fields;

        while (std::getline(ss, field, ',')) {
            fields.push_back(field);
        }

        if (fields.size() >= 11) {
            SwitchEvent event;
            event.switch_time = std::stoi(fields[0]);
            event.job_index = std::stoi(fields[1]);
            event.old_param_L = fields[2].empty() || fields[2] == "None" ? -1.0 : std::stod(fields[2]);
            event.old_param_H = fields[3].empty() || fields[3] == "None" ? -1.0 : std::stod(fields[3]);
            event.new_param_L = std::stod(fields[4]);
            event.new_param_H = std::stod(fields[5]);
            event.old_inter_arrival = fields[6].empty() || fields[6] == "None" ? -1.0 : std::stod(fields[6]);
            event.new_inter_arrival = std::stod(fields[7]);
            event.old_load = fields[8].empty() || fields[8] == "None" ? -1.0 : std::stod(fields[8]);
            event.new_load = std::stod(fields[9]);
            event.duration_since_last_switch = std::stoi(fields[10]);

            switches.push_back(event);
        }
    }

    return switches;
}

template<typename AlgoFunc>
void process_experiment3_folders(AlgoFunc algo, const std::string& algo_name,
                                 const std::string& data_dir, const std::string& output_dir) {
    std::string exp3_result_dir = output_dir + "/experiment3_record_switches_result";
    create_directory(exp3_result_dir);

    // Results: version -> coherence_time -> (performance + switch stats)
    std::map<int, std::vector<std::map<std::string, std::string>>> results_by_version;

    auto folders = list_directory(data_dir);

    for (const auto& folder : folders) {
        std::string basename = folder.substr(folder.find_last_of('/') + 1);
        if (basename.find("experiment3_record_switches_") == std::string::npos ||
            !directory_exists(folder)) {
            continue;
        }

        int base_version = extract_version_from_path(basename);
        std::cout << "Processing experiment3_record_switches base: " << basename
                 << " (version=" << base_version << ")" << std::endl;

        auto freq_folders = list_directory(folder);

        for (const auto& freq_folder : freq_folders) {
            std::string freq_basename = freq_folder.substr(freq_folder.find_last_of('/') + 1);
            if (freq_basename.find("freq_") == std::string::npos ||
                !directory_exists(freq_folder)) {
                continue;
            }

            int frequency = parse_freq_from_folder(freq_basename);
            if (frequency < 0) continue;

            std::cout << "  Processing subfolder: " << freq_basename
                     << " (coherence_time=" << frequency << ")" << std::endl;

            // Find job file and switch file
            std::string job_file;
            std::string switch_file;

            auto files = list_directory(freq_folder);
            for (const auto& file : files) {
                std::string filename = file.substr(file.find_last_of('/') + 1);
                if (filename.find("exp3_jobs_freq_") != std::string::npos) {
                    job_file = file;
                } else if (filename.find("exp3_switches_freq_") != std::string::npos) {
                    switch_file = file;
                }
            }

            if (job_file.empty()) {
                std::cerr << "  Warning: No job file found in " << freq_folder << std::endl;
                continue;
            }

            std::cout << "    Processing job file: " << job_file.substr(job_file.find_last_of('/') + 1) << std::endl;

            auto jobs = read_jobs_from_csv(job_file);
            if (jobs.empty()) continue;

            // Read switch history if available
            std::vector<SwitchEvent> switches;
            if (!switch_file.empty()) {
                std::cout << "    Reading switch history: " << switch_file.substr(switch_file.find_last_of('/') + 1) << std::endl;
                switches = read_switch_history_from_csv(switch_file);
                std::cout << "    Found " << switches.size() << " switch events" << std::endl;
            }

            try {
                auto [l2_results, max_flow_results] = run_random(algo, jobs);
                std::cout << "    Results: L2=" << l2_results
                         << ", Max Flow=" << max_flow_results << std::endl;

                // Calculate switch statistics
                int num_switches = switches.empty() ? 0 : switches.size() - 1; // Exclude initial state
                double avg_duration = 0.0;
                int overload_switches = 0;
                double max_load = 0.0;
                double min_load = 999.0;

                if (!switches.empty()) {
                    double total_duration = 0.0;
                    for (size_t i = 1; i < switches.size(); ++i) {
                        total_duration += switches[i].duration_since_last_switch;
                        if (switches[i].new_load > 1.0) overload_switches++;
                        if (switches[i].new_load > max_load) max_load = switches[i].new_load;
                        if (switches[i].new_load < min_load) min_load = switches[i].new_load;
                    }
                    avg_duration = switches.size() > 1 ? total_duration / (switches.size() - 1) : 0.0;
                }

                std::map<std::string, std::string> result_map;
                result_map["coherence_time"] = std::to_string(frequency);
                result_map["l2_results"] = std::to_string(l2_results);
                result_map["max_flow_results"] = std::to_string(max_flow_results);
                result_map["num_switches"] = std::to_string(num_switches);
                result_map["avg_switch_duration"] = std::to_string(avg_duration);
                result_map["overload_switches"] = std::to_string(overload_switches);
                result_map["max_load"] = std::to_string(max_load);
                result_map["min_load"] = std::to_string(min_load);

                results_by_version[base_version].push_back(result_map);
            } catch (const std::exception& e) {
                std::cerr << "Error processing " << job_file << ": " << e.what() << std::endl;
                continue;
            }
        }
    }

    // Write results grouped by version
    for (auto& pair : results_by_version) {
        if (pair.second.empty()) continue;

        std::string output_file;
        if (pair.first >= 0) {
            output_file = exp3_result_dir + "/experiment3_record_switches_result_" +
                         algo_name + "_" + std::to_string(pair.first) + ".csv";
        } else {
            output_file = exp3_result_dir + "/experiment3_record_switches_result_" + algo_name + ".csv";
        }

        std::cout << "Writing " << pair.second.size() << " results to "
                 << output_file << std::endl;

        std::ofstream out(output_file);
        out << "coherence_time,"
            << algo_name << "_L2_norm_flow_time,"
            << algo_name << "_max_flow_time,"
            << "num_switches,"
            << "avg_switch_duration,"
            << "overload_switches,"
            << "max_load,"
            << "min_load\n";

        for (const auto& result : pair.second) {
            out << result.at("coherence_time") << ","
                << result.at("l2_results") << ","
                << result.at("max_flow_results") << ","
                << result.at("num_switches") << ","
                << result.at("avg_switch_duration") << ","
                << result.at("overload_switches") << ","
                << result.at("max_load") << ","
                << result.at("min_load") << "\n";
        }

        out.close();
        std::cout << "Successfully wrote " << output_file << std::endl;
    }

    std::cout << "\nExperiment 3 processing complete!" << std::endl;
}

#endif // PROCESS_EXPERIMENT3_FOLDERS_H
