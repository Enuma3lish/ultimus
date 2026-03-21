#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <random> // Needed for JobSizePool
#include <cassert>
#include <string>
#include <map>
#include <thread>
#include <mutex>
#include <fstream>
#include <sstream>
#include <iomanip> // Needed for save_analysis_results
#include <set>       // Needed for main
#include <sys/stat.h> // Needed for ensure_directory_exists

// Headers for the algorithms
#include "RMLF_algorithm.h"
#include "Optimized_FCFS_algorithm.h" // Includes Job.h
#include "utils.h"

// Headers for the processing templates
#include "process_avg_folders.h"
#include "process_random_folders.h"
#include "process_softrandom_folders.h"
#include "process_fix_combination_folders.h"

// Global mutex for thread-safe console output
std::mutex cout_mutex;

// Thread-safe console output
void safe_cout(const std::string& message) {
    std::lock_guard<std::mutex> lock(cout_mutex);
    std::cout << message << std::flush;
}

// Helper to create directory if it doesn't exist
bool ensure_directory_exists(const std::string& path) {
    struct stat info;
    if (stat(path.c_str(), &info) != 0) {
        #ifdef _WIN32
            return _mkdir(path.c_str()) == 0;
        #else
            return mkdir(path.c_str(), 0755) == 0;
        #endif
    }
    return (info.st_mode & S_IFDIR) != 0;
}


// =================================================================
// START: Logic from RFDynamic_algorithm.h (for JobSizePool)
// =================================================================

class JobSizePool {
private:
    std::vector<int> pool;  // All completed job sizes
    std::mt19937 rng;
    
public:
    JobSizePool() {
        std::random_device rd;
        rng.seed(rd());
    }
    
    void add_job_size(int size) {
        pool.push_back(size);
    }
    
    // **UNUSED but kept for reference**
    std::vector<int> get_recent(int n) const {
        if (pool.empty()) return {};
        int start_idx = std::max(0, static_cast<int>(pool.size()) - n);
        return std::vector<int>(pool.begin() + start_idx, pool.end());
    }
    
    std::vector<int> sample_random(int n) {
        if (pool.empty() || n <= 0) return {};
        
        std::vector<int> samples;
        std::uniform_int_distribution<size_t> dist(0, pool.size() - 1);
        
        for (int i = 0; i < n; i++) {
            samples.push_back(pool[dist(rng)]);
        }
        return samples;
    }
    
    size_t size() const {
        return pool.size();
    }
    
    // =================================================================
    // >>> START FIX: Modified get_simulation_set
    // Uses actual recent completions first, then samples from pool
    // =================================================================
    std::vector<int> get_simulation_set(int target_size, const std::vector<int>& recent_completions) {
        if (target_size <= 0) return {};
        
        std::vector<int> result;
        
        // 1. Take as many recent completions as needed, up to target_size
        int take = std::min(static_cast<int>(recent_completions.size()), target_size);
        if (take > 0) {
            result.insert(result.end(), recent_completions.begin(), recent_completions.begin() + take);
        }
        
        // 2. If we still need more, sample randomly from the *entire* pool
        int needed = target_size - result.size();
        if (needed > 0 && !pool.empty()) {
            auto samples = sample_random(needed);
            result.insert(result.end(), samples.begin(), samples.end());
        }
        
        return result;
    }
    // =================================================================
    // >>> END FIX
    // =================================================================
};

// Simulate FCFS on a job pool with known sizes
inline double simulate_fcfs_l2(const std::vector<int>& job_sizes) {
    if (job_sizes.empty()) return 0.0;
    std::vector<Job> sim_jobs;
    for (size_t i = 0; i < job_sizes.size(); i++) {
        Job j; j.arrival_time = 0; j.job_size = job_sizes[i];
        j.job_index = i; j.remaining_time = job_sizes[i];
        sim_jobs.push_back(j);
    }
    return Fcfs_Optimized(sim_jobs).l2_norm_flow_time;
}

// Simulate RMLF on a job pool with known sizes
inline double simulate_rmlf_l2(const std::vector<int>& job_sizes) {
    if (job_sizes.empty()) return 0.0;
    std::vector<Job> sim_jobs;
    for (size_t i = 0; i < job_sizes.size(); i++) {
        Job j; j.arrival_time = 0; j.job_size = job_sizes[i];
        j.job_index = i; j.remaining_time = job_sizes[i];
        sim_jobs.push_back(j);
    }
    return RMLF_algorithm(sim_jobs).l2_norm_flow_time;
}

