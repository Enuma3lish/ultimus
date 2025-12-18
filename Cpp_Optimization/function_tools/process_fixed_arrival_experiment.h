#ifndef PROCESS_FIXED_ARRIVAL_EXPERIMENT_H
#define PROCESS_FIXED_ARRIVAL_EXPERIMENT_H

#include <string>
#include <vector>
#include <map>
#include <fstream>
#include <iostream>
#include <regex>
#include "utils.h"
#include "_run_random.h"

/**
 * 固定到达率实验处理器
 *
 * 处理结构：
 * data/
 * └── fixed_arrival_{arrival_name}_{replication}/
 *     └── param_{param_name}/
 *         └── coherence_{ct}/
 *             └── fixed_arrival_{arrival_name}_{param_name}_ct{ct}.csv
 *
 * 输出结构：
 * algorithm_result/
 * └── {Algorithm}_result/
 *     └── fixed_arrival_experiment_result/
 *         └── fixed_arrival_{arrival_name}_{param_name}_result_{Algorithm}_{replication}.csv
 */

template<typename AlgoFunc>
void process_fixed_arrival_experiment(AlgoFunc algo, const std::string& algo_name,
                                      const std::string& data_dir, const std::string& output_dir) {

    std::string result_dir = output_dir + "/fixed_arrival_experiment_result";
    create_directory(result_dir);

    std::cout << "\n" << std::string(70, '=') << "\n";
    std::cout << "处理固定到达率实验: " << algo_name << "\n";
    std::cout << std::string(70, '=') << "\n";

    // 存储结果：map[arrival_name][param_name][replication] = results_vector
    std::map<std::string, std::map<std::string, std::map<int, std::vector<std::map<std::string, std::string>>>>> all_results;

    // 负载条件名称
    std::vector<std::string> arrival_names = {"overload", "critical", "stable"};

    auto folders = list_directory(data_dir);

    for (const auto& folder : folders) {
        std::string basename = folder.substr(folder.find_last_of('/') + 1);

        // 匹配：fixed_arrival_{arrival_name}_{replication}
        std::regex folder_pattern(R"(fixed_arrival_(overload|critical|stable)_(\d+))");
        std::smatch matches;

        if (!std::regex_match(basename, matches, folder_pattern) || !directory_exists(folder)) {
            continue;
        }

        std::string arrival_name = matches[1].str();
        int replication = std::stoi(matches[2].str());

        std::cout << "\n负载条件: " << arrival_name << ", 重复 " << replication << "\n";

        // 遍历参数文件夹
        auto param_folders = list_directory(folder);
        for (const auto& param_folder : param_folders) {
            std::string param_basename = param_folder.substr(param_folder.find_last_of('/') + 1);

            if (param_basename.find("param_") != 0 || !directory_exists(param_folder)) {
                continue;
            }

            // 提取参数名称
            std::string param_name = param_basename.substr(6);  // 去掉 "param_"

            std::cout << "  参数: " << param_name << "\n";

            // 遍历 coherence time 文件夹
            auto ct_folders = list_directory(param_folder);
            for (const auto& ct_folder : ct_folders) {
                std::string ct_basename = ct_folder.substr(ct_folder.find_last_of('/') + 1);

                if (ct_basename.find("coherence_") != 0 || !directory_exists(ct_folder)) {
                    continue;
                }

                // 提取 coherence time
                int coherence_time = std::stoi(ct_basename.substr(10));  // 去掉 "coherence_"

                // 查找 CSV 文件
                auto files = list_directory(ct_folder);
                for (const auto& file : files) {
                    std::string filename = file.substr(file.find_last_of('/') + 1);
                    if (filename.find(".csv") == std::string::npos) {
                        continue;
                    }

                    // 读取工作数据
                    auto jobs = read_jobs_from_csv(file);
                    if (jobs.empty()) {
                        std::cerr << "    警告：文件为空 " << filename << "\n";
                        continue;
                    }

                    try {
                        // 运行算法
                        auto [l2_results, max_flow_results] = run_random(algo, jobs);

                        // 存储结果
                        std::map<std::string, std::string> result_map;
                        result_map["coherence_time"] = std::to_string(coherence_time);
                        result_map["l2_norm"] = std::to_string(l2_results);
                        result_map["max_flow"] = std::to_string(max_flow_results);
                        result_map["num_jobs"] = std::to_string(jobs.size());

                        all_results[arrival_name][param_name][replication].push_back(result_map);

                        std::cout << "    ct=" << coherence_time
                                 << ", L2=" << l2_results
                                 << ", MaxFlow=" << max_flow_results << "\n";

                    } catch (const std::exception& e) {
                        std::cerr << "    错误处理 " << filename << ": " << e.what() << "\n";
                        continue;
                    }
                }
            }
        }
    }

    // 写入结果文件
    std::cout << "\n" << std::string(70, '-') << "\n";
    std::cout << "保存结果...\n";

    int files_written = 0;
    for (const auto& [arrival_name, param_map] : all_results) {
        for (const auto& [param_name, rep_map] : param_map) {
            for (const auto& [replication, results] : rep_map) {
                if (results.empty()) continue;

                // 输出文件名
                std::string output_file = result_dir + "/fixed_arrival_" + arrival_name +
                                        "_" + param_name + "_result_" + algo_name +
                                        "_" + std::to_string(replication) + ".csv";

                std::ofstream out(output_file);
                out << "coherence_time," << algo_name << "_L2_norm_flow_time,"
                    << algo_name << "_max_flow_time," << algo_name << "_num_jobs\n";

                // 按 coherence_time 排序
                std::vector<std::map<std::string, std::string>> sorted_results = results;
                std::sort(sorted_results.begin(), sorted_results.end(),
                         [](const auto& a, const auto& b) {
                             return std::stoi(a.at("coherence_time")) < std::stoi(b.at("coherence_time"));
                         });

                for (const auto& result : sorted_results) {
                    out << result.at("coherence_time") << ","
                        << result.at("l2_norm") << ","
                        << result.at("max_flow") << ","
                        << result.at("num_jobs") << "\n";
                }

                out.close();
                files_written++;
            }
        }
    }

    std::cout << "✓ 完成！保存了 " << files_written << " 个结果文件\n";
    std::cout << std::string(70, '=') << "\n";
}

#endif // PROCESS_FIXED_ARRIVAL_EXPERIMENT_H
