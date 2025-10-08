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
    
    int t = 0;
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
            
            // Find the selected job in waiting queue
            int sel_idx = -1;
            for (int k = 0; k < waiting.size(); k++) {
                if (waiting[k]->remaining_time == picked->remaining_time &&
                    waiting[k]->arrival_time == picked->arrival_time &&
                    waiting[k]->job_index == picked->job_index) {
                    sel_idx = k;
                    break;
                }
            }
            
            if (sel_idx != -1) {
                current = waiting[sel_idx];
                waiting.erase(waiting.begin() + sel_idx);
                
                if (current->start_time == -1) {
                    current->start_time = t;
                }
                
                // Determine next arrival time
                int next_arrival_t = (i < total) ? jobs[i].arrival_time : -1;
                
                if (next_arrival_t == -1) {
                    // No more arrivals: run to completion
                    t += current->remaining_time;
                    current->completion_time = t;
                    current->remaining_time = 0;
                    completed.push_back(current);
                    current = nullptr;
                    continue;
                } else {
                    // CRITICAL FIX: Check if new arrival is at current time
                    if (next_arrival_t == t) {
                        // New arrival right now - don't execute, reconsider scheduling
                        continue;
                    }
                    
                    // Run until either next arrival or completion
                    // FIXED: Removed std::max(1, ...) that was forcing execution
                    int delta = std::min(current->remaining_time, next_arrival_t - t);
                    
                    // Safety check: delta should be positive
                    if (delta <= 0) {
                        // This should not happen with the fix above, but safety check
                        continue;
                    }
                    
                    t += delta;
                    current->remaining_time -= delta;
                    
                    if (current->remaining_time == 0) {
                        current->completion_time = t;
                        completed.push_back(current);
                        current = nullptr;
                    }
                    // Loop; new arrivals will be admitted at the updated t
                    continue;
                }
            }
        }
        
        // If nothing waiting, jump to next arrival
        if (i < total) {
            t = std::max(t, jobs[i].arrival_time);
        } else {
            break;
        }
    }
    
    // Calculate metrics
    std::vector<int> flows;
    for (Job* c : completed) {
        flows.push_back(c->completion_time - c->arrival_time);
    }
    
    int n = flows.size();
    if (n == 0) return {0.0, 0.0, 0.0};
    
    double avg_flow = 0.0;
    double l2 = 0.0;
    int max_flow = 0;
    
    for (int f : flows) {
        avg_flow += f;
        l2 += f * f;
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