// =================================================================
// END: Logic from RFDynamic_algorithm.h
// =================================================================


// Result struct for our new algorithm
struct DynamicRFResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
    std::vector<std::string> algorithm_history;
};

// Get analysis base directory
std::string get_analysis_base_dir() {
    const char* base = std::getenv("ULTIMUS_ANALYSIS_DIR");
    if (base) return std::string(base);
    return "./Analysis/RFDynamic_analysis";
}

// Save analysis results for all file types (avg, random, softrandom, combination)
void save_analysis_results_RF(const std::string& input_file_path, int nJobsPerRound, int k,
                              const std::vector<std::string>& algorithm_history, int total_rounds) {
    if (input_file_path.empty() || algorithm_history.empty()) {
        return;
    }

    size_t last_slash = input_file_path.find_last_of('/');
    std::string dir_path = input_file_path.substr(0, last_slash);
    std::string folder_name = dir_path.substr(dir_path.find_last_of('/') + 1);
    std::string filename = input_file_path.substr(last_slash + 1);

    std::string main_dir = get_analysis_base_dir();
    std::string sub_folder;
    int version = extract_version_from_path(folder_name);

    NewAvgParams params;
    params.arrival_rate = -1;
    params.bp_L = -1;
    params.bp_H = -1;

    if (folder_name.find("avg_") == 0) {
        std::regex avg_type_pattern("avg_(\\d+)");
        std::smatch match;
        std::string avg_type = "30";
        if (std::regex_search(folder_name, match, avg_type_pattern)) {
            avg_type = match[1];
        }
        sub_folder = "avg_" + avg_type;

        params = parse_new_avg_filename(filename);
        if (params.arrival_rate < 0) {
            AvgParams old_params = parse_avg_filename(filename);
            if (old_params.arrival_rate >= 0) {
                params.arrival_rate = old_params.arrival_rate;
                params.bp_L = old_params.bp_L;
                params.bp_H = old_params.bp_H;
            }
        }
    } else if (input_file_path.find("random") != std::string::npos ||
               input_file_path.find("Random") != std::string::npos) {
        if (input_file_path.find("softrandom") != std::string::npos) {
            sub_folder = "Softrandom";
        } else {
            sub_folder = "Random";
        }
        params.arrival_rate = 30.0;
        params.bp_L = 16.77;
        params.bp_H = 64;
    } else if (input_file_path.find("combination") != std::string::npos) {
        sub_folder = "Combination";
        params.arrival_rate = 30.0;
        params.bp_L = 16.77;
        params.bp_H = 64;
    } else if (input_file_path.find("fix") != std::string::npos) {
        sub_folder = "Fix";
        params.arrival_rate = 30.0;
        params.bp_L = 16.77;
        params.bp_H = 64;
    } else {
        return;
    }

    if (params.arrival_rate < 0) {
        return;
    }

    std::string mode_folder = "k_" + std::to_string(k);
    std::string folder_path = main_dir + "/" + sub_folder + "/" + mode_folder;

    // Create all directories recursively (like mkdir -p)
    create_directories_recursive(folder_path);

    int rmlf_count = 0, fcfs_count = 0;
    for (const auto& algo : algorithm_history) {
        if (algo == "RMLF") rmlf_count++;
        else if (algo == "FCFS") fcfs_count++;
    }

    int total = algorithm_history.size();
    double rmlf_percentage = total > 0 ? (rmlf_count * 100.0 / total) : 0.0;
    double fcfs_percentage = total > 0 ? (fcfs_count * 100.0 / total) : 0.0;

    std::string output_file;
    if (version >= 0) {
        output_file = folder_path + "/RFDynamic_" + sub_folder + "_nJobsPerRound_" +
                     std::to_string(nJobsPerRound) + "_k_" + std::to_string(k) +
                     "_round_" + std::to_string(version) + ".csv";
    } else {
        output_file = folder_path + "/RFDynamic_" + sub_folder + "_nJobsPerRound_" +
                     std::to_string(nJobsPerRound) + "_k_" + std::to_string(k) + ".csv";
    }

    bool write_header = !std::ifstream(output_file).good();

    std::ofstream out(output_file, std::ios::app);
    if (write_header) {
        out << "arrival_rate,bp_L,bp_H,FCFS_percentage,RMLF_percentage,total_rounds\n";
    }
    out << std::fixed << std::setprecision(2);
    out << params.arrival_rate << "," << params.bp_L << "," << params.bp_H << ","
        << fcfs_percentage << "," << rmlf_percentage << "," << total_rounds << "\n";
}


