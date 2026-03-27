// =============================================================================
// Distribution Shift Experiment (4.6)
//
// N=10000 jobs: first 5000 BP-H64, last 5000 BP-H262144
// rho=1.00  B=100  k=16
// Runs all 3 framework instances + all baselines
// Outputs per-batch L2-norm CSV for plotting
// =============================================================================

#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <cmath>
#include <algorithm>
#include <string>
#include <map>
#include <cassert>
#include <iomanip>
#include <climits>
#include <thread>
#include <mutex>
#include <random>
#include <set>
#include <functional>
#include <sys/stat.h>

// ---- Shared infrastructure ----
#include "Job.h"
#include "utils.h"
#include "Optimized_Selector.h"
#include "Optimized_SRPT_algorithm.h"
#include "Optimized_FCFS_algorithm.h"
#include "BAL_algorithm.h"

#include "SJF_algorithm.h"
#include "NC_RR_algorithm.h"

#include "RMLF_algorithm.h"
#include "MLFQ_algorithm.h"
#include "SETF_algorithm.h"

// Global mutex for thread-safe output
std::mutex g_cout_mutex;

void safe_print(const std::string& msg) {
    std::lock_guard<std::mutex> lock(g_cout_mutex);
    std::cout << msg << std::flush;
}

// =============================================================================
// SRPT by-reference variant (SRPT_Optimized takes by value — can't read back)
// =============================================================================
inline void SRPT_ref(std::vector<Job>& jobs) {
    const int total_jobs = jobs.size();
    if (total_jobs == 0) return;

    for (auto& job : jobs) {
        job.remaining_time = job.job_size;
        job.start_time = -1;
        job.completion_time = -1;
        job.starving_time = -1;
        job.waiting_time_ratio = 0.0;
    }

    std::stable_sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        if (a.arrival_time != b.arrival_time) return a.arrival_time < b.arrival_time;
        if (a.job_size != b.job_size) return a.job_size < b.job_size;
        return a.job_index < b.job_index;
    });

    long long current_time = 0;
    int next_arrival_idx = 0;
    std::vector<Job*> active_jobs;
    active_jobs.reserve(total_jobs);
    Job* current_job = nullptr;
    int completed_count = 0;

    while (completed_count < total_jobs) {
        bool new_arrivals = false;
        while (next_arrival_idx < total_jobs &&
               jobs[next_arrival_idx].arrival_time <= current_time) {
            active_jobs.push_back(&jobs[next_arrival_idx]);
            next_arrival_idx++;
            new_arrivals = true;
        }

        if (new_arrivals && current_job != nullptr) {
            active_jobs.push_back(current_job);
            current_job = nullptr;
        }

        if (current_job == nullptr && !active_jobs.empty()) {
            current_job = srpt_select_next_job_fast(active_jobs);
            active_jobs.erase(
                std::remove(active_jobs.begin(), active_jobs.end(), current_job),
                active_jobs.end());
            if (current_job->start_time == -1)
                current_job->start_time = current_time;
        }

        if (current_job != nullptr) {
            long long next_arrival_time = (next_arrival_idx < total_jobs) ?
                jobs[next_arrival_idx].arrival_time : LLONG_MAX;
            long long delta = std::min(
                (long long)current_job->remaining_time,
                next_arrival_time - current_time);
            if (delta <= 0) {
                delta = (next_arrival_time > current_time) ?
                    current_job->remaining_time : 1;
            }
            current_time += delta;
            current_job->remaining_time -= delta;
            if (current_job->remaining_time == 0) {
                current_job->completion_time = current_time;
                completed_count++;
                current_job = nullptr;
            }
        } else if (next_arrival_idx < total_jobs) {
            current_time = jobs[next_arrival_idx].arrival_time;
        } else {
            break;
        }
    }
}

// =============================================================================
// DYNAMIC (SRPT / FCFS) — copied from Dynamic.cpp, stripped of analysis I/O
// =============================================================================
struct DynamicResult {
    double avg_flow_time;
    double l2_norm_flow_time;
    double max_flow_time;
    std::vector<std::string> algorithm_history;
};

