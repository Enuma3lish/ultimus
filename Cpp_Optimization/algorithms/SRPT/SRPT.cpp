#include <iostream>
#include <vector>
#include <cmath>
#include <algorithm>
#include "SRPT_Selector.h"
#include "utils.h"
#include "_run.h"
#include "_run_random.h"
#include "process_avg_folders.h"
#include "process_random_folders.h"
#include "process_softrandom_folders.h"

// ============ SRPT Scheduler - FIXED VERSION ============

struct SRPTResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
};

SRPTResult SRPT(std::vector<Job>& jobs) {
    int total = jobs.size();
    if (total == 0) {
        return {0.0, 0.0, 0.0};
    }

    // Sort by arrival time, then by job size for tie-breaking
    std::sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        if (a.arrival_time != b.arrival_time)
            return a.arrival_time < b.arrival_time;
        if (a.job_size != b.job_size)
            return a.job_size < b.job_size;
        return a.job_index < b.job_index;
    });

    // Initialize all jobs
    for (int i = 0; i < total; i++) {
        jobs[i].remaining_time = jobs[i].job_size;
        jobs[i].start_time = -1;
        jobs[i].completion_time = -1;
    }

    long long t = 0;  // Current time
    int next_arrival_idx = 0;  // Index of next job to arrive
    std::vector<Job*> waiting;  // Jobs waiting to be processed
    std::vector<Job*> completed;  // Completed jobs

    while (completed.size() < total) {
        // Step 1: Admit ALL jobs that have arrived by time t
        while (next_arrival_idx < total && jobs[next_arrival_idx].arrival_time <= t) {
            waiting.push_back(&jobs[next_arrival_idx]);
            next_arrival_idx++;
        }

        // Step 2: If no jobs are waiting, jump to next arrival
        if (waiting.empty()) {
            if (next_arrival_idx < total) {
                t = jobs[next_arrival_idx].arrival_time;
            } else {
                break;  // All jobs completed
            }
            continue;
        }

        // Step 3: Select job with shortest remaining time (SRPT policy)
        Job* current = srpt_select_next_job_optimized(waiting);

        // Remove selected job from waiting queue
        auto it = std::find(waiting.begin(), waiting.end(), current);
        if (it != waiting.end()) {
            waiting.erase(it);
        } else {
            std::cerr << "ERROR: Selected job not found in waiting queue!" << std::endl;
            break;
        }

        // Record start time if this is the first time job is executed
        if (current->start_time == -1) {
            current->start_time = t;
        }

        // Step 4: Determine how long to execute the current job
        long long exec_time;

        if (next_arrival_idx < total) {
            // There are more jobs arriving
            long long next_arrival_t = jobs[next_arrival_idx].arrival_time;

            // Execute until either:
            // - Job completes (remaining_time runs out)
            // - Next job arrives (might preempt if it has shorter time)
            exec_time = std::min((long long)current->remaining_time,
                                next_arrival_t - t);
        } else {
            // No more arrivals, run to completion
            exec_time = current->remaining_time;
        }

        // Safety check
        if (exec_time <= 0) {
            std::cerr << "WARNING: Non-positive exec_time: " << exec_time
                      << " at time " << t << std::endl;
            std::cerr << "  Current job: idx=" << current->job_index
                      << " remaining=" << current->remaining_time << std::endl;
            if (next_arrival_idx < total) {
                std::cerr << "  Next arrival at: " << jobs[next_arrival_idx].arrival_time << std::endl;
            }
            // Force progress
            exec_time = 1;
        }

        // Step 5: Execute the job
        t += exec_time;
        current->remaining_time -= exec_time;

        // Step 6: Check if job completed
        if (current->remaining_time == 0) {
            // Job finished
            current->completion_time = t;
            completed.push_back(current);
        } else {
            // Job not finished, put back in waiting queue for re-evaluation
            // (will be preempted if a shorter job arrives)
            waiting.push_back(current);
        }
    }

    // Validate all jobs completed
    if (completed.size() != total) {
        std::cerr << "ERROR: Only " << completed.size() << " of " << total
                  << " jobs completed!" << std::endl;
    }

    // Calculate metrics
    std::vector<long long> flows;
    flows.reserve(completed.size());

    for (Job* c : completed) {
        long long flow = (long long)(c->completion_time - c->arrival_time);

        // Validation
        if (flow < c->job_size) {
            std::cerr << "ERROR: Flow time " << flow << " < job size "
                      << c->job_size << " for job " << c->job_index << std::endl;
            std::cerr << "  Arrival: " << c->arrival_time
                      << ", Completion: " << c->completion_time << std::endl;
        }
        if (c->start_time < c->arrival_time) {
            std::cerr << "ERROR: Start time " << c->start_time
                      << " < arrival time " << c->arrival_time
                      << " for job " << c->job_index << std::endl;
        }

        flows.push_back(flow);
    }

    int n = flows.size();
    if (n == 0) return {0.0, 0.0, 0.0};

    double avg_flow = 0.0;
    double l2 = 0.0;
    long long max_flow = 0;

    for (long long f : flows) {
        avg_flow += f;
        l2 += (double)f * f;  // Cast to double before multiplication
        max_flow = std::max(max_flow, f);
    }

    avg_flow /= n;
    l2 = std::sqrt(l2);

    return {avg_flow, l2, static_cast<double>(max_flow)};
}

// ============ Main Function ============

int main() {
    std::string data_dir = "/home/melowu/Work/ultimus/data";
    std::string output_dir = "/home/melowu/Work/ultimus/SRPT_result";

    std::cout << "============================================================\n";
    std::cout << "Starting SRPT batch processing (FIXED VERSION v2):\n";
    std::cout << "  Data directory: " << data_dir << "\n";
    std::cout << "  Output directory: " << output_dir << "\n";
    std::cout << "  FIXES APPLIED:\n";
    std::cout << "    1. Removed unconditional preemption\n";
    std::cout << "    2. Proper event-driven scheduling\n";
    std::cout << "    3. Job only returns to queue if not completed\n";
    std::cout << "    4. Fixed simultaneous arrival handling\n";
    std::cout << "============================================================\n";

    create_directory(output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing avg files...\n";
    std::cout << "========================================\n";
    process_avg_folders(SRPT, "SRPT", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Bounded Pareto random files...\n";
    std::cout << "========================================\n";
    process_bounded_pareto_random_folders(SRPT, "SRPT", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Normal random files...\n";
    std::cout << "========================================\n";
    process_normal_random_folders(SRPT, "SRPT", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Bounded Pareto softrandom files...\n";
    std::cout << "========================================\n";
    process_bounded_pareto_softrandom_folders(SRPT, "SRPT", data_dir, output_dir);

    std::cout << "\n========================================\n";
    std::cout << "Processing Normal softrandom files...\n";
    std::cout << "========================================\n";
    process_normal_softrandom_folders(SRPT, "SRPT", data_dir, output_dir);

    std::cout << "\n============================================================\n";
    std::cout << "SRPT batch processing completed successfully!\n";
    std::cout << "============================================================\n";

    return 0;
}
