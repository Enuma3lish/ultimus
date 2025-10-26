#include <iostream>
#include <string>
#include <vector>
#include <mutex>

// Include all necessary headers
#include "Job.h"
#include "utils.h"
#include "MLFQ_algorithm.h"
#include "_run.h"
#include "_run_random.h"
#include "process_avg_folders.h"
#include "process_random_folders.h"
#include "process_softrandom_folders.h"

// Main function to demonstrate MLFQ usage
int main(int argc, char* argv[]) {
    // Default parameters
    std::string data_dir = "./data";
    std::string output_dir = "./output";
    int num_queues = 1;  // Default number of MLFQ queues
    
    // Parse command line arguments if provided
    if (argc >= 2) {
        data_dir = argv[1];
    }
    if (argc >= 3) {
        output_dir = argv[2];
    }
    if (argc >= 4) {
        num_queues = std::atoi(argv[3]);
    }
    
    std::cout << "==================================================" << std::endl;
    std::cout << "MLFQ Scheduler - Non-Clairvoyant Implementation" << std::endl;
    std::cout << "==================================================" << std::endl;
    std::cout << "Data directory: " << data_dir << std::endl;
    std::cout << "Output directory: " << output_dir << std::endl;
    std::cout << "Number of MLFQ queues: " << num_queues << std::endl;
    std::cout << "Queue time quanta: Queue 1=1, Queue 2=2, Queue 3=4, ..." << std::endl;
    std::cout << "==================================================" << std::endl;
    
    // Create output directory if it doesn't exist
    create_directory(output_dir);
    
    // Create lambda wrapper for MLFQ algorithm with configurable num_queues
    auto mlfq_algo = [num_queues](std::vector<Job> jobs) -> MLFQResult {
        return MLFQ(jobs, num_queues);
    };
    
    std::cout << "\n[1/3] Processing AVG folders..." << std::endl;
    std::cout << "----------------------------------------" << std::endl;
    try {
        process_avg_folders(mlfq_algo, "MLFQ", data_dir, output_dir);
        std::cout << "✓ AVG folder processing completed successfully" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "✗ Error processing AVG folders: " << e.what() << std::endl;
    }
    
    std::cout << "\n[2/3] Processing RANDOM folders..." << std::endl;
    std::cout << "----------------------------------------" << std::endl;
    try {
        process_random_folders(mlfq_algo, "MLFQ", data_dir, output_dir);
        std::cout << "✓ RANDOM folder processing completed successfully" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "✗ Error processing RANDOM folders: " << e.what() << std::endl;
    }
    
    std::cout << "\n[3/3] Processing SOFTRANDOM folders..." << std::endl;
    std::cout << "----------------------------------------" << std::endl;
    try {
        process_softrandom_folders(mlfq_algo, "MLFQ", data_dir, output_dir);
        std::cout << "✓ SOFTRANDOM folder processing completed successfully" << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "✗ Error processing SOFTRANDOM folders: " << e.what() << std::endl;
    }
    
    std::cout << "\n==================================================" << std::endl;
    std::cout << "All processing completed!" << std::endl;
    std::cout << "Results saved to: " << output_dir << std::endl;
    std::cout << "==================================================" << std::endl;
    
    return 0;
}