DynamicResult DYNAMIC(std::vector<Job>& jobs, int nJobsPerRound, int k) {
    int total_jobs = jobs.size();
    if (total_jobs == 0) return {0,0,0,{}};

    std::sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        if (a.arrival_time != b.arrival_time) return a.arrival_time < b.arrival_time;
        if (a.job_size != b.job_size) return a.job_size < b.job_size;
        return a.job_index < b.job_index;
    });

    long long current_time = 0;
    std::vector<Job*> active_jobs;
    std::vector<Job*> completed_jobs;
    int n_arrival_jobs = 0, n_completed_jobs = 0;
    bool is_srpt_better = true;
    int jobs_pointer = 0;
    std::vector<Job> jobs_in_current_round;
    std::vector<std::vector<Job>> round_jobs_history;
    int current_round = 1;
    std::vector<std::string> algorithm_history;
    Job* currently_executing_job = nullptr;

    for (size_t idx = 0; idx < jobs.size(); idx++) {
        jobs[idx].remaining_time = jobs[idx].job_size;
        jobs[idx].completion_time = -1;
        jobs[idx].start_time = -1;
    }

    while (n_completed_jobs < total_jobs) {
        long long prev_time = current_time;
        int prev_completed = n_completed_jobs;
        int prev_jobs_pointer = jobs_pointer;

        while (jobs_pointer < total_jobs && jobs[jobs_pointer].arrival_time <= current_time) {
            Job* job = &jobs[jobs_pointer];
            active_jobs.push_back(job);
            Job hj; hj.arrival_time = job->arrival_time; hj.job_size = job->job_size; hj.job_index = job->job_index;
            jobs_in_current_round.push_back(hj);
            n_arrival_jobs++; jobs_pointer++;
        }

        while (n_arrival_jobs >= nJobsPerRound) {
            std::vector<Job> jfr(jobs_in_current_round.begin(), jobs_in_current_round.begin() + nJobsPerRound);
            if (!jfr.empty()) {
                round_jobs_history.push_back(jfr);
                if (currently_executing_job) { active_jobs.push_back(currently_executing_job); currently_executing_job = nullptr; }
                if (current_round == 1) {
                    is_srpt_better = true;
                    algorithm_history.push_back("SRPT");
                } else {
                    std::vector<Job> sim_jobs;
                    size_t lb = (k <= 0) ? round_jobs_history.size() : std::min((size_t)k, round_jobs_history.size());
                    for (size_t i = round_jobs_history.size() - lb; i < round_jobs_history.size(); i++)
                        sim_jobs.insert(sim_jobs.end(), round_jobs_history[i].begin(), round_jobs_history[i].end());
                    std::vector<Job> sc = sim_jobs, fc = sim_jobs;
                    SRPTResult sr = SRPT(sc);
                    FCFSResult fr = Fcfs(fc);
                    is_srpt_better = !(std::isnan(sr.l2_norm_flow_time) || std::isnan(fr.l2_norm_flow_time))
                                     ? sr.l2_norm_flow_time <= fr.l2_norm_flow_time : true;
                    algorithm_history.push_back(is_srpt_better ? "SRPT" : "FCFS");
                }
                current_round++;
            }
            jobs_in_current_round.erase(jobs_in_current_round.begin(), jobs_in_current_round.begin() + nJobsPerRound);
            n_arrival_jobs -= nJobsPerRound;
        }

        if (!currently_executing_job && !active_jobs.empty()) {
            currently_executing_job = is_srpt_better ? srpt_select_next_job_fast(active_jobs) : fcfs_select_next_job_fast(active_jobs);
            active_jobs.erase(std::find(active_jobs.begin(), active_jobs.end(), currently_executing_job));
            if (currently_executing_job && currently_executing_job->remaining_time <= 0) { currently_executing_job = nullptr; continue; }
            if (currently_executing_job && currently_executing_job->start_time == -1) currently_executing_job->start_time = current_time;
        }

        if (currently_executing_job) {
            long long next_arr = (jobs_pointer < total_jobs) ? (long long)jobs[jobs_pointer].arrival_time : LLONG_MAX;
            int delta;
            if (is_srpt_better) {
                if (next_arr == LLONG_MAX) delta = currently_executing_job->remaining_time;
                else if (next_arr <= current_time) { active_jobs.push_back(currently_executing_job); currently_executing_job = nullptr; continue; }
                else delta = (currently_executing_job->remaining_time <= (int)(next_arr - current_time)) ? currently_executing_job->remaining_time : (int)(next_arr - current_time);
            } else {
                delta = currently_executing_job->remaining_time;
            }
            if (delta <= 0) { std::cerr << "FATAL delta<=0\n"; std::abort(); }
            current_time += delta;
            currently_executing_job->remaining_time -= delta;
            if (currently_executing_job->remaining_time == 0) {
                currently_executing_job->completion_time = current_time;
                completed_jobs.push_back(currently_executing_job);
                n_completed_jobs++;
                currently_executing_job = nullptr;
            }
        } else {
            if (jobs_pointer < total_jobs) current_time = jobs[jobs_pointer].arrival_time;
            else break;
        }
        assert(current_time > prev_time || n_completed_jobs > prev_completed || jobs_pointer > prev_jobs_pointer);
    }
    if (!jobs_in_current_round.empty() && n_arrival_jobs > 0) {
        round_jobs_history.push_back(jobs_in_current_round);
        algorithm_history.push_back(is_srpt_better ? "SRPT" : "FCFS");
    }

    long double sf = 0, ss = 0; long long mf = 0;
    for (Job* c : completed_jobs) {
        long long f = c->completion_time - c->arrival_time;
        sf += f; ss += (long double)f*f; mf = std::max(mf, f);
    }
    return {(double)(sf/total_jobs), std::sqrt((double)ss), (double)mf, algorithm_history};
}

