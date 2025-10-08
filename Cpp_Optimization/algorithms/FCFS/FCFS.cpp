#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include "Optimized_FCFS_algorithm.h"
#include "utils.h"
#include "_run.h"
#include "_run_random.h"
#include "process_avg_folders.h"
#include "process_random_folders.h"
#include "process_softrandom_folders.h"

int main() {
    std::string data_dir = "/home/melowu/Work/ultimus/data";
    std::string output_dir = "/home/melowu/Work/ultimus/FCFS_result";
    
    std::cout << "============================================================\n";
    std::cout << "Starting FCFS batch processing:\n";
    std::cout << "  Data directory: " << data_dir << "\n";
    std::cout << "  Output directory: " << output_dir << "\n";
    std::cout << "============================================================\n";
    
    create_directory(output_dir);
    
    std::cout << "\n========================================\n";
    std::cout << "Processing avg files...\n";
    std::cout << "========================================\n";
    process_avg_folders(Fcfs, "FCFS", data_dir, output_dir);
    
    std::cout << "\n========================================\n";
    std::cout << "Processing random files...\n";
    std::cout << "========================================\n";
    process_random_folders(Fcfs, "FCFS", data_dir, output_dir);
    
    std::cout << "\n========================================\n";
    std::cout << "Processing softrandom files...\n";
    std::cout << "========================================\n";
    process_softrandom_folders(Fcfs, "FCFS", data_dir, output_dir);
    
    std::cout << "\n============================================================\n";
    std::cout << "FCFS batch processing completed successfully!\n";
    std::cout << "============================================================\n";
    
    return 0;
}