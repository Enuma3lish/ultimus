#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include "Job.h"
#include "SETF_algorithm.h"
#include "utils.h"
#include "_run.h"
#include "_run_random.h"
#include "process_avg_folders.h"
#include "process_random_folders.h"
#include "process_softrandom_folders.h"
#include "process_experiment1_folders.h"
#include "process_experiment2_folders.h"
#include "process_experiment3_folders.h"
#include "process_experiment4_folders.h"
#include "process_experiment5_folders.h"
#include "process_experiment6_folders.h"
#include "process_fix_combination_folders.h"

int main() {
    std::string data_dir = "/Users/melowu/Desktop/ultimus/data";
    std::string output_dir = "/Users/melowu/Desktop/ultimus/SETF_result";
    
    std::cout << "============================================================\n";
    std::cout << "Starting SETF batch processing:\n";
    std::cout << "  Data directory: " << data_dir << "\n";
    std::cout << "  Output directory: " << output_dir << "\n";
    std::cout << "============================================================\n";
    
    create_directory(output_dir);
    
    // std::cout << "\n========================================\n";
    // std::cout << "Processing avg files...\n";
    // std::cout << "========================================\n";
    // process_avg_folders(Setf, "SETF", data_dir, output_dir);
    
    std::cout << "\n========================================\n";
    std::cout << "Processing Bounded Pareto random files...\n";
    std::cout << "========================================\n";
    process_bounded_pareto_random_folders(Setf, "SETF", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Normal random files...\n";
    std::cout << "========================================\n";
    process_normal_random_folders(Setf, "SETF", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Bounded Pareto softrandom files...\n";
    std::cout << "========================================\n";
    process_bounded_pareto_softrandom_folders(Setf, "SETF", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Normal softrandom files...\n";
    std::cout << "========================================\n";
    process_normal_softrandom_folders(Setf, "SETF", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Bounded Pareto combination random files...\n";
    std::cout << "========================================\n";
    process_bounded_pareto_combination_random_folders(Setf, "SETF", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Normal combination random files...\n";
    std::cout << "========================================\n";
    process_normal_combination_random_folders(Setf, "SETF", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Bounded Pareto combination softrandom files...\n";
    std::cout << "========================================\n";
    process_bounded_pareto_combination_softrandom_folders(Setf, "SETF", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Normal combination softrandom files...\n";
    std::cout << "========================================\n";
    process_normal_combination_softrandom_folders(Setf, "SETF", data_dir, output_dir);

    std::cout << "\n============================================================\n";

    // ==================== FIX COMBINATION FOLDERS (Fixed Mean Arrival Time) ====================

    std::cout << "\n========================================\n";
    std::cout << "Processing Fix Combination Folders (fix20, fix30, fix40)...\n";
    std::cout << "========================================\n";
    process_fix_combination_folders(Setf, "SETF", data_dir, output_dir);

    std::cout << "SETF batch processing completed successfully!\n  (Including fix combination folders)\n";
    std::cout << "============================================================\n";

    return 0;
}