// =============================================================================
// DYNAMIC_BAL (BAL / FCFS) — copied from Dynamic_BAL.cpp
// =============================================================================
DynamicResult DYNAMIC_BAL(std::vector<Job>& jobs, int nJobsPerRound, int k) {
    int total_jobs = jobs.size();
    if (total_jobs == 0) return {0,0,0,{}};
    double starvation_threshold = std::pow(total_jobs, 2.0/3.0);

    std::sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        if (a.arrival_time != b.arrival_time) return a.arrival_time < b.arrival_time;
        if (a.job_size != b.job_size) return a.job_size < b.job_size;
        return a.job_index < b.job_index;
    });

    long long current_time = 0;
    std::vector<Job*> active_jobs, completed_jobs;
    int n_arrival_jobs = 0, n_completed_jobs = 0;
    bool is_bal_better = true;
    int jobs_pointer = 0;
    std::vector<Job> jobs_in_current_round;
    std::vector<std::vector<Job>> round_jobs_history;
    int current_round = 1;
    std::vector<std::string> algorithm_history;
    Job* currently_executing_job = nullptr;

    for (size_t idx = 0; idx < jobs.size(); idx++) {
        jobs[idx].remaining_time = jobs[idx].job_size;
        jobs[idx].completion_time = -1;
        jobs[idx].start_time = -1;
        jobs[idx].starving_time = -1;
        jobs[idx].waiting_time_ratio = 0.0;
    }

    while (n_completed_jobs < total_jobs) {
        long long prev_time = current_time;
        int prev_completed = n_completed_jobs;
        int prev_jp = jobs_pointer;

        while (jobs_pointer < total_jobs && jobs[jobs_pointer].arrival_time <= current_time) {
            Job* job = &jobs[jobs_pointer];
            active_jobs.push_back(job);
            Job hj; hj.arrival_time = job->arrival_time; hj.job_size = job->job_size; hj.job_index = job->job_index;
            jobs_in_current_round.push_back(hj);
            n_arrival_jobs++; jobs_pointer++;
        }

        while (n_arrival_jobs >= nJobsPerRound) {
            std::vector<Job> jfr(jobs_in_current_round.begin(), jobs_in_current_round.begin() + nJobsPerRound);
            if (!jfr.empty()) {
                round_jobs_history.push_back(jfr);
                if (currently_executing_job) { active_jobs.push_back(currently_executing_job); currently_executing_job = nullptr; }
                if (current_round == 1) {
                    is_bal_better = true;
                    algorithm_history.push_back("BAL");
                } else {
                    std::vector<Job> sim_jobs;
                    size_t lb = (k <= 0) ? round_jobs_history.size() : std::min((size_t)k, round_jobs_history.size());
                    for (size_t i = round_jobs_history.size() - lb; i < round_jobs_history.size(); i++)
                        sim_jobs.insert(sim_jobs.end(), round_jobs_history[i].begin(), round_jobs_history[i].end());
                    std::vector<Job> bc = sim_jobs, fc = sim_jobs;
                    BALResult br = Bal(bc, starvation_threshold);
                    FCFSResult fr = Fcfs(fc);
                    is_bal_better = !(std::isnan(br.l2_norm_flow_time) || std::isnan(fr.l2_norm_flow_time))
                                     ? br.l2_norm_flow_time <= fr.l2_norm_flow_time : true;
                    algorithm_history.push_back(is_bal_better ? "BAL" : "FCFS");
                }
                current_round++;
            }
            jobs_in_current_round.erase(jobs_in_current_round.begin(), jobs_in_current_round.begin() + nJobsPerRound);
            n_arrival_jobs -= nJobsPerRound;
        }

        if (!currently_executing_job && !active_jobs.empty()) {
            currently_executing_job = is_bal_better
                ? bal_select_next_job_fast(active_jobs, current_time, starvation_threshold)
                : fcfs_select_next_job_fast(active_jobs);
            active_jobs.erase(std::find(active_jobs.begin(), active_jobs.end(), currently_executing_job));
            if (currently_executing_job && currently_executing_job->remaining_time <= 0) { currently_executing_job = nullptr; continue; }
            if (currently_executing_job && currently_executing_job->start_time == -1) currently_executing_job->start_time = current_time;
        }

        if (currently_executing_job) {
            long long next_arr = (jobs_pointer < total_jobs) ? (long long)jobs[jobs_pointer].arrival_time : LLONG_MAX;
            int delta;
            if (is_bal_better) {
                if (next_arr == LLONG_MAX) delta = currently_executing_job->remaining_time;
                else if (next_arr <= current_time) { active_jobs.push_back(currently_executing_job); currently_executing_job = nullptr; continue; }
                else delta = (currently_executing_job->remaining_time <= (int)(next_arr - current_time)) ? currently_executing_job->remaining_time : (int)(next_arr - current_time);
            } else {
                delta = currently_executing_job->remaining_time;
            }
            if (delta <= 0) { std::cerr << "FATAL delta<=0\n"; std::abort(); }
            current_time += delta;
            currently_executing_job->remaining_time -= delta;
            if (currently_executing_job->remaining_time == 0) {
                currently_executing_job->completion_time = current_time;
                completed_jobs.push_back(currently_executing_job);
                n_completed_jobs++;
                currently_executing_job = nullptr;
            }
        } else {
            if (jobs_pointer < total_jobs) current_time = jobs[jobs_pointer].arrival_time;
            else break;
        }
        assert(current_time > prev_time || n_completed_jobs > prev_completed || jobs_pointer > prev_jp);
    }
    if (!jobs_in_current_round.empty() && n_arrival_jobs > 0) {
        round_jobs_history.push_back(jobs_in_current_round);
        algorithm_history.push_back(is_bal_better ? "BAL" : "FCFS");
    }

    long double sf = 0, ssq = 0; long long mf = 0;
    for (Job* c : completed_jobs) {
        long long f = c->completion_time - c->arrival_time;
        sf += f; ssq += (long double)f*f; mf = std::max(mf, f);
    }
    return {(double)(sf/total_jobs), std::sqrt((double)ssq), (double)mf, algorithm_history};
}