// Dynamic RF (RMLF/FCFS) non-clairvoyant algorithm
DynamicRFResult DYNAMIC_RF(std::vector<Job> jobs, int nJobsPerRound, int k,
                           const std::string& input_file_name = "") {
    
    const size_t INITIAL_FCFS_COUNT = 100; // Phase 1 goal
    
    if (jobs.empty()) {
        return {0.0, 0.0, 0.0, {}};
    }
    
    // Sort jobs by arrival time once
    std::stable_sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        return a.arrival_time < b.arrival_time;
    });
    
    // Master list to track completions
    std::vector<Job> job_pool_tracking = jobs;
    for (auto& job : job_pool_tracking) {
        job.completion_time = -1; // Initialize all as not completed
    }
    
    JobSizePool job_pool;
    std::vector<std::string> algorithm_history;
    std::vector<int> completed_sizes_this_round;
    
    // =================================================================
    // >>> START FIX: Added history of completed sizes per round
    // =================================================================
    std::vector<std::vector<int>> round_completions_history;
    // =================================================================
    // >>> END FIX
    // =================================================================
    
    size_t completion_count = 0;
    size_t next_job_idx = 0; // Index into the *sorted* 'jobs' vector
    int current_round = 0;
    
    // ========== PHASE 1: FCFS for first 100 completions ==========
    {
        safe_cout("Phase 1: Running FCFS for first " + std::to_string(INITIAL_FCFS_COUNT) + " completions...\n");
        std::vector<Job> phase1_jobs = jobs; 
        Fcfs_Optimized(phase1_jobs); 
        
        std::vector<std::pair<long long, size_t>> completed_with_time;
        for (size_t i = 0; i < phase1_jobs.size(); i++) {
            if (phase1_jobs[i].completion_time > 0) {
                completed_with_time.push_back({phase1_jobs[i].completion_time, i});
            }
        }
        
        if (completed_with_time.size() < INITIAL_FCFS_COUNT) {
            safe_cout("FATAL ERROR: Phase 1 FCFS run completed less than " + 
                      std::to_string(INITIAL_FCFS_COUNT) + " jobs. Aborting.\n");
            return {0.0, 0.0, 0.0, {}};
        }
        
        std::sort(completed_with_time.begin(), completed_with_time.end());
        
        long long phase1_end_time = 0;
        completed_sizes_this_round.clear(); // Prepare to store Phase 1's completions
        
        for (size_t i = 0; i < INITIAL_FCFS_COUNT; i++) {
            size_t job_idx_in_phase1 = completed_with_time[i].second;
            Job& job = phase1_jobs[job_idx_in_phase1];
            
            job_pool_tracking[job.job_index] = job; 
            job_pool.add_job_size(job.job_size);
            completed_sizes_this_round.push_back(job.job_size); // Store size for history
            completion_count++;
            phase1_end_time = job.completion_time;
        }
        
        // Save Phase 1's completions as Round 1 history
        round_completions_history.push_back(completed_sizes_this_round);
        
        for (size_t i = 0; i < jobs.size(); i++) {
            if (jobs[i].arrival_time > phase1_end_time) {
                next_job_idx = i;
                break;
            }
            if (i == jobs.size() - 1) next_job_idx = jobs.size(); 
        }
        
        algorithm_history.push_back("FCFS");
        current_round = 1;
        safe_cout("Phase 1 complete: " + std::to_string(completion_count) + " jobs finished at time " 
                 + std::to_string(phase1_end_time) + "\n");
        safe_cout("  Pool size: " + std::to_string(job_pool.size()) + "\n");
    }
    
    // ========== PHASE 2: Dynamic switching every 'nJobsPerRound' arrivals ==========
    safe_cout("\nPhase 2: Dynamic switching every " + std::to_string(nJobsPerRound) + " arrivals...\n");
    
    std::vector<Job> accumulated_jobs;
    bool use_fcfs = true; 
    
    while (next_job_idx < jobs.size()) {
        current_round++;
        completed_sizes_this_round.clear(); // Clear for harvesting this round's completions
        
        size_t batch_end = std::min(next_job_idx + nJobsPerRound, jobs.size());
        size_t batch_size = batch_end - next_job_idx;
        
        safe_cout("\n  [Round " + std::to_string(current_round) + "] Processing jobs " 
                 + std::to_string(next_job_idx) + " to " + std::to_string(batch_end - 1) 
                 + " (batch size: " + std::to_string(batch_size) + " arrivals)\n");
        
        // =================================================================
        // >>> START FIX: Correct simulation and mode-gating logic
        // =================================================================
        
        // k = number of past batches to look back (0 means all)
        // No mode fallback needed - just use min(k, available_rounds)
        int rounds_needed = (k <= 0) ? static_cast<int>(round_completions_history.size()) : k;
        int target_size = (k <= 0) ? static_cast<int>(job_pool.size()) : rounds_needed * nJobsPerRound;

        // 3. Build simulation set from *actual* past completions
        std::vector<int> recent_completions;
        int rounds_to_get = std::min(static_cast<int>(round_completions_history.size()), rounds_needed);
        
        for (int i = 0; i < rounds_to_get; i++) {
            // Get most recent rounds first
            const auto& round_data = round_completions_history[round_completions_history.size() - 1 - i];
            recent_completions.insert(recent_completions.end(), round_data.begin(), round_data.end());
        }

        // 4. Get the final simulation set
        // This will take all `recent_completions` (up to target_size)
        // and then sample from the pool if `needed > 0`.
        std::vector<int> simulation_set = job_pool.get_simulation_set(
            target_size, recent_completions
        );

        // =================================================================
        // >>> END FIX
        // =================================================================
        
        if (!simulation_set.empty()) {
            double fcfs_l2 = simulate_fcfs_l2(simulation_set);
            double rmlf_l2 = simulate_rmlf_l2(simulation_set);
            use_fcfs = (fcfs_l2 <= rmlf_l2);
            
            safe_cout("    Simulation (k=" + std::to_string(k) +
                     ", hist_rounds " + std::to_string(rounds_to_get) +
                     ", sim_size " + std::to_string(simulation_set.size()) +
                     "): FCFS L2=" + std::to_string(fcfs_l2) + ", RMLF L2=" + std::to_string(rmlf_l2) +
                     " -> Chose " + (use_fcfs ? "FCFS" : "RMLF") + "\n");
        } else {
            use_fcfs = true; 
            safe_cout("    No simulation data, defaulting to FCFS\n");
        }
        
        algorithm_history.push_back(use_fcfs ? "FCFS" : "RMLF");
        
        // --- Execution (Re-run all history up to batch_end) ---
        accumulated_jobs.clear();
        for (size_t i = 0; i < batch_end; i++) {
            accumulated_jobs.push_back(jobs[i]);
        }
        
        int prev_completion_count = completion_count;
        
        if (use_fcfs) {
            Fcfs_Optimized(accumulated_jobs);
        } else {
            RMLF_algorithm(accumulated_jobs);
        }
        
        // --- Harvest Results ---
        for (size_t i = 0; i < accumulated_jobs.size(); i++) {
            auto& job = accumulated_jobs[i];
            if (job.completion_time > 0 && 
                (job_pool_tracking[job.job_index].completion_time <= 0)) {
                
                job_pool_tracking[job.job_index] = job;
                job_pool.add_job_size(job.job_size);
                completed_sizes_this_round.push_back(job.job_size); // Store for history
                completion_count++;
            }
        }
        
        // Store this round's completions for future simulations
        round_completions_history.push_back(completed_sizes_this_round);
        
        int new_completions = completion_count - prev_completion_count;
        safe_cout("    Completed " + std::to_string(new_completions) + " NEW jobs in this round\n");
        safe_cout("    Total completed: " + std::to_string(completion_count) + "/" + std::to_string(jobs.size())
                 + ", Pool size: " + std::to_string(job_pool.size()) + "\n");
        
        next_job_idx = batch_end;
    }
    
    safe_cout("\nSimulation complete!\n");
    
    // --- Final Metrics ---
    long double sum_flow = 0.0;
    long double sum_sq = 0.0;
    long long max_flow = 0;
    int valid_jobs = 0;
    
    for (const auto& job : job_pool_tracking) {
        if (job.completion_time > 0) {
            long long flow = job.completion_time - job.arrival_time;
            if (flow >= job.job_size) {
                sum_flow += flow;
                sum_sq += static_cast<long double>(flow) * flow;
                max_flow = std::max(max_flow, flow);
                valid_jobs++;
            }
        }
    }
    
    if (valid_jobs != (int)jobs.size()) {
         safe_cout("WARNING: Only " + std::to_string(valid_jobs) + "/" + std::to_string(jobs.size()) + " jobs completed validly.\n");
    }
    
    double avg_flow = valid_jobs > 0 ? (double)(sum_flow / valid_jobs) : 0.0;
    double l2_norm = std::sqrt((double)sum_sq);
    
    safe_cout("Results: avg_flow=" + std::to_string(avg_flow) + ", L2=" + std::to_string(l2_norm) 
             + ", max_flow=" + std::to_string(max_flow) + " (from " + std::to_string(valid_jobs) + " jobs)\n");
    
    if (!input_file_name.empty()) {
        save_analysis_results_RF(input_file_name, nJobsPerRound, k,
                                 algorithm_history, current_round); // Use final current_round
    }
    
    return {avg_flow, l2_norm, static_cast<double>(max_flow), algorithm_history};
}


