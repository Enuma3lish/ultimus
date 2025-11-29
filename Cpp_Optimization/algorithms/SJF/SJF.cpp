#include <iostream>
#include <string>
#include <vector>
#include "SJF_algorithm.h"
#include "process_avg_folders.h"
#include "process_random_folders.h"
#include "process_softrandom_folders.h"
#include "utils.h"

int main(int argc, char* argv[]) {
    std::cout << "============================================================" << std::endl;
    std::cout << "Shortest Job First (SJF) Batch Processing" << std::endl;
    std::cout << "============================================================" << std::endl;
    
    // Configuration
    std::string data_dir = "/home/melowu/Work/ultimus/data";
    std::string output_dir = "/home/melowu/Work/ultimus/SJF_result";
    
    // Parse command line arguments
    if (argc > 1) {
        data_dir = argv[1];
    }
    if (argc > 2) {
        output_dir = argv[2];
    }
    
    std::cout << "Data directory: " << data_dir << std::endl;
    std::cout << "Output directory: " << output_dir << std::endl;
    std::cout << "============================================================" << std::endl;
    
    // Create main output directory
    create_directory(output_dir);
    
    // Create lambda wrapper for SJF algorithm
    auto sjf_lambda = [](std::vector<Job>& jobs) -> SchedulingResult {
        return SJF(jobs);
    };
    
    // Process avg30 files
    // std::cout << "\n========================================" << std::endl;
    // std::cout << "Processing avg files..." << std::endl;
    // std::cout << "========================================" << std::endl;
    // process_avg_folders(sjf_lambda, "SJF", data_dir, output_dir);
    
    // Process Bounded Pareto random files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Bounded Pareto random files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_bounded_pareto_random_folders(sjf_lambda, "SJF", data_dir, output_dir);

    // Process Normal random files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Normal random files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_normal_random_folders(sjf_lambda, "SJF", data_dir, output_dir);

    // Process Bounded Pareto softrandom files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Bounded Pareto softrandom files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_bounded_pareto_softrandom_folders(sjf_lambda, "SJF", data_dir, output_dir);

    // Process Normal softrandom files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Normal softrandom files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_normal_softrandom_folders(sjf_lambda, "SJF", data_dir, output_dir);

    // Process Bounded Pareto combination random files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Bounded Pareto combination random files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_bounded_pareto_combination_random_folders(sjf_lambda, "SJF", data_dir, output_dir);

    // Process Normal combination random files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Normal combination random files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_normal_combination_random_folders(sjf_lambda, "SJF", data_dir, output_dir);

    // Process Bounded Pareto combination softrandom files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Bounded Pareto combination softrandom files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_bounded_pareto_combination_softrandom_folders(sjf_lambda, "SJF", data_dir, output_dir);

    // Process Normal combination softrandom files
    std::cout << "\n========================================" << std::endl;
    std::cout << "Processing Normal combination softrandom files..." << std::endl;
    std::cout << "========================================" << std::endl;
    process_normal_combination_softrandom_folders(sjf_lambda, "SJF", data_dir, output_dir);

    std::cout << "\n============================================================" << std::endl;
    std::cout << "SJF batch processing completed successfully!" << std::endl;
    std::cout << "============================================================" << std::endl;
    
    return 0;
}