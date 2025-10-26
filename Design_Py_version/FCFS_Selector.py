#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import heapq

def select_next_job(waiting_queue):
    """Backward-compatible O(n) FCFS selector.
    Priority: earliest arrival, then smaller job_size, then smaller job_index.
    """
    if not waiting_queue:
        return None
    best = waiting_queue[0]
    for j in waiting_queue:
        if (j["arrival_time"], j.get("job_size", 0), j.get("job_index", 0)) < \
           (best["arrival_time"], best.get("job_size", 0), best.get("job_index", 0)):
            best = j
    return best


def select_next_job_optimized(waiting_queue):
    """O(log n) heap-based selector. Same priority order as select_next_job.
    Automatically falls back to linear scan when small (<=10).
    Returns a *dict* representing the selected job (not removed from input).
    """
    n = len(waiting_queue)
    if n == 0:
        return None
    if n <= 10:
        return select_next_job(waiting_queue)

    # Build heap of tuples
    heap = []
    for j in waiting_queue:
        heap.append((j["arrival_time"], j.get("job_size", 0), j.get("job_index", 0), j))
    heapq.heapify(heap)
    return heapq.heappop(heap)[-1]
