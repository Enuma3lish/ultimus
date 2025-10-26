#include <iostream>
#include <string>
#include <vector>
#include <mutex>
#include "RMLF_algorithm.h"
#include "utils.h"
#include "process_avg_folders.h"
#include "process_random_folders.h"
#include "process_softrandom_folders.h"

// Wrapper function for average data processing
RMLFResult RMLF_wrapper(std::vector<Job> jobs) {
    return RMLF_algorithm(jobs);
}

int main(int argc, char* argv[]) {
    // Default paths
    std::string data_dir = "/home/melowu/Work/ultimus/data";
    std::string output_dir = "/home/melowu/Work/ultimus/RMLF_result";
    
    // Parse command line arguments
    if (argc >= 2) {
        data_dir = argv[1];
    }
    if (argc >= 3) {
        output_dir = argv[2];
    }
    
    std::cout << "=== RMLF (Randomized Multi-Level Feedback) Scheduler ===" << std::endl;
    std::cout << "Data directory: " << data_dir << std::endl;
    std::cout << "Output directory: " << output_dir << std::endl;
    std::cout << std::endl;
    
    // Create output directory if it doesn't exist
    create_directory(output_dir);
    
    std::mutex cout_mutex;
    
    // Process different types of data
    std::cout << "Processing data..." << std::endl;
    std::cout << std::endl;
    
    // Check what types of data exist and process accordingly
    auto folders = list_directory(data_dir);
    
    bool has_avg = false;
    bool has_random = false;
    bool has_softrandom = false;
    
    for (const auto& folder : folders) {
        std::string basename = folder.substr(folder.find_last_of('/') + 1);
        if (basename.find("avg_") != std::string::npos) {
            has_avg = true;
        }
        if (basename.find("freq_") != std::string::npos && 
            basename.find("softrandom_") == std::string::npos) {
            has_random = true;
        }
        if (basename.find("softrandom_") != std::string::npos) {
            has_softrandom = true;
        }
    }
    
    // Process average data if exists
    if (has_avg) {
        std::cout << ">>> Processing average data folders..." << std::endl;
        try {
            process_avg_folders(RMLF_wrapper, "RMLF", data_dir, output_dir);
            std::cout << "Average data processing completed." << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "Error processing average data: " << e.what() << std::endl;
        }
        std::cout << std::endl;
    }
    
    // Process random data if exists
    if (has_random) {
        std::cout << ">>> Processing random data folders..." << std::endl;
        try {
            process_random_folders(RMLF_wrapper, "RMLF", data_dir, output_dir);
            std::cout << "Random data processing completed." << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "Error processing random data: " << e.what() << std::endl;
        }
        std::cout << std::endl;
    }
    
    // Process softrandom data if exists
    if (has_softrandom) {
        std::cout << ">>> Processing softrandom data folders..." << std::endl;
        try {
            process_softrandom_folders(RMLF_wrapper, "RMLF", data_dir, output_dir);
            std::cout << "Softrandom data processing completed." << std::endl;
        } catch (const std::exception& e) {
            std::cerr << "Error processing softrandom data: " << e.what() << std::endl;
        }
        std::cout << std::endl;
    }
    
    if (!has_avg && !has_random && !has_softrandom) {
        std::cout << "No valid data folders found in " << data_dir << std::endl;
        std::cout << "Looking for folders starting with 'avg_', 'freq_', or 'softrandom_'" << std::endl;
        return 1;
    }
    
    std::cout << "=== All processing completed ===" << std::endl;
    std::cout << "Results saved to: " << output_dir << std::endl;
    
    return 0;
}