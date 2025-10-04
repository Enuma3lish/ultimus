// ==================== Job.h ====================
#ifndef JOB_H
#define JOB_H

struct Job {
    int arrival_time;
    int job_size;
    int job_index;
    int remaining_time;
    long long start_time;        // Fixed: Use long long to prevent overflow
    long long completion_time;   // Fixed: Use long long to prevent overflow
    int starving_time;
    double waiting_time_ratio;
    
    Job() : arrival_time(0), job_size(0), job_index(0), remaining_time(0),
            start_time(-1), completion_time(-1), starving_time(-1), 
            waiting_time_ratio(0.0) {}
};

#endif // JOB_H