// =================================================================
// START: Wrappers and main()
// (Unchanged, but now call DYNAMIC_RF)
// =================================================================

// For avg folders
std::map<int, double> run_all_modes_for_file_normal(std::vector<Job> jobs, int nJobsPerRound,
                                                    const std::vector<int>& k_values) {
    std::map<int, double> mode_results;
    std::mutex results_mutex;
    std::vector<std::thread> threads;

    for (int k_val : k_values) {
        threads.emplace_back([&, k_val]() {
            std::vector<Job> jobs_copy = jobs;
            DynamicRFResult result = DYNAMIC_RF(jobs_copy, nJobsPerRound, k_val);

            {
                std::lock_guard<std::mutex> lock(results_mutex);
                mode_results[k_val] = result.l2_norm_flow_time;

            }

            std::stringstream ss;
            ss << "    k=" << k_val << ": L2 norm = " << std::fixed
               << std::setprecision(4) << result.l2_norm_flow_time << std::endl;
            safe_cout(ss.str());
        });
    }

    for (auto& thread : threads) {
        thread.join();
    }
    return mode_results;
}

// For random/softrandom folders
std::pair<std::map<int, double>, std::map<int, double>>
run_all_modes_for_file_frequency(std::vector<Job> jobs, int nJobsPerRound,
                                 const std::vector<int>& k_values) {
    std::map<int, double> mode_results;
    std::map<int, double> max_flow_results;
    std::mutex results_mutex;
    std::vector<std::thread> threads;

    for (int k_val : k_values) {
        threads.emplace_back([&, k_val]() {
            std::vector<Job> jobs_copy = jobs;
            DynamicRFResult result = DYNAMIC_RF(jobs_copy, nJobsPerRound, k_val, "");

            {
                std::lock_guard<std::mutex> lock(results_mutex);
                mode_results[k_val] = result.l2_norm_flow_time;
                max_flow_results[k_val] = result.max_flow_time;
            }

            std::stringstream ss;
            ss << "    k=" << k_val << ": L2 norm = " << std::fixed
               << std::setprecision(4) << result.l2_norm_flow_time
               << ", Max flow = " << result.max_flow_time << std::endl;
            safe_cout(ss.str());
        });
    }

    for (auto& thread : threads) {
        thread.join();
    }
    return std::make_pair(mode_results, max_flow_results);
}

