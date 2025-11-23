#include <iostream>
#include <string>
#include <vector>
#include <functional>
#include "NC_RR_algorithm.h"
#include "process_avg_folders.h"
#include "process_random_folders.h"
#include "process_softrandom_folders.h"
#include "utils.h"

int main(int argc, char* argv[]) {
    std::cout << "============================================================" << std::endl;
    std::cout << "Non-Clairvoyant Round Robin Batch Processing" << std::endl;
    std::cout << "============================================================" << std::endl;
    
    // Configuration
    std::string data_dir = "/home/melowu/Work/ultimus/data";
    std::string output_dir = "/home/melowu/Work/ultimus/RR_result";
    int time_quantum = 1;  // Default time quantum
    
    // Parse command line arguments
    if (argc > 1) {
        data_dir = argv[1];
    }
    if (argc > 2) {
        output_dir = argv[2];
    }
    if (argc > 3) {
        time_quantum = std::stoi(argv[3]);
    }
    
    std::cout << "Data directory: " << data_dir << std::endl;
    std::cout << "Output directory: " << output_dir << std::endl;
    std::cout << "Time quantum: " << time_quantum << std::endl;
    std::cout << "============================================================" << std::endl;
    
    // Create main output directory
    create_directory(output_dir);
    
    // Create lambda wrapper with captured time_quantum
    // This lambda returns SchedulingResult which has .l2_norm_flow_time member
    auto nc_rr_lambda = [time_quantum](std::vector<Job>& jobs) -> SchedulingResult {
        return NC_RR(jobs, time_quantum);
    };
    
    // Process avg30 files
    // run() will extract .l2_norm_flow_time from SchedulingResult
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing avg files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_avg_folders(nc_rr_lambda, "RR", data_dir, output_dir);
    
    // Process Bounded Pareto random files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Bounded Pareto random files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_bounded_pareto_random_folders(nc_rr_lambda, "RR", data_dir, output_dir);

    // Process Normal random files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Normal random files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_normal_random_folders(nc_rr_lambda, "RR", data_dir, output_dir);

    // Process Bounded Pareto softrandom files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Bounded Pareto softrandom files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_bounded_pareto_softrandom_folders(nc_rr_lambda, "RR", data_dir, output_dir);

    // Process Normal softrandom files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Normal softrandom files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_normal_softrandom_folders(nc_rr_lambda, "RR", data_dir, output_dir);
    
    std::cout << "\n============================================================" << std::endl;
    std::cout << "NC-RR batch processing completed successfully!" << std::endl;
    std::cout << "============================================================" << std::endl;
    
    return 0;
}