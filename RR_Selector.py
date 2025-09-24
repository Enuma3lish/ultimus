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

from collections import deque
from typing import Deque, List, Tuple, Optional

def RR_Selector_optimized(jobs_info, 
                          current_time: int, 
                          ready_queue: Deque[Tuple[int, int]], 
                          time_quantum: int = 1) -> Tuple[Optional[int], int, bool]:
    """
    Optimized Round Robin selector (event-driven & O(1) amortized admission):
      - Expects jobs_info as a deque of (orig_idx, arrival_time, remaining_time) sorted by arrival_time.
      - Moves all arrived jobs into ready_queue (orig_idx, remaining_time) via popleft.
      - If ready_queue has a job, returns (orig_idx, execution_time, True), where execution_time is
        min(time_quantum, remaining_time, time_until_next_arrival). This allows event-driven jumps.
      - If no job is ready:
          * returns (None, next_arrival_time, False) if future jobs exist
          * otherwise (None, current_time, False)
    """
    # Ensure deque for O(1) popleft
    if not isinstance(jobs_info, deque):
        try:
            jobs_info = deque(jobs_info)
        except Exception:
            # Fallback but will be O(n) on pops; caller should pass deque
            jobs_info = deque(list(jobs_info))

    # Admit all jobs that have arrived by current_time
    while jobs_info and jobs_info[0][1] <= current_time:
        orig_idx, at, rem = jobs_info.popleft()
        ready_queue.append((orig_idx, rem))

    if ready_queue:
        # Choose next RR candidate (peek at leftmost)
        orig_idx, remaining = ready_queue[0]
        exec_time = min(time_quantum, remaining)
        # Consider next arrival to keep event-driven steps
        if jobs_info:
            next_arrival = jobs_info[0][1]
            # If a new job arrives before we finish the quantum, slice the run
            if current_time + exec_time > next_arrival:
                exec_time = max(1, next_arrival - current_time)
        return orig_idx, exec_time, True

    # No job ready; suggest jump time
    if jobs_info:
        return None, jobs_info[0][1], False
    return None, current_time, False