// =============================================================================
// DYNAMIC_RF (RMLF / FCFS) — incremental event-driven scheduling
// Mirrors DYNAMIC/DYNAMIC_BAL structure, with RMLF multi-level feedback
// when the framework selects RMLF, and non-preemptive FCFS otherwise.
// =============================================================================

DynamicResult DYNAMIC_RF(std::vector<Job>& jobs, int nJobsPerRound, int k) {
    int total_jobs = jobs.size();
    if (total_jobs == 0) return {0,0,0,{}};

    std::sort(jobs.begin(), jobs.end(), [](const Job& a, const Job& b) {
        if (a.arrival_time != b.arrival_time) return a.arrival_time < b.arrival_time;
        if (a.job_size != b.job_size) return a.job_size < b.job_size;
        return a.job_index < b.job_index;
    });

    long long current_time = 0;
    std::vector<Job*> active_jobs;
    std::vector<Job*> completed_jobs;
    int n_arrival_jobs = 0, n_completed_jobs = 0;
    bool use_rmlf = false;
    int jobs_pointer = 0;
    std::vector<Job> jobs_in_current_round;
    std::vector<std::vector<Job>> round_jobs_history;
    int current_round = 1;
    std::vector<std::string> algorithm_history;
    Job* currently_executing_job = nullptr;

    // RMLF level tracking (indexed by job_index)
    std::vector<int> rmlf_level(total_jobs, 0);
    std::vector<int> rmlf_quantum_left(total_jobs, 1); // 2^0 = 1

    for (size_t idx = 0; idx < jobs.size(); idx++) {
        jobs[idx].remaining_time = jobs[idx].job_size;
        jobs[idx].completion_time = -1;
        jobs[idx].start_time = -1;
    }

    while (n_completed_jobs < total_jobs) {
        long long prev_time = current_time;
        int prev_completed = n_completed_jobs;
        int prev_jp = jobs_pointer;

        // Admit new arrivals
        bool new_arrivals = false;
        while (jobs_pointer < total_jobs && jobs[jobs_pointer].arrival_time <= current_time) {
            Job* job = &jobs[jobs_pointer];
            active_jobs.push_back(job);
            Job hj; hj.arrival_time = job->arrival_time; hj.job_size = job->job_size; hj.job_index = job->job_index;
            jobs_in_current_round.push_back(hj);
            n_arrival_jobs++; jobs_pointer++;
            new_arrivals = true;
        }

        // RMLF preempts on new arrivals (lower-level job may have arrived)
        if (new_arrivals && use_rmlf && currently_executing_job != nullptr) {
            active_jobs.push_back(currently_executing_job);
            currently_executing_job = nullptr;
        }

        // Batch boundary: evaluate FCFS vs RMLF
        while (n_arrival_jobs >= nJobsPerRound) {
            std::vector<Job> jfr(jobs_in_current_round.begin(), jobs_in_current_round.begin() + nJobsPerRound);
            if (!jfr.empty()) {
                round_jobs_history.push_back(jfr);
                if (currently_executing_job) { active_jobs.push_back(currently_executing_job); currently_executing_job = nullptr; }
                if (current_round == 1) {
                    use_rmlf = false;
                    algorithm_history.push_back("FCFS");
                } else {
                    std::vector<Job> sim_jobs;
                    size_t lb = (k <= 0) ? round_jobs_history.size() : std::min((size_t)k, round_jobs_history.size());
                    for (size_t i = round_jobs_history.size() - lb; i < round_jobs_history.size(); i++)
                        sim_jobs.insert(sim_jobs.end(), round_jobs_history[i].begin(), round_jobs_history[i].end());
                    std::vector<Job> fc = sim_jobs;
                    FCFSResult fr = Fcfs(fc);
                    std::vector<Job> rc = sim_jobs;
                    for (auto& j : rc) { j.remaining_time = j.job_size; j.completion_time = -1; j.start_time = -1; }
                    auto rr = RMLF_algorithm(rc);
                    use_rmlf = !(std::isnan(rr.l2_norm_flow_time) || std::isnan(fr.l2_norm_flow_time))
                               ? rr.l2_norm_flow_time < fr.l2_norm_flow_time : false;
                    algorithm_history.push_back(use_rmlf ? "RMLF" : "FCFS");
                }
                current_round++;
            }
            jobs_in_current_round.erase(jobs_in_current_round.begin(), jobs_in_current_round.begin() + nJobsPerRound);
            n_arrival_jobs -= nJobsPerRound;
        }

        // Select next job
        if (!currently_executing_job && !active_jobs.empty()) {
            if (use_rmlf) {
                // RMLF: select job with lowest level, FIFO within same level
                Job* best = active_jobs[0];
                int best_level = rmlf_level[best->job_index];
                for (size_t i = 1; i < active_jobs.size(); i++) {
                    int lvl = rmlf_level[active_jobs[i]->job_index];
                    if (lvl < best_level || (lvl == best_level && active_jobs[i]->arrival_time < best->arrival_time)) {
                        best = active_jobs[i];
                        best_level = lvl;
                    }
                }
                currently_executing_job = best;
            } else {
                currently_executing_job = fcfs_select_next_job_fast(active_jobs);
            }
            active_jobs.erase(std::find(active_jobs.begin(), active_jobs.end(), currently_executing_job));
            if (currently_executing_job && currently_executing_job->remaining_time <= 0) { currently_executing_job = nullptr; continue; }
            if (currently_executing_job && currently_executing_job->start_time == -1) currently_executing_job->start_time = current_time;
        }

        // Execute
        if (currently_executing_job) {
            long long next_arr = (jobs_pointer < total_jobs) ? (long long)jobs[jobs_pointer].arrival_time : LLONG_MAX;
            int delta;

            if (use_rmlf) {
                // RMLF: preemptive at quantum boundary and new arrivals
                int idx = currently_executing_job->job_index;
                int q_left = rmlf_quantum_left[idx];

                if (next_arr <= current_time) {
                    active_jobs.push_back(currently_executing_job);
                    currently_executing_job = nullptr;
                    continue;
                }
                delta = std::min((int)currently_executing_job->remaining_time, q_left);
                if (next_arr != LLONG_MAX)
                    delta = std::min(delta, (int)(next_arr - current_time));
                if (delta <= 0) delta = 1;
            } else {
                // FCFS: non-preemptive, run to completion
                delta = currently_executing_job->remaining_time;
            }

            if (delta <= 0) { std::cerr << "FATAL delta<=0 in DYNAMIC_RF\n"; std::abort(); }
            current_time += delta;
            currently_executing_job->remaining_time -= delta;

            if (use_rmlf) {
                int idx = currently_executing_job->job_index;
                rmlf_quantum_left[idx] -= delta;
            }

            if (currently_executing_job->remaining_time == 0) {
                currently_executing_job->completion_time = current_time;
                completed_jobs.push_back(currently_executing_job);
                n_completed_jobs++;
                currently_executing_job = nullptr;
            } else if (use_rmlf) {
                // Quantum exhausted: promote to next level
                int idx = currently_executing_job->job_index;
                if (rmlf_quantum_left[idx] <= 0) {
                    rmlf_level[idx]++;
                    rmlf_quantum_left[idx] = 1 << std::min(rmlf_level[idx], 30);
                    active_jobs.push_back(currently_executing_job);
                    currently_executing_job = nullptr;
                }
            }
        } else {
            if (jobs_pointer < total_jobs) current_time = jobs[jobs_pointer].arrival_time;
            else break;
        }
        assert(current_time > prev_time || n_completed_jobs > prev_completed || jobs_pointer > prev_jp);
    }

    if (!jobs_in_current_round.empty() && n_arrival_jobs > 0) {
        round_jobs_history.push_back(jobs_in_current_round);
        algorithm_history.push_back(use_rmlf ? "RMLF" : "FCFS");
    }

    long double sf = 0, ssq = 0; long long mf = 0;
    for (Job* c : completed_jobs) {
        long long f = c->completion_time - c->arrival_time;
        sf += f; ssq += (long double)f*f; mf = std::max(mf, f);
    }
    return {(double)(sf/total_jobs), std::sqrt((double)ssq), (double)mf, algorithm_history};
}

