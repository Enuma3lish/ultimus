from typing import List, Tuple, Optional, Deque
from collections import deque

def RR_Selector(jobs_info: List[Tuple[int, int, int]], 
                current_time: int, 
                ready_queue: Deque[Tuple[int, int]], 
                time_quantum: int = 1) -> Tuple[Optional[int], int, bool]:
    """
    Selects the next job to execute according to Round Robin scheduling.
    
    Args:
        jobs_info: List of (original_index, arrival_time, remaining_time) tuples for jobs not yet in ready_queue
        current_time: Current system time
        ready_queue: Queue of jobs ready to be executed (orig_index, remaining_time)
        time_quantum: Time quantum for Round Robin
    
    Returns:
        Tuple of (selected_job_original_index, execution_time, is_job_selected)
        If no job is available, returns (None, next_arrival_time, False)
    """
    # Check for newly arrived jobs and add them to ready queue
    i = 0
    while i < len(jobs_info):
        orig_idx, arrival, remaining = jobs_info[i]
        if arrival <= current_time:
            ready_queue.append((orig_idx, remaining))
            jobs_info.pop(i)
        else:
            i += 1
    
    if ready_queue:
        # Get next job from the ready queue (Round Robin order)
        orig_idx, remaining = ready_queue[0]  # Peek at first job but don't remove it yet
        execution_time = min(time_quantum, remaining)
        return orig_idx, execution_time, True
    else:
        # No jobs ready, return the next arrival time if there are still jobs to arrive
        if jobs_info:
            return None, jobs_info[0][1], False
        return None, current_time, False