// Parse comma-separated k values list
std::vector<int> parse_k_values(const std::string& k_str) {
    std::vector<int> k_values;
    std::stringstream ss(k_str);
    std::string token;

    while (std::getline(ss, token, ',')) {
        token.erase(0, token.find_first_not_of(" \t"));
        token.erase(token.find_last_not_of(" \t") + 1);

        try {
            int kv = std::stoi(token);
            if (kv >= 0) {
                k_values.push_back(kv);
            } else {
                std::cerr << "WARNING: Invalid k=" << kv << " (must be >= 0), skipping\n";
            }
        } catch (const std::exception& e) {
            std::cerr << "WARNING: Invalid k value '" << token << "', skipping\n";
        }
    }

    std::set<int> unique_k(k_values.begin(), k_values.end());
    k_values.assign(unique_k.begin(), unique_k.end());
    return k_values;
}

// Wrapper function for experiments (simple single-parameter interface)
DynamicRFResult RFDynamic(std::vector<Job> jobs) {
    return DYNAMIC_RF(jobs, 100, 1, "");  // Default B=100, k=1
}

int main(int argc, char* argv[]) {
    int batch_size = 100;
    std::vector<int> k_values = {1, 2, 4, 8, 16, 0};

    if (argc > 1) {
        if (std::string(argv[1]) == "-h" || std::string(argv[1]) == "--help") {
            std::cout << "Usage: ./RFDynamic [batch_size] [k_values]\n";
            std::cout << "  batch_size: number of jobs per batch (default: 100)\n";
            std::cout << "  k_values: comma-separated lookback values, 0=all (default: 1,2,4,8,16,0)\n";
            return 0;
        }

        try {
            batch_size = std::atoi(argv[1]);
            if (batch_size <= 0) {
                std::cerr << "ERROR: batch_size must be positive\n";
                return 1;
            }
        } catch (const std::exception& e) {
            std::cerr << "ERROR: Invalid batch_size value\n";
            return 1;
        }
    }

    if (argc > 2) {
        k_values = parse_k_values(argv[2]);
        if (k_values.empty()) {
            std::cerr << "ERROR: No valid k values specified\n";
            return 1;
        }
    }

    std::string data_dir = "./data";
    std::string output_dir = "./algorithm_result/RFDynamic_result";

    unsigned int num_threads = std::thread::hardware_concurrency();
    if (num_threads == 0) num_threads = 4;

    std::cout << "============================================================\n";
    std::cout << "Starting RFDynamic (RMLF/FCFS) batch processing:\n";
    std::cout << "  Data directory: " << data_dir << "\n";
    std::cout << "  Output directory: " << output_dir << "\n";
    std::cout << "  batch_size (checkpoint): " << batch_size << "\n";
    std::cout << "  Hardware threads available: " << num_threads << "\n";
    std::cout << "  k values: ";
    for (size_t i = 0; i < k_values.size(); i++) {
        std::cout << k_values[i];
        if (i < k_values.size() - 1) std::cout << ", ";
    }
    std::cout << "\n";
    std::cout << "============================================================\n";
    
    ensure_directory_exists(output_dir);
    
    std::vector<std::thread> main_threads;
    std::cout << "\nLaunching parallel processing threads...\n\n";
    
    // Thread 1: Process avg files
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 1] Processing avg files...\n");
        safe_cout("========================================\n");

        auto avg_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                             const std::string& input_file_path,
                             const std::vector<int>& k_values) {
            // Pass input file path for analysis
            // Returns map<int, pair<double, double>> where pair = (L2_norm, max_flow_time)
            std::map<int, std::pair<double, double>> mode_results;
            std::mutex results_mutex;
            std::vector<std::thread> threads;

            for (int k_val : k_values) {
                threads.emplace_back([&, k_val]() {
                    std::vector<Job> jobs_copy = jobs;
                    DynamicRFResult result = DYNAMIC_RF(jobs_copy, nJobsPerRound, k_val, input_file_path);

                    {
                        std::lock_guard<std::mutex> lock(results_mutex);
                        mode_results[k_val] = std::make_pair(result.l2_norm_flow_time, result.max_flow_time);
                    }
                });
            }

            for (auto& thread : threads) {
                thread.join();
            }
            return mode_results;
        };

        process_avg_folders_multimode_RF(avg_wrapper, data_dir, output_dir,
                                      batch_size, k_values, cout_mutex);
        safe_cout("\n[Thread 1] Avg files completed!\n\n");
    });
    
    // Thread 2: Process Bounded Pareto random files using multimode function
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 2] Processing Bounded Pareto random files...\n");
        safe_cout("========================================\n");

        auto random_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                const std::vector<int>& k_values) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, k_values);
        };

        process_bounded_pareto_random_folders_multimode_RF(random_wrapper, data_dir, output_dir,
                                        batch_size, k_values, cout_mutex);
        safe_cout("\n[Thread 2] Bounded Pareto random files completed!\n\n");
    });

    // Thread 3: Process Normal random files using multimode function
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 3] Processing Normal random files...\n");
        safe_cout("========================================\n");

        auto random_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                const std::vector<int>& k_values) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, k_values);
        };

        process_normal_random_folders_multimode_RF(random_wrapper, data_dir, output_dir,
                                        batch_size, k_values, cout_mutex);
        safe_cout("\n[Thread 3] Normal random files completed!\n\n");
    });

    // Thread 4: Process Bounded Pareto softrandom files using multimode function
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 4] Processing Bounded Pareto softrandom files...\n");
        safe_cout("========================================\n");

        auto softrandom_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                    const std::vector<int>& k_values) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, k_values);
        };

        process_bounded_pareto_softrandom_folders_multimode_RF(softrandom_wrapper, data_dir, output_dir,
                                            batch_size, k_values, cout_mutex);
        safe_cout("\n[Thread 4] Bounded Pareto softrandom files completed!\n\n");
    });

    // Thread 5: Process Normal softrandom files using multimode function
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 5] Processing Normal softrandom files...\n");
        safe_cout("========================================\n");

        auto softrandom_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                    const std::vector<int>& k_values) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, k_values);
        };

        process_normal_softrandom_folders_multimode_RF(softrandom_wrapper, data_dir, output_dir,
                                            batch_size, k_values, cout_mutex);
        safe_cout("\n[Thread 5] Normal softrandom files completed!\n\n");
    });

    // Thread 6: Process Bounded Pareto combination random files
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 6] Processing Bounded Pareto combination random files...\n");
        safe_cout("========================================\n");

        auto combination_random_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                            const std::vector<int>& k_values) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, k_values);
        };

        process_bounded_pareto_combination_random_folders_multimode_RF(combination_random_wrapper, data_dir, output_dir,
                                                       batch_size, k_values, cout_mutex);
        safe_cout("\n[Thread 6] Bounded Pareto combination random files completed!\n\n");
    });

    // Thread 7: Process Normal combination random files
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 7] Processing Normal combination random files...\n");
        safe_cout("========================================\n");

        auto combination_random_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                            const std::vector<int>& k_values) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, k_values);
        };

        process_normal_combination_random_folders_multimode_RF(combination_random_wrapper, data_dir, output_dir,
                                                       batch_size, k_values, cout_mutex);
        safe_cout("\n[Thread 7] Normal combination random files completed!\n\n");
    });

    // Thread 8: Process Bounded Pareto combination softrandom files
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 8] Processing Bounded Pareto combination softrandom files...\n");
        safe_cout("========================================\n");

        auto combination_softrandom_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                                const std::vector<int>& k_values) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, k_values);
        };

        process_bounded_pareto_combination_softrandom_folders_multimode_RF(combination_softrandom_wrapper, data_dir, output_dir,
                                                            batch_size, k_values, cout_mutex);
        safe_cout("\n[Thread 8] Bounded Pareto combination softrandom files completed!\n\n");
    });

    // Thread 9: Process Normal combination softrandom files
    main_threads.emplace_back([&]() {
        safe_cout("========================================\n");
        safe_cout("[Thread 9] Processing Normal combination softrandom files...\n");
        safe_cout("========================================\n");

        auto combination_softrandom_wrapper = [](std::vector<Job> jobs, int nJobsPerRound,
                                                const std::vector<int>& k_values) {
            return run_all_modes_for_file_frequency(jobs, nJobsPerRound, k_values);
        };

        process_normal_combination_softrandom_folders_multimode_RF(combination_softrandom_wrapper, data_dir, output_dir,
                                                            batch_size, k_values, cout_mutex);
        safe_cout("\n[Thread 9] Normal combination softrandom files completed!\n\n");
    });

    for (auto& thread : main_threads) {
        thread.join();
    }
    
    std::cout << "\n============================================================\n";
    std::cout << "All Dynamic RF processing completed successfully!\n";
    std::cout << "============================================================\n";

    return 0;
}