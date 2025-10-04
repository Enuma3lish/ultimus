#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import heapq

def select_next_job(job_queue):
    """Backward-compatible O(n) SRPT selector.
    Priority: remaining_time, then arrival_time, then job_index.
    Expects dicts with keys: remaining_time, arrival_time, job_index.
    """
    if not job_queue:
        return None
    best = job_queue[0]
    for j in job_queue:
        if (j["remaining_time"], j["arrival_time"], j["job_index"]) < \
           (best["remaining_time"], best["arrival_time"], best["job_index"]):
            best = j
    return best


def select_next_job_optimized(job_queue):
    """O(log n) heap-based SRPT selector.
    Automatically falls back to linear scan when small (<=10).
    Returns a *dict* representing the selected job (not removed from input).
    """
    n = len(job_queue)
    if n == 0:
        return None
    if n <= 10:
        return select_next_job(job_queue)

    heap = []
    for j in job_queue:
        heap.append((j["remaining_time"], j["arrival_time"], j["job_index"], j))
    heapq.heapify(heap)
    return heapq.heappop(heap)[-1]
