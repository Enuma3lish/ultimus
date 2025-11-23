#include <iostream>
#include <vector>
#include <cmath>
#include "BAL_algorithm.h"
#include "utils.h"
#include "process_avg_folders.h"
#include "process_random_folders.h"
#include "process_softrandom_folders.h"

// Wrapper function for BAL that calculates starvation threshold automatically
BALResult BalWrapper(std::vector<Job> jobs) {
    int njob = jobs.size();
    double starvation_threshold = pow(njob, 2.0/3.0);
    return Bal(jobs, starvation_threshold);
}

int main() {
    std::string data_dir = "/home/melowu/Work/ultimus/data";
    std::string output_dir = "/home/melowu/Work/ultimus/BAL_result";
    
    std::cout << "============================================================\n";
    std::cout << "Starting BAL batch processing:\n";
    std::cout << "  Data directory: " << data_dir << "\n";
    std::cout << "  Output directory: " << output_dir << "\n";
    std::cout << "============================================================\n";
    
    create_directory(output_dir);
    
    std::cout << "\n========================================\n";
    std::cout << "Processing avg files...\n";
    std::cout << "========================================\n";
    process_avg_folders(BalWrapper, "BAL", data_dir, output_dir);
    
    std::cout << "\n========================================\n";
    std::cout << "Processing Bounded Pareto random files...\n";
    std::cout << "========================================\n";
    process_bounded_pareto_random_folders(BalWrapper, "BAL", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Normal random files...\n";
    std::cout << "========================================\n";
    process_normal_random_folders(BalWrapper, "BAL", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Bounded Pareto softrandom files...\n";
    std::cout << "========================================\n";
    process_bounded_pareto_softrandom_folders(BalWrapper, "BAL", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Normal softrandom files...\n";
    std::cout << "========================================\n";
    process_normal_softrandom_folders(BalWrapper, "BAL", data_dir, output_dir);
    
    std::cout << "\n============================================================\n";
    std::cout << "BAL batch processing completed successfully!\n";
    std::cout << "============================================================\n";
    
    return 0;
}