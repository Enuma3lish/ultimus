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

struct NewAvgParams {
    double arrival_rate;
    double bp_L;
    double bp_H;
    std::string distribution_type;
    double normal_mean;
    double normal_std;
};

inline NewAvgParams parse_new_avg_filename(const std::string& filename) {
    // Format: avg_(arrival,L_H).csv  e.g. avg_(30,1_100).csv
    std::regex pattern("\\((\\d+(?:\\.\\d+)?),\\s*(\\d+(?:\\.\\d+)?)_(\\d+)\\)");
    std::smatch match;
    if (std::regex_search(filename, match, pattern)) {
        NewAvgParams params;
        params.arrival_rate = std::stod(match[1]);
        params.bp_L = std::stod(match[2]);
        params.bp_H = static_cast<double>(std::stoi(match[3]));
        params.distribution_type = "BP";
        params.normal_mean = 0;
        params.normal_std = 0;
        return params;
    }
    return {-1.0, -1.0, -1.0, "", 0, 0};
}

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

// ============ Longest H interval info ============
struct LongestHInfo {
    int start_job_index;
    int end_job_index;
    int job_count;
    int total_jobs;
    double job_count_percentage;
    long long longest_H_job_size;
    long long total_job_size;
    double job_size_percentage;
    bool valid;  // True if file was found and parsed successfully
};

inline LongestHInfo read_longest_H_info(const std::string& folder_path) {
    LongestHInfo info = {-1, -1, 0, 0, 0.0, 0, 0, 0.0, false};
    std::string filepath = folder_path + "/longest_H_info.csv";
    std::ifstream file(filepath);
    if (!file.is_open()) {
        return info;  // File not found, return invalid info
    }

    std::string line;
    std::getline(file, line);  // Skip header

    if (std::getline(file, line)) {
        std::stringstream ss(line);
        std::string field;

        // Read all fields: start_job_index,end_job_index,job_count,total_jobs,job_count_percentage,longest_H_job_size,total_job_size,job_size_percentage
        if (std::getline(ss, field, ',')) info.start_job_index = std::stoi(field);
        if (std::getline(ss, field, ',')) info.end_job_index = std::stoi(field);
        if (std::getline(ss, field, ',')) info.job_count = std::stoi(field);
        if (std::getline(ss, field, ',')) info.total_jobs = std::stoi(field);
        if (std::getline(ss, field, ',')) info.job_count_percentage = std::stod(field);
        if (std::getline(ss, field, ',')) info.longest_H_job_size = std::stoll(field);
        if (std::getline(ss, field, ',')) info.total_job_size = std::stoll(field);
        if (std::getline(ss, field, ',')) info.job_size_percentage = std::stod(field);

        info.valid = true;
    }

    file.close();
    return info;
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

// Create directories recursively (like mkdir -p)
inline bool create_directories_recursive(const std::string& path) {
    if (path.empty()) return false;
    if (directory_exists(path)) return true;

    // Find parent directory
    size_t pos = path.find_last_of('/');
    if (pos == std::string::npos) {
        // No parent, just create
        create_directory(path);
        return directory_exists(path);
    }

    // Handle trailing slash
    if (pos == path.length() - 1) {
        return create_directories_recursive(path.substr(0, pos));
    }

    std::string parent = path.substr(0, pos);

    // Recursively create parent directories
    if (!parent.empty() && parent != "." && parent != "/") {
        if (!create_directories_recursive(parent)) {
            return false;
        }
    }

    // Create this directory
    create_directory(path);
    return directory_exists(path);
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