// =============================================================================
// Per-batch L2-norm computation
// =============================================================================

// jobs must have completion_time set and be identifiable by job_index (0..N-1)
std::vector<double> compute_per_batch_l2(const std::vector<Job>& jobs, int batch_size) {
    int N = jobs.size();
    int n_batches = N / batch_size;

    // Build index: completion_time by job_index
    std::vector<long long> ct(N, -1);
    std::vector<int> at(N, 0);
    for (const auto& j : jobs) {
        if (j.job_index >= 0 && j.job_index < N) {
            ct[j.job_index] = j.completion_time;
            at[j.job_index] = j.arrival_time;
        }
    }

    std::vector<double> batch_l2;
    for (int b = 0; b < n_batches; b++) {
        long double ssq = 0;
        for (int i = b*batch_size; i < (b+1)*batch_size; i++) {
            long long flow = ct[i] - at[i];
            ssq += (long double)flow * flow;
        }
        batch_l2.push_back(std::sqrt((double)ssq));
    }
    return batch_l2;
}

// =============================================================================
// Main
// =============================================================================
int main(int argc, char* argv[]) {
    // --- Parameters ---
    const int EVAL_WINDOW = 100;   // fixed 100-job evaluation window
    const int K_LOOKBACK = 16;
    const int N_JOBS = 10000;
    const int N_BATCHES = N_JOBS / EVAL_WINDOW;

    // CLI: <data_file> <B> <mode> <output_dir>
    //   B     = batch size for framework decision (10, 100, 1000)
    //   mode  = "all" | "baselines" | "framework"
    //   output_dir = where to write CSVs
    std::string data_file = "./data/distribution_shift_1/shift_H64_H262144.csv";
    int B = 100;
    std::string mode = "all";
    std::string out_dir = "./algorithm_result/distribution_shift_result";

    if (argc > 1) data_file = argv[1];
    if (argc > 2) B = std::atoi(argv[2]);
    if (argc > 3) mode = argv[3];
    if (argc > 4) out_dir = argv[4];

    if (B <= 0) { std::cerr << "ERROR: B must be positive\n"; return 1; }

    std::cout << "============================================================\n"
              << "Distribution Shift Experiment\n"
              << "  Data: " << data_file << "\n"
              << "  B=" << B << "  k=" << K_LOOKBACK
              << "  eval_window=" << EVAL_WINDOW << "  mode=" << mode << "\n"
              << "============================================================\n";

    // --- Read jobs ---
    std::vector<Job> jobs_orig = read_jobs_from_csv(data_file);
    if (jobs_orig.empty()) {
        std::cerr << "ERROR: Could not read jobs from " << data_file << "\n";
        return 1;
    }
    std::cout << "Loaded " << jobs_orig.size() << " jobs\n";

    // Assign job_index based on original order (arrival order)
    std::stable_sort(jobs_orig.begin(), jobs_orig.end(), [](const Job& a, const Job& b) {
        return a.arrival_time < b.arrival_time;
    });
    for (int i = 0; i < (int)jobs_orig.size(); i++) {
        jobs_orig[i].job_index = i;
    }

    // --- Output directory ---
    create_directories_recursive(out_dir);

    // --- Storage for per-batch L2 results ---
    struct AlgoResult {
        std::string name;
        std::vector<double> batch_l2;
    };
    std::vector<AlgoResult> all_results;

    // Mutex for thread-safe result collection
    std::mutex results_mutex;

    // =====================================================================
    // Run baseline algorithms (by-reference: completion_time is set on jobs)
    // =====================================================================
    std::vector<std::thread> threads;

    if (mode == "all" || mode == "baselines") {
        auto run_baseline = [&](const std::string& name, std::function<void(std::vector<Job>&)> algo_fn) {
            safe_print("Running " + name + "...\n");
            std::vector<Job> jc = jobs_orig;
            algo_fn(jc);
            auto bl = compute_per_batch_l2(jc, EVAL_WINDOW);
            {
                std::lock_guard<std::mutex> lock(results_mutex);
                all_results.push_back({name, bl});
            }
            double agg = 0;
            for (double v : bl) agg += v*v;
            safe_print("  " + name + " done. Aggregate L2 = " + std::to_string(std::sqrt(agg)) + "\n");
        };

        threads.emplace_back([&]() { run_baseline("SRPT", [](std::vector<Job>& j) { SRPT_ref(j); }); });
        threads.emplace_back([&]() { run_baseline("FCFS", [](std::vector<Job>& j) { Fcfs_Optimized(j); }); });
        threads.emplace_back([&]() {
            run_baseline("BAL", [&](std::vector<Job>& j) {
                double thr = std::pow(j.size(), 2.0/3.0);
                Bal(j, thr);
            });
        });
        threads.emplace_back([&]() { run_baseline("SJF", [](std::vector<Job>& j) { SJF(j); }); });
        threads.emplace_back([&]() { run_baseline("RR", [](std::vector<Job>& j) { NC_RR(j, 1); }); });
        threads.emplace_back([&]() { run_baseline("RMLF", [](std::vector<Job>& j) { RMLF_algorithm(j); }); });
        threads.emplace_back([&]() { run_baseline("MLFQ", [](std::vector<Job>& j) { MLFQ(j, 100); }); });
        threads.emplace_back([&]() { run_baseline("SETF", [](std::vector<Job>& j) { Setf(j); }); });

        for (auto& t : threads) t.join();
        threads.clear();
    }

    // =====================================================================
    // Run framework algorithms (Dynamic, Dynamic_BAL, RFDynamic)
    // =====================================================================
    std::vector<std::string> dyn_hist, dbal_hist, rf_hist;

    if (mode == "all" || mode == "framework") {
        threads.emplace_back([&]() {
            safe_print("Running Dynamic (B=" + std::to_string(B) + ", k=" + std::to_string(K_LOOKBACK) + ")...\n");
            std::vector<Job> jc = jobs_orig;
            auto res = DYNAMIC(jc, B, K_LOOKBACK);
            dyn_hist = res.algorithm_history;
            auto bl = compute_per_batch_l2(jc, EVAL_WINDOW);
            { std::lock_guard<std::mutex> lock(results_mutex); all_results.push_back({"Dynamic", bl}); }
            safe_print("  Dynamic done. Aggregate L2 = " + std::to_string(res.l2_norm_flow_time) + "\n");
        });

        threads.emplace_back([&]() {
            safe_print("Running Dynamic_BAL (B=" + std::to_string(B) + ", k=" + std::to_string(K_LOOKBACK) + ")...\n");
            std::vector<Job> jc = jobs_orig;
            auto res = DYNAMIC_BAL(jc, B, K_LOOKBACK);
            dbal_hist = res.algorithm_history;
            auto bl = compute_per_batch_l2(jc, EVAL_WINDOW);
            { std::lock_guard<std::mutex> lock(results_mutex); all_results.push_back({"Dynamic_BAL", bl}); }
            safe_print("  Dynamic_BAL done. Aggregate L2 = " + std::to_string(res.l2_norm_flow_time) + "\n");
        });

        threads.emplace_back([&]() {
            safe_print("Running RFDynamic (B=" + std::to_string(B) + ", k=" + std::to_string(K_LOOKBACK) + ")...\n");
            std::vector<Job> jc = jobs_orig;
            auto res = DYNAMIC_RF(jc, B, K_LOOKBACK);
            rf_hist = res.algorithm_history;
            auto bl = compute_per_batch_l2(jc, EVAL_WINDOW);
            { std::lock_guard<std::mutex> lock(results_mutex); all_results.push_back({"RFDynamic", bl}); }
            safe_print("  RFDynamic done. Aggregate L2 = " + std::to_string(res.l2_norm_flow_time) + "\n");
        });

        for (auto& t : threads) t.join();
    }

    // =====================================================================
    // Write per-batch L2 CSV
    // =====================================================================
    {
        std::string csv_path = out_dir + "/per_batch_l2.csv";
        std::ofstream out(csv_path);

        // Column order depends on mode
        std::vector<std::string> col_order;
        if (mode == "baselines") {
            col_order = {"SRPT", "FCFS", "BAL", "SJF", "RR", "RMLF", "MLFQ", "SETF"};
        } else if (mode == "framework") {
            col_order = {"Dynamic", "Dynamic_BAL", "RFDynamic"};
        } else {
            col_order = {"SRPT", "FCFS", "BAL", "SJF", "RR", "RMLF", "MLFQ", "SETF",
                         "Dynamic", "Dynamic_BAL", "RFDynamic"};
        }

        // Header
        out << "batch";
        for (auto& c : col_order) out << "," << c;
        out << "\n";

        // Build lookup
        std::map<std::string, std::vector<double>> lookup;
        for (auto& r : all_results) lookup[r.name] = r.batch_l2;

        // Write rows
        for (int b = 0; b < N_BATCHES; b++) {
            out << (b+1);
            for (auto& c : col_order) {
                out << ",";
                if (lookup.count(c) && b < (int)lookup[c].size())
                    out << std::fixed << std::setprecision(4) << lookup[c][b];
                else
                    out << "NA";
            }
            out << "\n";
        }
        out.close();
        std::cout << "Wrote " << csv_path << "\n";
    }

    // =====================================================================
    // Write algorithm selection history CSV (framework mode only)
    // =====================================================================
    if (mode == "all" || mode == "framework") {
        std::string csv_path = out_dir + "/algorithm_selection.csv";
        std::ofstream out(csv_path);
        out << "round,Dynamic_choice,Dynamic_BAL_choice,RFDynamic_choice\n";

        size_t max_rounds = std::max({dyn_hist.size(), dbal_hist.size(), rf_hist.size()});
        for (size_t r = 0; r < max_rounds; r++) {
            out << (r+1) << ",";
            out << (r < dyn_hist.size() ? dyn_hist[r] : "") << ",";
            out << (r < dbal_hist.size() ? dbal_hist[r] : "") << ",";
            out << (r < rf_hist.size() ? rf_hist[r] : "") << "\n";
        }
        out.close();
        std::cout << "Wrote " << csv_path << "\n";
    }

    std::cout << "\n============================================================\n"
              << "Distribution Shift Experiment COMPLETE\n"
              << "============================================================\n";
    return 0;
}
