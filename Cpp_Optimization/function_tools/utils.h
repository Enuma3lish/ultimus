#ifndef UTILS_H
#define UTILS_H

#include <string>
#include <regex>
#include <vector>
#include <fstream>
#include <sstream>
#include <iostream>
#include <sys/stat.h>
#include <dirent.h>
#include <algorithm>
#include "Job.h"

// ============ extract_version_from_path ============
inline int extract_version_from_path(const std::string& folder_path) {
    std::regex pattern("_(\\d+)$");
    std::smatch match;
    if (std::regex_search(folder_path, match, pattern)) {
        return std::stoi(match[1]);
    }
    return -1;
}

struct AvgParams {
    double arrival_rate;
    double bp_L;
    double bp_H;
    std::string distribution_type;  // "BP" or "Normal"
    double normal_mean;  // For Normal distribution
    double normal_std;   // For Normal distribution
};

inline AvgParams parse_avg_filename(const std::string& filename) {
    std::regex pattern("\\((\\d+(?:\\.\\d+)?),\\s*(\\d+(?:\\.\\d+)?)_(\\d+)\\)");
    std::smatch match;
    if (std::regex_search(filename, match, pattern)) {
        return {std::stod(match[1]), std::stod(match[2]), static_cast<double>(std::stoi(match[3]))};
    }
    return {-1.0, -1.0, -1.0};
}

// ============ parse_freq_from_folder ============
inline int parse_freq_from_folder(const std::string& folder_name) {
    std::regex pattern("freq_(\\d+)(?:_\\d+)?");
    std::smatch match;
    if (std::regex_search(folder_name, match, pattern)) {
        return std::stoi(match[1]);
    }
    return -1;
}

// ============ parse_combination_type_from_folder ============
inline std::string parse_combination_type_from_folder(const std::string& folder_name) {
    // Extract combination type from folder names like:
    // two_combination_H64_H512 -> "two_combination"
    // three_combination_std6_std9_std12 -> "three_combination"
    // four_combination_H64_H512_H4096_H32768 -> "four_combination"
    std::regex pattern("(two_combination|three_combination|four_combination)");
    std::smatch match;
    if (std::regex_search(folder_name, match, pattern)) {
        return match[1];
    }
    return "";
}

// ============ parse_combination_params_from_folder ============
inline std::string parse_combination_params_from_folder(const std::string& folder_name) {
    // Extract parameter part from folder names like:
    // two_combination_H64_H512 -> "H64_H512"
    // three_combination_std6_std9_std12 -> "std6_std9_std12"
    std::regex pattern("(?:two|three|four)_combination_(.+)$");
    std::smatch match;
    if (std::regex_search(folder_name, match, pattern)) {
        return match[1];
    }
    return "";
}

// ============ read_jobs_from_csv ============
inline std::vector<Job> read_jobs_from_csv(const std::string& filepath) {
    std::vector<Job> jobs;
    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file " << filepath << std::endl;
        return jobs;
    }
    
    std::string line;
    std::getline(file, line); // Skip header
    
    int idx = 0;
    while (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string arrival_str, size_str;
        
        if (std::getline(ss, arrival_str, ',') && std::getline(ss, size_str, ',')) {
            Job job;
            job.arrival_time = std::stoi(arrival_str);
            job.job_size = std::stoi(size_str);
            job.job_index = idx++;
            job.remaining_time = job.job_size;
            jobs.push_back(job);
        }
    }
    
    file.close();
    return jobs;
}

// ============ Directory utilities ============
inline bool directory_exists(const std::string& path) {
    struct stat info;
    return stat(path.c_str(), &info) == 0 && (info.st_mode & S_IFDIR);
}

inline void create_directory(const std::string& path) {
    if (!directory_exists(path)) {
        #ifdef _WIN32
            _mkdir(path.c_str());
        #else
            mkdir(path.c_str(), 0755);
        #endif
    }
}

inline std::vector<std::string> list_directory(const std::string& path) {
    std::vector<std::string> files;
    DIR* dir = opendir(path.c_str());
    if (dir) {
        struct dirent* entry;
        while ((entry = readdir(dir)) != nullptr) {
            std::string name = entry->d_name;
            if (name != "." && name != "..") {
                files.push_back(path + "/" + name);
            }
        }
        closedir(dir);
    }
    std::sort(files.begin(), files.end());
    return files;
}

#endif // UTILS_H