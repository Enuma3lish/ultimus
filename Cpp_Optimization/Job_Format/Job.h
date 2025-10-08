#ifndef JOB_H
#define JOB_H

// Updated Job struct with consistent type handling
struct Job {
    int arrival_time;         // Original arrival time from data
    int job_size;            // Original job size from data
    int job_index;           // Unique identifier
    int remaining_time;      // Remaining execution time
    long long start_time;    // When job first started (can be large due to gaps)
    long long completion_time; // When job completed (can be large)
    long long starving_time;   // When job became starving (-1 if not starving)
    double waiting_time_ratio; // Ratio for starvation detection
    
    Job() : arrival_time(0), job_size(0), job_index(0), remaining_time(0),
            start_time(-1), completion_time(-1), starving_time(-1), 
            waiting_time_ratio(0.0) {}
    
    // Constructor with parameters
    Job(int arr, int size, int idx, int rem, long long start, 
        long long comp, long long starve, double ratio)
        : arrival_time(arr), job_size(size), job_index(idx), 
          remaining_time(rem), start_time(start), completion_time(comp),
          starving_time(starve), waiting_time_ratio(ratio) {}
};

// Helper function for safe type conversion in scheduling algorithms
inline long long safe_min_ll(int a, long long b) {
    return std::min(static_cast<long long>(a), b);
}

inline long long safe_max_ll(long long a, int b) {
    return std::max(a, static_cast<long long>(b));
}

#endif // JOB_H