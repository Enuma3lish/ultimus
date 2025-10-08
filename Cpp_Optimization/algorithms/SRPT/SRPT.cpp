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

// ============ SRPT Scheduler ============

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
    
    // Sort by arrival time
    std::sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        return a.arrival_time < b.arrival_time;
    });
    
    long long t = 0;  // Use long long to avoid overflow
    int i = 0;
    std::vector<Job*> waiting;
    Job* current = nullptr;
    std::vector<Job*> completed;
    
    while (completed.size() < total) {
        // Admit arrivals at time t
        while (i < total && jobs[i].arrival_time <= t) {
            jobs[i].remaining_time = jobs[i].job_size;
            jobs[i].start_time = -1;
            jobs[i].completion_time = -1;
            waiting.push_back(&jobs[i]);
            i++;
        }
        
        // If there's a current job, consider preemption by pushing it back to waiting
        if (current != nullptr) {
            waiting.push_back(current);
            current = nullptr;
        }
        
        // Pick SRPT job if available
        if (!waiting.empty()) {
            Job* picked = srpt_select_next_job_optimized(waiting);
            
            // FIX: Find the selected job by POINTER comparison
            int sel_idx = -1;
            for (int k = 0; k < waiting.size(); k++) {
                if (waiting[k] == picked) {  // Direct pointer comparison
                    sel_idx = k;
                    break;
                }
            }
            
            if (sel_idx == -1) {
                // This should never happen - indicates a serious bug
                std::cerr << "ERROR: Selected job not found in waiting queue!" << std::endl;
                std::cerr << "  Job index: " << picked->job_index << std::endl;
                std::cerr << "  Remaining time: " << picked->remaining_time << std::endl;
                std::cerr << "  Waiting queue size: " << waiting.size() << std::endl;
                
                // Try to recover by using the first job
                sel_idx = 0;
            }
            
            current = waiting[sel_idx];
            waiting.erase(waiting.begin() + sel_idx);
            
            if (current->start_time == -1) {
                // Validate time consistency
                if (t < current->arrival_time) {
                    std::cerr << "WARNING: Time " << t << " < arrival " 
                              << current->arrival_time << " for job " 
                              << current->job_index << std::endl;
                    t = current->arrival_time;
                }
                current->start_time = t;
            }
            
            // Determine next arrival time
            long long next_arrival_t = (i < total) ? jobs[i].arrival_time : -1;
            
            if (next_arrival_t == -1) {
                // No more arrivals: run to completion
                t += current->remaining_time;
                current->completion_time = t;
                current->remaining_time = 0;
                completed.push_back(current);
                current = nullptr;
                continue;
            } else {
                // Check if new arrival is at current time
                if (next_arrival_t == t) {
                    // New arrival right now - don't execute, reconsider scheduling
                    continue;
                }
                
                // Run until either next arrival or completion
                long long delta = std::min((long long)current->remaining_time, 
                                          next_arrival_t - t);
                
                // Safety check: delta should be positive
                if (delta <= 0) {
                    std::cerr << "WARNING: Non-positive delta: " << delta << std::endl;
                    continue;
                }
                
                t += delta;
                current->remaining_time -= delta;
                
                if (current->remaining_time == 0) {
                    current->completion_time = t;
                    completed.push_back(current);
                    current = nullptr;
                }
                continue;
            }
        }
        
        // If nothing waiting, jump to next arrival
        if (i < total) {
            t = std::max(t, (long long)jobs[i].arrival_time);
        } else {
            break;
        }
    }
    
    // FIX: Calculate metrics with proper types to avoid overflow
    std::vector<long long> flows;
    flows.reserve(completed.size());
    
    for (Job* c : completed) {
        long long flow = (long long)(c->completion_time - c->arrival_time);
        
        // Validation
        if (flow < c->job_size) {
            std::cerr << "ERROR: Flow time " << flow << " < job size " 
                      << c->job_size << " for job " << c->job_index << std::endl;
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
    std::cout << "Starting SRPT batch processing (FIXED VERSION):\n";
    std::cout << "  Data directory: " << data_dir << "\n";
    std::cout << "  Output directory: " << output_dir << "\n";
    std::cout << "  Fix: Proper immediate preemption on arrival\n";
    std::cout << "============================================================\n";
    
    create_directory(output_dir);
    
    std::cout << "\n========================================\n";
    std::cout << "Processing avg files...\n";
    std::cout << "========================================\n";
    process_avg_folders(SRPT, "SRPT", data_dir, output_dir);
    
    std::cout << "\n========================================\n";
    std::cout << "Processing random files...\n";
    std::cout << "========================================\n";
    process_random_folders(SRPT, "SRPT", data_dir, output_dir);
    
    std::cout << "\n========================================\n";
    std::cout << "Processing softrandom files...\n";
    std::cout << "========================================\n";
    process_softrandom_folders(SRPT, "SRPT", data_dir, output_dir);
    
    std::cout << "\n============================================================\n";
    std::cout << "SRPT batch processing completed successfully!\n";
    std::cout << "============================================================\n";
    
    return 0;
}